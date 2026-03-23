@echo off
set /p URL=Paste CueScore player profile URL: 
cd /d C:\AI\BillarLanzarote\scripts
"C:\Program Files\Python312\python.exe" import_player_profile.py "%URL%"
pause

