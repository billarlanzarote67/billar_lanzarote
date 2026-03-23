@echo off
title Billar Lanzarote - Start MediaMTX v1

REM Set paths
set ROOT=C:\AI\BillarLanzarote\services\mediamtx
set MEDIAMTX_EXE=%ROOT%\mediamtx.exe

REM Check if MediaMTX exists
if not exist "%MEDIAMTX_EXE%" (
    echo [ERROR] MediaMTX executable not found at %MEDIAMTX_EXE%
    pause
    exit /b 1
)

REM Start Mesa 1 stream (port 8554)
start "" "%MEDIAMTX_EXE%" --port 8554 --stream /mesa1

REM Start Mesa 2 stream (port 8555)
start "" "%MEDIAMTX_EXE%" --port 8555 --stream /mesa2

echo MediaMTX streams started for Mesa 1 (8554) and Mesa 2 (8555)
pause