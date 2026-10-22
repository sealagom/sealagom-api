// SeaLagom API client for Java 11+. No dependencies: java.net.http.HttpClient. MIT License, Copyright (c) 2026 SeaLagom.
//
//   SeaLagom api = new SeaLagom("YOUR_KEY");                       // or the SEALAGOM_API_KEY environment variable
//   String page = api.searchWarnings(Map.of("navarea_id", 1, "ai_in_force", true));
//   String near = api.warningsNear(55.0, 3.0, 60);                 // warnings in force within 60 NM
//   String check = api.routeCheckFile(Path.of("passage.rtz"), 12, 15, null);
//   String check2 = api.routeCheck(new double[][] {{51.0, 1.5}, {36.1, -5.4}}, 14, 10, null);
//
// Every answer is the JSON as served, as a String: hand it to Jackson, Gson or any parser you already have, or
// use the two small helpers SeaLagom.field(json, "count") and SeaLagom.objects(json, "warnings") for a quick
// look. Lists are List or arrays: Map.of("ai_severity", List.of("critical", "high")). Errors throw SeaLagom.Error
// with the HTTP status and the server's detail (401 no or wrong key, 403 not in the plan, 429 allowance reached).
// Without a key only the public endpoints answer (feeds).

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;

public final class SeaLagom {
    public static final String BASE = "https://www.sealagom.com";
    public static final String USER_AGENT = "sealagom-java/1.0";

    public static final class Error extends RuntimeException {
        private static final long serialVersionUID = 1L;
        public final int status;
        public final String detail;
        public Error(int status, String detail) { super(status + ": " + detail); this.status = status; this.detail = detail; }
    }

    private final String key;
    private final String base;
    private final Duration timeout;
    private final HttpClient http;
    public Map<String, List<String>> lastHeaders = Collections.emptyMap();

    public SeaLagom(String key) { this(key, BASE, Duration.ofSeconds(60)); }
    public SeaLagom(String key, String base, Duration timeout) {
        String k = key != null ? key : System.getenv("SEALAGOM_API_KEY");
        this.key = k == null ? "" : k.trim();
        this.base = base.endsWith("/") ? base.substring(0, base.length() - 1) : base;
        this.timeout = timeout;
        this.http = HttpClient.newBuilder().connectTimeout(timeout).followRedirects(HttpClient.Redirect.NORMAL).build();
    }

    // -- plumbing ---------------------------------------------------------------------------------
    private static String enc(String s) { return URLEncoder.encode(s, StandardCharsets.UTF_8); }
    public static String query(Map<String, ?> params) {
        if (params == null || params.isEmpty()) return "";
        StringBuilder sb = new StringBuilder();
        for (Map.Entry<String, ?> e : params.entrySet()) {
            Object v = e.getValue();
            if (v == null) continue;
            List<?> values = v instanceof List ? (List<?>) v : v instanceof Object[] ? List.of((Object[]) v) : List.of(v);
            for (Object x : values) sb.append(sb.length() == 0 ? '?' : '&').append(enc(e.getKey())).append('=').append(enc(String.valueOf(x)));
        }
        return sb.toString();
    }

    private HttpRequest.Builder request(String path) {
        HttpRequest.Builder b = HttpRequest.newBuilder(URI.create(base + path)).timeout(timeout)
            .header("User-Agent", USER_AGENT).header("Accept", "application/json").header("X-Requested-With", "sealagom-kit");
        if (!key.isEmpty()) b.header("X-API-Token", key);
        return b;
    }

