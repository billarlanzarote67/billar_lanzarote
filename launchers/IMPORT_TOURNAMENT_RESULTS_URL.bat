@echo off
setlocal
set /p URL=Paste CueScore tournament URL: 
cd /d C:\AI\BillarLanzarote\scripts
"C:\Program Files\Python312\python.exe" import_tournament_results_any_v2.py --url "%URL%" --mode update
pause
