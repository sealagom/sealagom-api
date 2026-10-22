@echo off
rem Send a route file, get the NAVAREAs and the warnings along it. Windows, curl is built in since Windows 10.
rem   set SEALAGOM_API_KEY=YOUR_KEY
rem   route-check.bat C:\routes\passage.rtz 15
set ROUTE=%~1
if "%ROUTE%"=="" set ROUTE=passage.rtz
set CORRIDOR=%~2
if "%CORRIDOR%"=="" set CORRIDOR=10
curl -sS -X POST https://www.sealagom.com/api/v2/route/ -H "X-API-Token: %SEALAGOM_API_KEY%" -F "file=@%ROUTE%" -F "corridor_nm=%CORRIDOR%" -o result.json
if errorlevel 1 (echo request failed & exit /b 1)
type result.json
