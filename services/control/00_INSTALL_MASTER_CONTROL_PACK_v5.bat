@echo off
setlocal
title Billar Lanzarote - Master Control Pack v5 Installer

set ROOT=C:\AI\BillarLanzarote
set PYTHON_EXE=C:\Program Files\Python312\python.exe
set PACK_DIR=%~dp0

if not exist "%ROOT%" (
  echo [ERROR] Root path not found: %ROOT%
  exit /b 1
)

mkdir "%ROOT%\config" 2>nul
mkdir "%ROOT%\services\control" 2>nul
mkdir "%ROOT%\services\dashboard" 2>nul
mkdir "%ROOT%\logs\system" 2>nul
mkdir "%ROOT%\launchers" 2>nul

copy /Y "%PACK_DIR%config\master_control_config_v5.json" "%ROOT%\config\master_control_config_v5.json" >nul
copy /Y "%PACK_DIR%services\control\control_helpers_v5.py" "%ROOT%\services\control\control_helpers_v5.py" >nul
copy /Y "%PACK_DIR%services\control\master_health_check_v5.py" "%ROOT%\services\control\master_health_check_v5.py" >nul
copy /Y "%PACK_DIR%services\dashboard\dashboard_server_v5.py" "%ROOT%\services\dashboard\dashboard_server_v5.py" >nul

copy /Y "%PACK_DIR%INSTALL_ALL_v5.bat" "%ROOT%\INSTALL_ALL_v5.bat" >nul
copy /Y "%PACK_DIR%START_ALL_v5.bat" "%ROOT%\START_ALL_v5.bat" >nul
copy /Y "%PACK_DIR%STOP_ALL_v5.bat" "%ROOT%\STOP_ALL_v5.bat" >nul
copy /Y "%PACK_DIR%STATUS_ALL_v5.bat" "%ROOT%\STATUS_ALL_v5.bat" >nul
copy /Y "%PACK_DIR%CHECK_SYSTEM_HEALTH_v5.bat" "%ROOT%\CHECK_SYSTEM_HEALTH_v5.bat" >nul
copy /Y "%PACK_DIR%VIEW_LOGS_v5.bat" "%ROOT%\VIEW_LOGS_v5.bat" >nul

echo [OK] Master Control Pack v5 installed to %ROOT%
echo NEXT:
echo 1. Run INSTALL_ALL_v5.bat
echo 2. Run START_ALL_v5.bat
echo 3. Open dashboard at http://127.0.0.1:8787
