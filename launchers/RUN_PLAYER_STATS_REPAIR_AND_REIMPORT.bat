@echo off
cd /d C:\AI\BillarLanzarote\scripts
"C:\Program Files\Python312\python.exe" repair_player_stats_db.py
"C:\Program Files\Python312\python.exe" import_tournament_results_any_v2.py --url "https://cuescore.com/tournament/Inaguraci%C3%B3n+Billar+Lanzarote/77005630" --mode update
pause
