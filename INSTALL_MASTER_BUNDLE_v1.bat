@echo off
setlocal
set ROOT=C:\AI\BillarLanzarote
echo ============================================
echo Installing Billar Lanzarote Master Bundle
echo ============================================

if not exist "%ROOT%\logs\telegram" mkdir "%ROOT%\logs\telegram"
if not exist "%ROOT%\logs\watchdog" mkdir "%ROOT%\logs\watchdog"
if not exist "%ROOT%\state" mkdir "%ROOT%\state"
if not exist "%ROOT%\services\control" mkdir "%ROOT%\services\control"
if not exist "%ROOT%\services\watchdog" mkdir "%ROOT%\services\watchdog"

call "%ROOT%\venv\Scripts\activate.bat"
if errorlevel 1 (
  echo Failed to activate venv.
  pause
  exit /b 1
)

pip install websocket-client
if errorlevel 1 (
  echo websocket-client install failed
  pause
  exit /b 1
)

echo Install complete.
pause
