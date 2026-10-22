# Warnings in force around 55N 003E (the North Sea), as a table. PowerShell 7 or Windows PowerShell 5.1.
#   $env:SEALAGOM_API_KEY = "YOUR_KEY"
#   .\examples\powershell\near.ps1
# Without a key the example lists the public feed catalogue instead, which needs no key.
# MIT License, Copyright (c) 2026 SeaLagom.
Import-Module (Join-Path $PSScriptRoot "../../powershell/SeaLagom.psm1") -Force

try {
    if (-not $env:SEALAGOM_API_KEY) {
        $feeds = Get-SeaLagomFeeds
        "{0,-10} {1,8}  {2}" -f "Feed", "In force", "Title"
        foreach ($f in $feeds.feeds) { "{0,-10} {1,8}  {2}" -f $f.slug, $f.in_force, $f.title }
        "Set SEALAGOM_API_KEY for the warnings around 55N 003E."
        exit 0
    }
    $near = Get-SeaLagomWarningsNear -Lat 55 -Lon 3 -RadiusNm 60
    "{0} warnings in force within 60 NM of 55N 003E" -f $near.count
    "{0,-14} {1,-12} {2,6}  {3,-9} {4}" -f "Region", "Number", "NM", "Severity", "Headline"
    foreach ($w in $near.warnings) {
        "{0,-14} {1,-12} {2,6:N1}  {3,-9} {4}" -f $w.region_title, $w.number, $w.distance_nm, $w.ai.severity, $w.ai.headline
    }
    $left = (Get-SeaLagomLastHeaders)["X-API-Tokens-Remaining"]
    if ($left) { "{0} requests left" -f ($left -join ", ") }
} catch {
    Write-Error "SeaLagom $($_.Exception.Message)"
    exit 1
}
