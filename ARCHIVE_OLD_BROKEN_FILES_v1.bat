@echo off
setlocal
set ROOT=C:\AI\BillarLanzarote
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set TS=%%i
set ARCH=%ROOT%\_ARCHIVE_OLD\%TS%
mkdir "%ARCH%" 2>nul

if exist "%ROOT%\scripts\run_watchdog_full.bat" move "%ROOT%\scripts\run_watchdog_full.bat" "%ARCH%"
if exist "%ROOT%\scripts\run_all_alerts.bat" move "%ROOT%\scripts\run_all_alerts.bat" "%ARCH%"
if exist "%ROOT%\scripts\run_telegram_test_clean.bat" move "%ROOT%\scripts\run_telegram_test_clean.bat" "%ARCH%"
if exist "%ROOT%\billar_watchdog_telegram_alerts_pack_v1\services\watchdog\runallalerts.py" move "%ROOT%\billar_watchdog_telegram_alerts_pack_v1\services\watchdog\runallalerts.py" "%ARCH%"
if exist "%ROOT%\billar_watchdog_telegram_alerts_pack_v1\services\watchdog\runallalerts.bat" move "%ROOT%\billar_watchdog_telegram_alerts_pack_v1\services\watchdog\runallalerts.bat" "%ARCH%"
if exist "%ROOT%\billar_watchdog_telegram_alerts_pack_v1\services\watchdog\telegram_config.json" move "%ROOT%\billar_watchdog_telegram_alerts_pack_v1\services\watchdog\telegram_config.json" "%ARCH%"
echo Archived old/broken files to %ARCH%
pause
