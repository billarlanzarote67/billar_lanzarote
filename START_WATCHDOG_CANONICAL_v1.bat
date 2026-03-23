@echo off
setlocal
set ROOT=C:\AI\BillarLanzarote
call "%ROOT%\venv\Scripts\activate.bat"
cd /d "%ROOT%\scripts"
python watchdog_core_v1.py
exit /b %errorlevel%
