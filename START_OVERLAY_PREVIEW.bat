@echo off
setlocal

set ROOT=C:\AI\BillarLanzarote
set PY=C:\Program Files\Python312\python.exe

echo Starting Overlay Preview...
cd /d "%ROOT%"

if exist "%PY%" (
    start "Overlay Preview" cmd /k ""%PY%" "%ROOT%\scripts\overlay_preview_server.py""
) else (
    echo Python not found at "%PY%"
    echo Trying fallback...
    start "Overlay Preview" cmd /k "python "%ROOT%\scripts\overlay_preview_server.py""
)

exit /b 0