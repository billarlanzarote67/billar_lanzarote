@echo off
setlocal
set ROOT=C:\AI\BillarLanzarote
set LOG=%ROOT%\logs\watchdog\ai_launcher_v1.log
if not exist "%ROOT%\logs\watchdog" mkdir "%ROOT%\logs\watchdog"
if not exist "%ROOT%\services\watchdog" mkdir "%ROOT%\services\watchdog"
call "%ROOT%\venv\Scripts\activate.bat"
if exist "%ROOT%\START_ALL_v5.bat" (
  start "" cmd /c "%ROOT%\START_ALL_v5.bat"
  echo [%date% %time%] Started AI/system via START_ALL_v5.bat >> "%LOG%"
  exit /b 0
)
echo [%date% %time%] No canonical AI entrypoint found; V1 using flag-only recovery >> "%LOG%"
exit /b 0
