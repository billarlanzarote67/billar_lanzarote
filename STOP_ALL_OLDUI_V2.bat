@echo off
echo Stopping common Python UI windows...
taskkill /FI "WINDOWTITLE eq BL Admin Stats*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq BL Player Gallery*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq BL H2H*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq BL Watcher*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq BL DB Saver*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq BL Master Control*" /T /F >nul 2>&1
echo Done.
pause
