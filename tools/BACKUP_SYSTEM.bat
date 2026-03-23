@echo off
set SRC=C:\AI\BillarLanzarote
set DEST=C:\AI\BACKUPS
if not exist %DEST% mkdir %DEST%
set DATESTAMP=%DATE:~6,4%-%DATE:~3,2%-%DATE:~0,2%_%TIME:~0,2%-%TIME:~3,2%
set DATESTAMP=%DATESTAMP: =0%
powershell -Command "Compress-Archive -Path '%SRC%' -DestinationPath '%DEST%\BillarLanzarote_%DATESTAMP%.zip' -Force"
echo Backup complete.
pause
