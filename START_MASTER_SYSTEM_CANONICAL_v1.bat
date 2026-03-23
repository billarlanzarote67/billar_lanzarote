@echo off
setlocal
set ROOT=C:\AI\BillarLanzarote
set LOG=%ROOT%\logs\watchdog\master_launcher_v1.log
if not exist "%ROOT%\logs\watchdog" mkdir "%ROOT%\logs\watchdog"

if exist "%ROOT%\services\mediamtx\mediamtx.exe" (
  tasklist /FI "IMAGENAME eq mediamtx.exe" | find /I "mediamtx.exe" >nul
  if errorlevel 1 (
    start "" "%ROOT%\services\mediamtx\mediamtx.exe"
    echo [%date% %time%] Started MediaMTX >> "%LOG%"
  ) else (
    echo [%date% %time%] MediaMTX already running >> "%LOG%"
  )
) else (
  echo [%date% %time%] MediaMTX exe missing >> "%LOG%"
)

tasklist /FI "IMAGENAME eq obs64.exe" | find /I "obs64.exe" >nul
if errorlevel 1 (
  call "%ROOT%\scripts\START_OBS_CANONICAL_v1.bat"
) else (
  echo [%date% %time%] OBS already running >> "%LOG%"
)

call "%ROOT%\scripts\START_AI_CANONICAL_v1.bat"

start "" cmd /c "%ROOT%\scripts\START_WATCHDOG_CANONICAL_v1.bat"
start "" cmd /c "%ROOT%\scripts\START_TELEGRAM_REMOTE_CONTROL_v1.bat"
echo [%date% %time%] Master launcher complete >> "%LOG%"
exit /b 0
