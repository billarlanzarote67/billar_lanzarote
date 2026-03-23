@echo off
setlocal
set ROOT=C:\AI\BillarLanzarote
set LOG=%ROOT%\logs\watchdog\ai_launcher_v1.log
set FLAG=%ROOT%\services\watchdog\RESTART_AI_v1.flag
if not exist "%ROOT%\services\watchdog" mkdir "%ROOT%\services\watchdog"
echo %date% %time% > "%FLAG%"
echo [%date% %time%] AI restart flag written: %FLAG% >> "%LOG%"
call "%ROOT%\scripts\START_AI_CANONICAL_v1.bat"
exit /b %errorlevel%
