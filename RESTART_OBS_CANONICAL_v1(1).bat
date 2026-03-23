@echo off
setlocal
set ROOT=C:\AI\BillarLanzarote
set LOG=%ROOT%\logs\watchdog\obs_launcher_v1.log
taskkill /IM obs64.exe /F >nul 2>&1
timeout /t 3 /nobreak >nul
call "%ROOT%\scripts\START_OBS_CANONICAL_v1.bat"
if errorlevel 1 (
  echo [%date% %time%] OBS restart failed >> "%LOG%"
  exit /b 1
)
timeout /t 8 /nobreak >nul
echo [%date% %time%] OBS restarted; scene target left to Telegram selection >> "%LOG%"
exit /b 0
