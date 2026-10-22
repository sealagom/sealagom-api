# SeaLagom API client for PowerShell 7 (pwsh) and Windows PowerShell 5.1. No dependencies: Invoke-RestMethod.
# MIT License, Copyright (c) 2026 SeaLagom. See LICENSE in the repository root.
#
#   Import-Module ./powershell/SeaLagom.psm1
#   Connect-SeaLagom -Key "YOUR_KEY"                                   # or $env:SEALAGOM_API_KEY
#   $page = Search-SeaLagomWarnings @{ navarea_id = 1; ai_in_force = $true }
#   $near = Get-SeaLagomWarningsNear -Lat 55 -Lon 3 -RadiusNm 60       # warnings in force within 60 NM
#   $check = Test-SeaLagomRoute -File passage.rtz -CorridorNm 15       # the file needs PowerShell 7
#   $check = Test-SeaLagomRoute -Waypoints @(@(51.0, 1.5), @(36.1, -5.4)) -SpeedKn 14
#   Get-SeaLagomNavareas; Get-SeaLagomFeeds; Get-SeaLagomFeed military
#
# Lists are arrays: @{ ai_severity = @("critical", "high") }. Every answer is the JSON as served, as the
# objects Invoke-RestMethod makes; Get-SeaLagomLastHeaders gives the response headers of the last call
# (X-API-Tokens-Remaining; PowerShell 7 only). Errors throw "401: ..." with the server's detail (401 no or
# wrong key, 403 the plan does not include the call, 429 allowance or rate limit reached).
# Without a key only the public endpoints answer (feeds).

$script:Base = "https://www.sealagom.com"
$script:Key = ""
$script:TimeoutSec = 60
$script:LastHeaders = @{}

function Connect-SeaLagom {
    param([string]$Key = "", [string]$BaseUrl = "https://www.sealagom.com", [int]$TimeoutSec = 60)
    $script:Key = $Key.Trim()
    $script:Base = $BaseUrl.TrimEnd("/")
    $script:TimeoutSec = $TimeoutSec
}

function Get-SeaLagomLastHeaders { return $script:LastHeaders }

function ConvertTo-SeaLagomQuery {
    param([hashtable]$Params)
    if (-not $Params -or $Params.Count -eq 0) { return "" }
    $parts = @()
    foreach ($k in $Params.Keys) {
        $v = $Params[$k]
        if ($null -eq $v) { continue }
        foreach ($x in @($v)) {
            $s = if ($x -is [bool]) { if ($x) { "true" } else { "false" } } else { [string]$x }
            $parts += [uri]::EscapeDataString([string]$k) + "=" + [uri]::EscapeDataString($s)
        }
    }
    if ($parts.Count -eq 0) { return "" }
    return "?" + ($parts -join "&")
}

function Format-SeaLagomError {
    param($ErrorRecord)
    $status = 0; $body = ""
    try { $status = [int]$ErrorRecord.Exception.Response.StatusCode } catch {}
    if ($ErrorRecord.ErrorDetails -and $ErrorRecord.ErrorDetails.Message) { $body = $ErrorRecord.ErrorDetails.Message }
    elseif ($ErrorRecord.Exception.Response) {
        try { $body = (New-Object System.IO.StreamReader($ErrorRecord.Exception.Response.GetResponseStream())).ReadToEnd() } catch {}
    }
    $detail = ""
    try { $detail = ($body | ConvertFrom-Json).detail } catch {}
    if (-not $detail) { $detail = if ($body) { $body.Substring(0, [Math]::Min(200, $body.Length)) } else { $ErrorRecord.Exception.Message } }
    return "${status}: $detail"
}

