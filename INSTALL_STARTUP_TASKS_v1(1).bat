@echo off
setlocal
set ROOT=C:\AI\BillarLanzarote
schtasks /Delete /TN "BillarLanzaroteMasterV1" /F >nul 2>&1
schtasks /Create /TN "BillarLanzaroteMasterV1" /SC ONSTART /RU SYSTEM /RL HIGHEST /TR "\"%ROOT%\scripts\START_MASTER_SYSTEM_CANONICAL_v1.bat\"" /F
if errorlevel 1 (
  echo Failed to create startup task.
  pause
  exit /b 1
)
echo Startup task installed.
pause