    private String send(HttpRequest req) {
        HttpResponse<String> r;
        try {
            r = http.send(req, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
        } catch (IOException | InterruptedException e) {
            throw new Error(0, e.getMessage() == null ? e.toString() : e.getMessage());
        }
        lastHeaders = r.headers().map();
        if (r.statusCode() >= 400) {
            String detail = field(r.body(), "detail");
            if (detail == null) detail = r.body().length() > 200 ? r.body().substring(0, 200) : r.body();
            throw new Error(r.statusCode(), detail);
        }
        return r.body();
    }

    public String get(String path, Map<String, ?> params) { return send(request(path + query(params)).GET().build()); }

    private String postJson(String path, String json) {
        return send(request(path).header("Content-Type", "application/json").POST(HttpRequest.BodyPublishers.ofString(json)).build());
    }

    // -- warnings ---------------------------------------------------------------------------------
    /** GET /api/v2/messages/: navarea_id, country, q, date_from, date_to, ai_severity, ai_in_force, include_ai_analysis,
     *  topic, page, page_size... Answer: count, next, results[]. */
    public String searchWarnings(Map<String, ?> params) { return get("/api/v2/messages/", params); }

    /** GET /api/v2/near/: warnings in force within radiusNm (up to 200) of a position. Answer: count, warnings[]
     *  with region_title, number, distance_nm, nearest [lat, lon], ai (headline, severity, valid_until). */
    public String warningsNear(double lat, double lon, double radiusNm) {
        return get("/api/v2/near/", Map.of("lat", lat, "lon", lon, "radius_nm", radiusNm));
    }

    /** GET /api/v2/navarea/: the 21 NAVAREAs with their region ids. */
    public String navareas() { return get("/api/v2/navarea/", null); }

    /** GET /api/v2/feeds/: every feed with its endpoint and warnings in force (no key needed). Answer: feeds[]. */
    public String feeds() { return get("/api/v2/feeds/", null); }

    /** GET /api/v2/feeds/{slug}/: one themed feed (military, cables, offshore, survey, hazards, ice...). */
    public String feed(String slug, Map<String, ?> params) { return get("/api/v2/feeds/" + enc(slug) + "/", params); }

    // -- route ------------------------------------------------------------------------------------
    /** POST /api/v2/route/ with waypoints {{lat, lon}, ...}; departure ISO UTC or null. Answer: route_nm, navareas[],
     *  count, results[] (distance_nm, along_nm, verdict, ai). */
    public String routeCheck(double[][] waypoints, double speedKn, double corridorNm, String departure) {
        StringBuilder sb = new StringBuilder("{\"waypoints\":[");
        for (int i = 0; i < waypoints.length; i++)
            sb.append(i > 0 ? "," : "").append("{\"lat\":").append(waypoints[i][0]).append(",\"lon\":").append(waypoints[i][1]).append('}');
        sb.append("],\"speed_kn\":").append(speedKn).append(",\"corridor_nm\":").append(corridorNm);
        if (departure != null) sb.append(",\"departure\":\"").append(departure.replace("\"", "")).append('"');
        return postJson("/api/v2/route/", sb.append('}').toString());
    }

    /** POST /api/v2/route/ with a route file (RTZ, RT3, GPX, KML, CSV, NMEA; up to 5 MB). */
    public String routeCheckFile(Path file, double speedKn, double corridorNm, String departure) {
        String boundary = "----sealagom" + System.nanoTime();
        try {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            part(out, boundary, "speed_kn", String.valueOf(speedKn));
            part(out, boundary, "corridor_nm", String.valueOf(corridorNm));
            if (departure != null) part(out, boundary, "departure", departure);
            out.write(("--" + boundary + "\r\nContent-Disposition: form-data; name=\"file\"; filename=\"" + file.getFileName()
                + "\"\r\nContent-Type: application/octet-stream\r\n\r\n").getBytes(StandardCharsets.UTF_8));
            out.write(Files.readAllBytes(file));
            out.write(("\r\n--" + boundary + "--\r\n").getBytes(StandardCharsets.UTF_8));
            return send(request("/api/v2/route/").header("Content-Type", "multipart/form-data; boundary=" + boundary)
                .POST(HttpRequest.BodyPublishers.ofByteArray(out.toByteArray())).build());
        } catch (IOException e) {
            throw new Error(0, e.getMessage());
        }
    }

    private static void part(ByteArrayOutputStream out, String boundary, String name, String value) throws IOException {
        out.write(("--" + boundary + "\r\nContent-Disposition: form-data; name=\"" + name + "\"\r\n\r\n" + value + "\r\n").getBytes(StandardCharsets.UTF_8));
    }

    // -- two small JSON helpers, enough for a table; use a real parser for more --------------------
    /** The first value of "key" anywhere in json as text (strings unquoted, numbers and booleans as written), null when absent or null. */
    public static String field(String json, String key) {
        int i = json.indexOf("\"" + key + "\"");
        if (i < 0) return null;
        i = json.indexOf(':', i + key.length() + 2);
        if (i < 0) return null;
        for (i++; i < json.length() && Character.isWhitespace(json.charAt(i)); i++) { }
        if (i >= json.length()) return null;
        if (json.charAt(i) != '"') {
            int j = i;
            while (j < json.length() && ",}]".indexOf(json.charAt(j)) < 0) j++;
            String v = json.substring(i, j).trim();
            return v.equals("null") ? null : v;
        }
        StringBuilder sb = new StringBuilder();
        for (i++; i < json.length(); i++) {
            char c = json.charAt(i);
            if (c == '"') break;
            if (c != '\\') { sb.append(c); continue; }
            char n = json.charAt(++i);
            if (n == 'u') { sb.append((char) Integer.parseInt(json.substring(i + 1, i + 5), 16)); i += 4; }
            else sb.append(n == 'n' ? '\n' : n == 't' ? '\t' : n == 'r' ? '\r' : n);
        }
        return sb.toString();
    }

    /** The objects of the array "key" (each as its own JSON text), so a row can be read with field(row, ...). */
    public static List<String> objects(String json, String key) {
        List<String> rows = new ArrayList<>();
        int i = json.indexOf("\"" + key + "\"");
        if (i < 0 || (i = json.indexOf('[', i)) < 0) return rows;
        int depth = 0, start = -1;
        boolean inString = false;
        for (i++; i < json.length(); i++) {
            char c = json.charAt(i);
            if (inString) { if (c == '\\') i++; else if (c == '"') inString = false; continue; }
            if (c == '"') inString = true;
            else if (c == '{') { if (depth++ == 0) start = i; }
            else if (c == '}') { if (--depth == 0) rows.add(json.substring(start, i + 1)); }
            else if (c == ']' && depth == 0) break;
        }
        return rows;
    }
}
