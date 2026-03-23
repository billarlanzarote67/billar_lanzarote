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
start "BL Player Gallery v3" cmd /k ""%PYTHON_EXE%" "%ROOT%\scripts\player_pages_recovery_v3.py" gallery"
start "BL Player H2H v3" cmd /k ""%PYTHON_EXE%" "%ROOT%\scripts\player_pages_recovery_v3.py" h2h"
start "BL Player Profile v3" cmd /k ""%PYTHON_EXE%" "%ROOT%\scripts\player_pages_recovery_v3.py" profile"
start "" "http://127.0.0.1:8099"
start "" "http://127.0.0.1:8097"
