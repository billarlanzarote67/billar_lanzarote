@echo off
setlocal
title Billar Lanzarote - STATUS ALL v5

set ROOT=C:\AI\BillarLanzarote
set PYTHON_EXE=C:\Program Files\Python312\python.exe
set CFG=%ROOT%\config\master_control_config_v5.json

if not exist "%PYTHON_EXE%" (
  echo [ERROR] Python 3.12 not found at %PYTHON_EXE%
  exit /b 1
)

"%PYTHON_EXE%" "%ROOT%\services\control\master_health_check_v5.py" "%CFG%"
pause
