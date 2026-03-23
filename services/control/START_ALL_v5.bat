@echo off
setlocal
title Billar Lanzarote - START ALL v5

set ROOT=C:\AI\BillarLanzarote
set PYTHON_EXE=C:\Program Files\Python312\python.exe
set CFG=%ROOT%\config\master_control_config_v5.json

if not exist "%PYTHON_EXE%" (
  echo [ERROR] Python 3.12 not found at %PYTHON_EXE%
  exit /b 1
)

rem Start master health check once
"%PYTHON_EXE%" "%ROOT%\services\control\master_health_check_v5.py" "%CFG%"

rem Start dashboard
start "Dashboard v5" cmd /c ""%PYTHON_EXE%" "%ROOT%\services\dashboard\dashboard_server_v5.py" "%ROOT%" 8787"

rem Start known launchers if present
for %%F in (
  "%ROOT%\launchers\START_WATCHDOG.bat"
  "%ROOT%\launchers\START_CUESCORE_CONTEXT.bat"
  "%ROOT%\launchers\START_OVERLAY_STATE.bat"
  "%ROOT%\launchers\START_AI_STATE_BASELINE_v5.bat"
  "%ROOT%\launchers\START_PACK_06_v5.bat"
  "%ROOT%\launchers\START_PACK_07_v5.bat"
  "%ROOT%\launchers\START_PACK_08_v5.bat"
  "%ROOT%\launchers\START_PACK_09_v5.bat"
  "%ROOT%\launchers\START_PACK_10_v5.bat"
  "%ROOT%\launchers\START_PACK_11_v5.bat"
  "%ROOT%\launchers\START_PACK_12_v5.bat"
) do (
  if exist %%F start "%%~nF" cmd /c %%F
)

start "" http://127.0.0.1:8787
echo [OK] START_ALL_v5 launched
