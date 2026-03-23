@echo off
setlocal
set ROOT=C:\AI\BillarLanzarote
schtasks /Delete /TN "BillarLanzaroteMasterV1" /F >nul 2>&1
schtasks /Create /TN "BillarLanzaroteMasterV1" /SC ONSTART /RU SYSTEM /RL HIGHEST /TR "\"%ComSpec%\" /c %ROOT%\launchers\START_ALL_UI_AND_WATCHERS_v1.bat" /F
if errorlevel 1 (
  echo Failed to create startup task.
  pause
  exit /b 1
)
echo Startup task installed.
pause
