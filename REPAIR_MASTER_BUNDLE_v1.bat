@echo off
setlocal
set ROOT=C:\AI\BillarLanzarote
call "%ROOT%\venv\Scripts\activate.bat"
pip install --upgrade pip
pip install websocket-client
echo Repair complete.
pause
