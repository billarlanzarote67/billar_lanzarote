@echo off
setlocal
schtasks /Delete /TN "BillarLanzaroteMasterV1" /F >nul 2>&1
call C:\AI\BillarLanzarote\scripts\INSTALL_STARTUP_TASKS_v1.bat
