@echo off
setlocal
set "ROOT=C:\AI\BillarLanzarote"
set "PY=C:\Program Files\Python312\python.exe"
if not exist "%PY%" set "PY=py"

echo =====================================
echo Billar Lanzarote - Start All Fixed v2
echo ROOT=%ROOT%
echo PY=%PY%
echo =====================================

if exist "%ROOT%\scripts\live_tables_watcher_final_capture_v1_4.py" (
    start "BL Watcher" cmd /k "cd /d "%ROOT%\scripts" && "%PY%" live_tables_watcher_final_capture_v1_4.py"
) else (
    echo WARNING: live_tables_watcher_final_capture_v1_4.py not found
)

if exist "%ROOT%\dashboard\admin_stats\app.py" (
    start "BL Admin Stats" cmd /k "cd /d "%ROOT%\dashboard\admin_stats" && "%PY%" app.py"
) else (
    echo WARNING: admin stats app not found
)

if exist "%ROOT%\dashboard\web_ui\app.py" (
    start "BL Player Gallery" cmd /k "cd /d "%ROOT%\dashboard\web_ui" && "%PY%" app.py"
) else (
    echo WARNING: player gallery app not found
)

if exist "%ROOT%\scripts\player_h2h_dashboard_fixed.py" (
    start "BL H2H" cmd /k "cd /d "%ROOT%\scripts" && "%PY%" player_h2h_dashboard_fixed.py"
) else if exist "%ROOT%\scripts\player_h2h_dashboard.py" (
    start "BL H2H" cmd /k "cd /d "%ROOT%\scripts" && "%PY%" player_h2h_dashboard.py"
) else (
    echo WARNING: no working H2H dashboard found
)

if exist "%ROOT%\scripts\master_control_recovery_v2.py" (
    start "BL Master Control" cmd /k "cd /d "%ROOT%\scripts" && "%PY%" master_control_recovery_v2.py"
) else (
    echo INFO: master_control_recovery_v2.py not found, skipping
)

echo.
echo Start commands sent.
pause
endlocal
