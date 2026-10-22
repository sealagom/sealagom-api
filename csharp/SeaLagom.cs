// SeaLagom API client for .NET 8+. No dependencies: HttpClient and System.Text.Json.
// MIT License, Copyright (c) 2026 SeaLagom. See LICENSE in the repository root.
//
//   using var api = new SeaLagom.Client("YOUR_KEY");            // or the SEALAGOM_API_KEY environment variable
//   var page = await api.SearchWarnings(new() { ["navarea_id"] = 1, ["ai_in_force"] = true });
//   var near = await api.WarningsNear(55.0, 3.0, 60);            // warnings in force within 60 NM
//   var check = await api.RouteCheckFile("passage.rtz", corridorNm: 15);
//   var check2 = await api.RouteCheck(new[] { (51.0, 1.5), (36.1, -5.4) }, speedKn: 14);
//
// Lists are passed as arrays: ["ai_severity"] = new[] { "critical", "high" }. Every answer is the JSON as
// served, as a JsonElement. Errors throw SeaLagomException with the HTTP status and the server's detail
// (401 no or wrong key, 403 the plan does not include the call, 429 allowance or rate limit reached).
// Without a key only the public endpoints answer (Feeds, the NAVAREA zones, stations near a position).

using System.Globalization;
using System.Text;
using System.Text.Json;

namespace SeaLagom;

public class SeaLagomException : Exception
{
    public int Status { get; }
    public string Detail { get; }
    public SeaLagomException(int status, string detail) : base($"{status}: {detail}") { Status = status; Detail = detail; }
}

public sealed class Client : IDisposable
{
    public const string DefaultBase = "https://www.sealagom.com";
    public const string UserAgent = "sealagom-csharp/1.0";

    private readonly HttpClient _http;
    public string Base { get; }
    public Dictionary<string, string> LastHeaders { get; private set; } = new();

    public Client(string? key = null, string baseUrl = DefaultBase, double timeoutSeconds = 60)
    {
        key = (key ?? Environment.GetEnvironmentVariable("SEALAGOM_API_KEY") ?? "").Trim();
        Base = baseUrl.TrimEnd('/');
        _http = new HttpClient { Timeout = TimeSpan.FromSeconds(timeoutSeconds) };
        if (key.Length > 0) _http.DefaultRequestHeaders.Add("X-API-Token", key);
        _http.DefaultRequestHeaders.Add("User-Agent", UserAgent);
        _http.DefaultRequestHeaders.Add("Accept", "application/json");
        _http.DefaultRequestHeaders.Add("X-Requested-With", "sealagom-kit");
    }

    public void Dispose() => _http.Dispose();

    // -- plumbing ---------------------------------------------------------------------------------
    private static string Str(object v) => v switch
    {
        bool b => b ? "true" : "false",
        IFormattable f => f.ToString(null, CultureInfo.InvariantCulture),
        _ => v.ToString() ?? ""
    };

    public static string Query(IDictionary<string, object?>? p)
    {
        if (p == null || p.Count == 0) return "";
        var sb = new StringBuilder();
        foreach (var (k, v) in p)
        {
            if (v == null) continue;
            IEnumerable<object> values = v is string || v is not System.Collections.IEnumerable ? new[] { v } : ((System.Collections.IEnumerable)v).Cast<object>();
            foreach (var x in values)
                sb.Append(sb.Length == 0 ? '?' : '&').Append(Uri.EscapeDataString(k)).Append('=').Append(Uri.EscapeDataString(Str(x)));
        }
        return sb.ToString();
    }

    private async Task<JsonElement> Send(HttpRequestMessage req)
    {
        using var r = await _http.SendAsync(req);
        LastHeaders = r.Headers.ToDictionary(h => h.Key, h => string.Join(", ", h.Value));
        var text = await r.Content.ReadAsStringAsync();
        if ((int)r.StatusCode >= 400)
        {
            string detail = text.Length > 200 ? text[..200] : text;
            try
            {
                using var doc = JsonDocument.Parse(text);
                if (doc.RootElement.TryGetProperty("detail", out var d) && d.ValueKind == JsonValueKind.String) detail = d.GetString() ?? detail;
            }
            catch (JsonException) { }
            throw new SeaLagomException((int)r.StatusCode, detail.Length > 0 ? detail : r.ReasonPhrase ?? "error");
        }
        using var ok = JsonDocument.Parse(text);
        return ok.RootElement.Clone();
    }

