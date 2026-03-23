@echo off
setlocal
set ROOT=C:\AI\BillarLanzarote
set PYTHON_EXE=
if exist "C:\Program Files\Python312\python.exe" set PYTHON_EXE=C:\Program Files\Python312\python.exe
if "%PYTHON_EXE%"=="" if exist "C:\Program Files\Python313\python.exe" set PYTHON_EXE=C:\Program Files\Python313\python.exe
if "%PYTHON_EXE%"=="" for %%P in (py.exe python.exe) do (
  where %%P >nul 2>nul && set PYTHON_EXE=%%P
)
start "BL Player Gallery" cmd /k ""%PYTHON_EXE%" "%ROOT%\scripts\player_gallery_server_v2.py""
start "" "http://127.0.0.1:8099"
