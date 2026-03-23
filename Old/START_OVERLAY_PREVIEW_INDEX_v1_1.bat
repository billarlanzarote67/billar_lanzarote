@echo off
set ROOT=C:\AI\BillarLanzarote
set PYTHON_EXE=C:\Program Files\Python312\python.exe
cd /d "%ROOT%\addons\overlay_preview_index_v1_1"
"%PYTHON_EXE%" overlay_preview_server_v1_1.py
