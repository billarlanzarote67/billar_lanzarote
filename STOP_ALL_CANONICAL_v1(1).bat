@echo off
setlocal
taskkill /IM obs64.exe /F >nul 2>&1
taskkill /IM mediamtx.exe /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq *telegram_remote_control_v1.py*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq *watchdog_core_v1.py*" /F >nul 2>&1
echo Stop-all attempted.
pause
