@echo off
setlocal

set ROOT=C:\AI\BillarLanzarote
set PY=C:\Progra~1\Python312\python.exe

echo ==============================
echo STARTING STABLE V3 SYSTEM
echo ==============================

start "BL STABLE V3 WATCHER" cmd /k ""%PY%" "%ROOT%\scripts\stable_v3_match_watcher.py""
start "BL STABLE V3 OVERLAY API" cmd /k ""%PY%" "%ROOT%\scripts\stable_v3_overlay_server.py""
start "BL STABLE V3 CONTROL PANEL" cmd /k ""%PY%" "%ROOT%\scripts\stable_v3_control_panel.py""
start "BL STABLE V3 STREAM CTRL" cmd /k ""%PY%" "%ROOT%\scripts\stable_v3_stream_controller.py""

timeout /t 2 >nul
start http://127.0.0.1:8788

exit /b 0