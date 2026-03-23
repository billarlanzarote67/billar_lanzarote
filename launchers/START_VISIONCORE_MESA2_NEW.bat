@echo off
title START VISIONCORE MESA2
setlocal

set ROOT=C:\AI\BillarLanzarote
set PY=C:\Program Files\Python312\python.exe

cd /d "%ROOT%"

echo Starting Mesa2 VisionCore...

start "M2 Frame Grabber" cmd /k ""%PY%" "%ROOT%\scripts\visioncore\frame_grabber.py" mesa2"
start "M2 Motion Detector" cmd /k ""%PY%" "%ROOT%\scripts\visioncore\motion_detector.py" mesa2"
start "M2 Event Engine" cmd /k ""%PY%" "%ROOT%\scripts\visioncore\event_engine.py" mesa2"

exit /b 0