@echo off
setlocal
set ROOT=C:\AI\BillarLanzarote
set LOG=%ROOT%\logs\watchdog\obs_launcher_v1.log
if not exist "%ROOT%\logs\watchdog" mkdir "%ROOT%\logs\watchdog"

set OBS_EXE=
if exist "C:\Program Files\obs-studio\bin\64bit\obs64.exe" set OBS_EXE=C:\Program Files\obs-studio\bin\64bit\obs64.exe
if not defined OBS_EXE if exist "C:\Program Files (x86)\obs-studio\bin\64bit\obs64.exe" set OBS_EXE=C:\Program Files (x86)\obs-studio\bin\64bit\obs64.exe

if not defined OBS_EXE (
  echo [%date% %time%] OBS executable not found >> "%LOG%"
  exit /b 1
)
start "" "%OBS_EXE%"
echo [%date% %time%] Started OBS: %OBS_EXE% >> "%LOG%"
exit /b 0
