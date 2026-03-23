@echo off
echo Stopping Billar Lanzarote UI / watchers...
taskkill /FI "WINDOWTITLE eq BL_MasterControl*" /T /F
taskkill /FI "WINDOWTITLE eq BL_LiveWatcher*" /T /F
taskkill /FI "WINDOWTITLE eq BL_DBWriter*" /T /F
taskkill /FI "WINDOWTITLE eq BL_Gallery*" /T /F
taskkill /FI "WINDOWTITLE eq BL_Stats*" /T /F
taskkill /FI "WINDOWTITLE eq BL_H2H*" /T /F
echo Done.
pause
