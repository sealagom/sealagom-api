// Warnings in force around 55N 003E (the North Sea), as a table. .NET 8.
//   set SEALAGOM_API_KEY=YOUR_KEY
//   dotnet run --project examples/csharp
// Without a key the example lists the public feed catalogue instead, which needs no key.
// MIT License, Copyright (c) 2026 SeaLagom.

using System.Text.Json;
using SeaLagom;

using var api = new Client();
try
{
    if (string.IsNullOrEmpty(Environment.GetEnvironmentVariable("SEALAGOM_API_KEY")))
    {
        var feeds = await api.Feeds();
        Console.WriteLine($"{"Feed",-10} {"In force",8}  Title");
        foreach (var f in feeds.GetProperty("feeds").EnumerateArray())
        {
            var inForce = f.TryGetProperty("in_force", out var n) && n.ValueKind == JsonValueKind.Number ? n.GetInt32().ToString() : "";
            Console.WriteLine($"{f.GetProperty("slug").GetString(),-10} {inForce,8}  {f.GetProperty("title").GetString()}");
        }
        Console.WriteLine("Set SEALAGOM_API_KEY for the warnings around 55N 003E.");
        return;
    }

    var near = await api.WarningsNear(55.0, 3.0, 60);
    Console.WriteLine($"{near.GetProperty("count").GetInt32()} warnings in force within 60 NM of 55N 003E");
    Console.WriteLine($"{"Region",-14} {"Number",-12} {"NM",6}  {"Severity",-9} Headline");
    foreach (var w in near.GetProperty("warnings").EnumerateArray())
    {
        string severity = "", headline = "";
        if (w.TryGetProperty("ai", out var ai) && ai.ValueKind == JsonValueKind.Object)
        {
            severity = ai.TryGetProperty("severity", out var s) ? s.GetString() ?? "" : "";
            headline = ai.TryGetProperty("headline", out var h) ? h.GetString() ?? "" : "";
        }
        Console.WriteLine($"{w.GetProperty("region_title").GetString(),-14} {w.GetProperty("number").GetString(),-12} {w.GetProperty("distance_nm").GetDouble(),6:F1}  {severity,-9} {headline}");
    }
    if (api.LastHeaders.TryGetValue("X-API-Tokens-Remaining", out var left)) Console.WriteLine($"{left} requests left");
}
catch (SeaLagomException e)
{
    Console.Error.WriteLine($"SeaLagom {e.Status}: {e.Detail}");
    Environment.ExitCode = 1;
}
