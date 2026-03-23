@echo off
set /p URL=Paste CueScore finished match URL: 
cd /d C:\AI\BillarLanzarote\scripts
"C:\Program Files\Python312\python.exe" import_finished_match.py "%URL%"
pause

