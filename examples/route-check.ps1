# Send a route file, get the NAVAREAs and the warnings along it. PowerShell 7 (pwsh) or Windows PowerShell 5.1.
#   $env:SEALAGOM_API_KEY = "YOUR_KEY"
#   .\route-check.ps1 -Route C:\routes\passage.rtz -CorridorNm 15
param([string]$Route = "passage.rtz", [double]$CorridorNm = 10, [double]$SpeedKn = 12)
$form = @{ file = Get-Item $Route; corridor_nm = "$CorridorNm"; speed_kn = "$SpeedKn" }
$r = Invoke-RestMethod -Method Post -Uri "https://www.sealagom.com/api/v2/route/" -Headers @{ "X-API-Token" = $env:SEALAGOM_API_KEY } -Form $form
"{0} NM, NAVAREAs: {1}, {2} warnings on the route" -f $r.route_nm, (($r.navareas | ForEach-Object { $_.name }) -join ", "), $r.count
$r.results | ForEach-Object { "  {0} {1}  {2} NM off at {3} NM  {4}  {5}" -f $_.region_title, $_.number, $_.distance_nm, $_.along_nm, $_.verdict, $_.ai.headline }
