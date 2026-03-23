@echo off
set ROOT=C:\AI\BillarLanzarote_DEMO
set PY="C:\Program Files\Python312\python.exe"

start "BL DEMO SIMULATOR STRESS" cmd /k %PY% %ROOT%\scripts\demo_match_simulator.py --mode stress
start "BL DEMO OVERLAY" cmd /k %PY% %ROOT%\scripts\demo_overlay_server.py
start "BL DEMO DASHBOARD" cmd /k %PY% %ROOT%\dashboard\control_panel\demo_control_panel.py
start http://127.0.0.1:8798
