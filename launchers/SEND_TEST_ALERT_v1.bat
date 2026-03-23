@echo off
set ROOT=C:\AI\BillarLanzarote
set PYTHON_EXE=C:\Program Files\Python312\python.exe
cd /d %ROOT%\services\telegram
"%PYTHON_EXE%" send_test_alert_v1.py "%ROOT%\config\telegram_config.json"
