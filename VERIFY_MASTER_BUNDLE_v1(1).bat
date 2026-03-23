@echo off
setlocal
set ROOT=C:\AI\BillarLanzarote
echo ============================================
echo Billar Lanzarote Master Bundle Verification
echo ============================================

if not exist "%ROOT%\venv\Scripts\activate.bat" echo [FAIL] venv missing & goto :end
if not exist "%ROOT%\config\telegram_config.json" echo [FAIL] telegram_config.json missing & goto :end
if not exist "%ROOT%\config\telegram_remote_control_config_v1.json" echo [FAIL] telegram_remote_control_config_v1.json missing & goto :end
if not exist "%ROOT%\config\watchdog_config_v1.json" echo [FAIL] watchdog_config_v1.json missing & goto :end

if exist "%ROOT%\services\mediamtx\mediamtx.exe" (
  echo [PASS] MediaMTX exe found
) else (
  echo [WARN] MediaMTX exe missing
)

if exist "C:\Program Files\obs-studio\bin\64bit\obs64.exe" (
  echo [PASS] OBS exe found
) else if exist "C:\Program Files (x86)\obs-studio\bin\64bit\obs64.exe" (
  echo [PASS] OBS exe found
) else (
  echo [WARN] OBS exe not found in standard path
)

echo [PASS] basic verification complete
:end
pause
exit /b 0
