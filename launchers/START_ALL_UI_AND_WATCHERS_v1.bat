@echo off
setlocal

set ROOT=C:\AI\BillarLanzarote
set PY=C:\Program Files\Python312\python.exe

if not exist "%PY%" set PY=py

echo ==========================================
echo Billar Lanzarote - Start All UI + Watchers
echo ROOT=%ROOT%
echo PY=%PY%
echo ==========================================
echo.

cd /d "%ROOT%"

REM ----- Master Control -----
if exist "%ROOT%\scripts\master_control_server.py" (
    start "BL_MasterControl" %PY% "%ROOT%\scripts\master_control_server.py"
) else if exist "%ROOT%\scripts\master_control_server_v2.py" (
    start "BL_MasterControl" %PY% "%ROOT%\scripts\master_control_server_v2.py"
) else (
    echo [WARN] master control script not found
)

timeout /t 2 >nul

REM ----- Live Watcher -----
if exist "%ROOT%\scripts\live_tables_watcher_final_capture_v1_5.py" (
    start "BL_LiveWatcher" %PY% "%ROOT%\scripts\live_tables_watcher_final_capture_v1_5.py"
) else if exist "%ROOT%\scripts\live_tables_watcher_final_capture_v1_4.py" (
    start "BL_LiveWatcher" %PY% "%ROOT%\scripts\live_tables_watcher_final_capture_v1_4.py"
) else (
    echo [WARN] no live_tables_watcher_final_capture script found
)

timeout /t 2 >nul

REM ----- Gallery -----
if exist "%ROOT%\dashboard\web_ui\app.py" (
    start "BL_Gallery" %PY% "%ROOT%\dashboard\web_ui\app.py"
) else (
    echo [WARN] dashboard web_ui app not found
)

timeout /t 2 >nul

REM ----- Stats -----
if exist "%ROOT%\scripts\player_stats_dashboard.py" (
    start "BL_Stats" %PY% "%ROOT%\scripts\player_stats_dashboard.py"
) else (
    echo [WARN] player_stats_dashboard.py not found
)

timeout /t 2 >nul

REM ----- H2H -----
if exist "%ROOT%\scripts\player_h2h_dashboard_fixed.py" (
    start "BL_H2H" %PY% "%ROOT%\scripts\player_h2h_dashboard_fixed.py"
) else if exist "%ROOT%\scripts\player_h2h_dashboard.py" (
    start "BL_H2H" %PY% "%ROOT%\scripts\player_h2h_dashboard.py"
) else (
    echo [WARN] no working H2H dashboard script found
)

echo.
echo Done.
echo Master Control: http://127.0.0.1:5090
echo Stats:          http://127.0.0.1:8098
echo Gallery:        http://127.0.0.1:8099
echo H2H:            http://127.0.0.1:8097
echo.
pause
endlocal
