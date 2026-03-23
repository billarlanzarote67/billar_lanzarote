@echo off
setlocal
set ROOT=C:\AI\BillarLanzarote
set PACKDIR=%~dp0..

mkdir "%ROOT%\scripts" 2>nul
mkdir "%ROOT%\bat" 2>nul

copy /Y "%PACKDIR%\scripts\player_gallery_server_v2.py" "%ROOT%\scripts\player_gallery_server_v2.py" >nul
copy /Y "%PACKDIR%\scripts\player_h2h_server_v2.py" "%ROOT%\scripts\player_h2h_server_v2.py" >nul
copy /Y "%PACKDIR%\bat\START_MASTERCONTROL_FIXED.bat" "%ROOT%\bat\START_MASTERCONTROL_FIXED.bat" >nul
copy /Y "%PACKDIR%\bat\START_PLAYER_GALLERY_V2.bat" "%ROOT%\bat\START_PLAYER_GALLERY_V2.bat" >nul
copy /Y "%PACKDIR%\bat\START_PLAYER_H2H_V2.bat" "%ROOT%\bat\START_PLAYER_H2H_V2.bat" >nul

echo UI recovery files installed.
pause
