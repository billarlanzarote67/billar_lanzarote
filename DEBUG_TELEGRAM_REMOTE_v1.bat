@echo off
setlocal
set ROOT=C:\AI\BillarLanzarote
call "%ROOT%\venv\Scripts\activate.bat"
cd /d "%ROOT%\scripts"
python telegram_remote_control_v1.py
pause