function Invoke-SeaLagom {
    param([string]$Path, [string]$Method = "Get", [hashtable]$Params, $Json, [hashtable]$Form)
    $key = if ($script:Key) { $script:Key } else { [string]$env:SEALAGOM_API_KEY }
    $headers = @{ "Accept" = "application/json"; "X-Requested-With" = "sealagom-kit" }
    if ($key.Trim()) { $headers["X-API-Token"] = $key.Trim() }
    $call = @{ Method = $Method; Uri = ($script:Base + $Path + (ConvertTo-SeaLagomQuery $Params)); Headers = $headers
               UserAgent = "sealagom-powershell/1.0"; TimeoutSec = $script:TimeoutSec; ErrorAction = "Stop" }
    if ($null -ne $Json) { $call.ContentType = "application/json"; $call.Body = ($Json | ConvertTo-Json -Depth 10 -Compress) }
    if ($Form) {
        if ($PSVersionTable.PSVersion.Major -lt 7) { throw "Sending a route file needs PowerShell 7 (pwsh); pass -Waypoints on Windows PowerShell 5.1" }
        $call.Form = $Form
    }
    $responseHeaders = $null
    if ($PSVersionTable.PSVersion.Major -ge 7) { $call.ResponseHeadersVariable = "responseHeaders" }
    try { $data = Invoke-RestMethod @call } catch { throw (Format-SeaLagomError $_) }
    if ($responseHeaders) { $script:LastHeaders = $responseHeaders }
    return $data
}

# GET /api/v2/messages/: navarea_id, coastal_id, country, q, date_from, date_to, keyword, has_coordinates, include_archived,
# include_ai_analysis, ai_severity, ai_category, ai_in_force, expires_within_hours, topic, page, page_size. Answer: count, next, results.
function Search-SeaLagomWarnings { param([hashtable]$Params = @{}) Invoke-SeaLagom -Path "/api/v2/messages/" -Params $Params }

# GET /api/v2/near/: warnings in force within RadiusNm (up to 200) of a position. Answer: count, warnings (region_title, number,
# distance_nm, nearest, ai.headline, ai.severity, ai.valid_until).
function Get-SeaLagomWarningsNear {
    param([Parameter(Mandatory)][double]$Lat, [Parameter(Mandatory)][double]$Lon, [double]$RadiusNm = 30)
    $inv = [cultureinfo]::InvariantCulture
    Invoke-SeaLagom -Path "/api/v2/near/" -Params @{ lat = $Lat.ToString($inv); lon = $Lon.ToString($inv); radius_nm = $RadiusNm.ToString($inv) }
}

# GET /api/v2/navarea/: the 21 NAVAREAs with their region ids.
function Get-SeaLagomNavareas { param([hashtable]$Params = @{}) Invoke-SeaLagom -Path "/api/v2/navarea/" -Params $Params }

# GET /api/v2/feeds/: every feed with its endpoint and warnings in force (no key needed). Answer: feeds.
function Get-SeaLagomFeeds { Invoke-SeaLagom -Path "/api/v2/feeds/" }

# GET /api/v2/feeds/<slug>/: one themed feed (military, cables, offshore, survey, hazards, ice...).
function Get-SeaLagomFeed {
    param([Parameter(Mandatory)][string]$Slug, [hashtable]$Params = @{})
    Invoke-SeaLagom -Path ("/api/v2/feeds/" + [uri]::EscapeDataString($Slug) + "/") -Params $Params
}

# POST /api/v2/route/ with a route file (RTZ, RT3, GPX, KML, CSV, NMEA) or with -Waypoints @(@(lat, lon), ...).
# Answer: route_nm, navareas, count, results (distance_nm, along_nm, verdict, ai).
function Test-SeaLagomRoute {
    param([string]$File, [array]$Waypoints, [double]$SpeedKn = 12, [double]$CorridorNm = 10, [string]$Departure)
    if ($File) {
        $form = @{ file = Get-Item $File; speed_kn = "$SpeedKn"; corridor_nm = "$CorridorNm" }
        if ($Departure) { $form.departure = $Departure }
        return Invoke-SeaLagom -Path "/api/v2/route/" -Method Post -Form $form
    }
    if (-not $Waypoints -or $Waypoints.Count -lt 2) { throw "Pass -File or at least two -Waypoints" }
    $body = @{ waypoints = @($Waypoints | ForEach-Object { @{ lat = [double]$_[0]; lon = [double]$_[1] } }); speed_kn = $SpeedKn; corridor_nm = $CorridorNm }
    if ($Departure) { $body.departure = $Departure }
    return Invoke-SeaLagom -Path "/api/v2/route/" -Method Post -Json $body
}

Export-ModuleMember -Function Connect-SeaLagom, Get-SeaLagomLastHeaders, Search-SeaLagomWarnings, Get-SeaLagomWarningsNear, Get-SeaLagomNavareas, Get-SeaLagomFeeds, Get-SeaLagomFeed, Test-SeaLagomRoute