    public Task<JsonElement> Get(string path, IDictionary<string, object?>? p = null) =>
        Send(new HttpRequestMessage(HttpMethod.Get, Base + path + Query(p)));

    private Task<JsonElement> PostJson(string path, object body)
    {
        var req = new HttpRequestMessage(HttpMethod.Post, Base + path)
        {
            Content = new StringContent(JsonSerializer.Serialize(body), Encoding.UTF8, "application/json")
        };
        return Send(req);
    }

    // -- warnings ---------------------------------------------------------------------------------
    /// <summary>GET /api/v2/messages/: navarea_id, coastal_id, country, q, date_from, date_to, keyword, has_coordinates,
    /// include_archived, include_ai_analysis, include_geo_features, ai_severity, ai_category, ai_in_force,
    /// expires_within_hours, exclude_routine, topic, page, page_size. Answer: count, next, results[].</summary>
    public Task<JsonElement> SearchWarnings(IDictionary<string, object?>? p = null) => Get("/api/v2/messages/", p);

    /// <summary>GET /api/v2/near/: warnings in force within radius_nm (up to 200) of a position. Answer: count, warnings[]
    /// with region_title, number, distance_nm, nearest [lat, lon], ai (headline, severity, valid_until).</summary>
    public Task<JsonElement> WarningsNear(double lat, double lon, double radiusNm = 30) =>
        Get("/api/v2/near/", new Dictionary<string, object?> { ["lat"] = lat, ["lon"] = lon, ["radius_nm"] = radiusNm });

    /// <summary>GET /api/v2/navarea/: the 21 NAVAREAs with their region ids.</summary>
    public Task<JsonElement> Navareas(IDictionary<string, object?>? p = null) => Get("/api/v2/navarea/", p);

    /// <summary>GET /api/v2/feeds/: every feed with its endpoint and warnings in force (no key needed). Answer: feeds[].</summary>
    public Task<JsonElement> Feeds() => Get("/api/v2/feeds/");

    /// <summary>GET /api/v2/feeds/{slug}/: one themed feed (military, cables, offshore, survey, hazards, ice...).</summary>
    public Task<JsonElement> Feed(string slug, IDictionary<string, object?>? p = null) => Get($"/api/v2/feeds/{Uri.EscapeDataString(slug)}/", p);

    // -- route ------------------------------------------------------------------------------------
    /// <summary>POST /api/v2/route/ with JSON waypoints (lat, lon). Answer: route_nm, navareas[], count, results[]
    /// with distance_nm, along_nm, verdict, ai.</summary>
    public Task<JsonElement> RouteCheck(IEnumerable<(double lat, double lon)> waypoints, double speedKn = 12, double corridorNm = 10, string? departure = null)
    {
        var body = new Dictionary<string, object?>
        {
            ["waypoints"] = waypoints.Select(w => new { lat = w.lat, lon = w.lon }).ToArray(),
            ["speed_kn"] = speedKn,
            ["corridor_nm"] = corridorNm
        };
        if (departure != null) body["departure"] = departure;
        return PostJson("/api/v2/route/", body);
    }

    /// <summary>POST /api/v2/route/ with a route file (RTZ, RT3, GPX, KML, CSV, NMEA; up to 5 MB).</summary>
    public async Task<JsonElement> RouteCheckFile(string path, double speedKn = 12, double corridorNm = 10, string? departure = null)
    {
        using var form = new MultipartFormDataContent();
        form.Add(new ByteArrayContent(await File.ReadAllBytesAsync(path)), "file", Path.GetFileName(path));
        form.Add(new StringContent(Str(speedKn)), "speed_kn");
        form.Add(new StringContent(Str(corridorNm)), "corridor_nm");
        if (departure != null) form.Add(new StringContent(departure), "departure");
        return await Send(new HttpRequestMessage(HttpMethod.Post, Base + "/api/v2/route/") { Content = form });
    }
}
