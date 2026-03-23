@echo off
set ROOT=C:\AI\BillarLanzarote
set PYTHON_EXE=C:\Program Files\Python312\python.exe
cd /d %ROOT%\services\watchdog
"%PYTHON_EXE%" watchdog_telegram_alerts_v1.py "%ROOT%\config\telegram_config.json"
