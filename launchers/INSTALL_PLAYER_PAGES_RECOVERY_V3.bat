@echo off
setlocal
set ROOT=C:\AI\BillarLanzarote
set PACKDIR=%~dp0..

mkdir "%ROOT%\scripts" 2>nul
mkdir "%ROOT%\bat" 2>nul

copy /Y "%PACKDIR%\scripts\player_pages_recovery_v3.py" "%ROOT%\scripts\player_pages_recovery_v3.py" >nul
copy /Y "%PACKDIR%\bat\START_PLAYER_PAGES_RECOVERY_V3.bat" "%ROOT%\bat\START_PLAYER_PAGES_RECOVERY_V3.bat" >nul

echo Installed player pages recovery v3.
pause
