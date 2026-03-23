@echo off
setlocal

set ROOT=C:\AI\BillarLanzarote
set PYTHON_EXE=

if exist "C:\Program Files\Python312\python.exe" set PYTHON_EXE=C:\Program Files\Python312\python.exe
if "%PYTHON_EXE%"=="" if exist "C:\Program Files\Python313\python.exe" set PYTHON_EXE=C:\Program Files\Python313\python.exe
if "%PYTHON_EXE%"=="" for %%P in (py.exe python.exe) do (
  where %%P >nul 2>nul && set PYTHON_EXE=%%P
)

if "%PYTHON_EXE%"=="" (
  echo [ERROR] Python not found.
  pause
  exit /b 1
)

cd /d "%ROOT%"

if exist "%ROOT%\scripts\master_control_server.py" (
  start "BL Master Control" cmd /k ""%PYTHON_EXE%" "%ROOT%\scripts\master_control_server.py""
  start "" "http://127.0.0.1:5090"
) else (
  echo [ERROR] master_control_server.py not found.
  pause
  exit /b 1
)
