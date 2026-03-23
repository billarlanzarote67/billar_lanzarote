@echo off
setlocal
set "ROOT=C:\AI\BillarLanzarote"
set "PY=C:\Program Files\Python312\python.exe"
if not exist "%PY%" set "PY=py"

start "BL Admin Stats" cmd /k "cd /d "%ROOT%\dashboard\admin_stats" && "%PY%" app.py"
start "BL Player Gallery" cmd /k "cd /d "%ROOT%\dashboard\web_ui" && "%PY%" app.py"
start "BL H2H" cmd /k "cd /d "%ROOT%\scripts" && "%PY%" player_h2h_server.py"

endlocal
