:: --- Billar Lanzarote Alerts Test ---
@echo off
echo ==============================
echo Billar Lanzarote Alert Test
echo ==============================

:: Navigate to scripts folder
cd /d C:\AI\BillarLanzarote\scripts

:: Activate virtual environment
echo Activating virtual environment...
call ..\venv\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate virtual environment. Check path.
    pause
    exit /b
)

:: Run Telegram test alert
echo Running Telegram test alert...
python test_telegram.py
if errorlevel 1 (
    echo Telegram test failed! Check token/chat ID and requirements.
) else (
    echo Telegram test alert sent successfully! ✅
)

:: Run Watchdog test alert
echo Running Watchdog test alert...
cd ..\billar_watchdog_telegram_alerts_pack_v1\services\watchdog
python send_test_alert_v1.py
if errorlevel 1 (
    echo Watchdog alert test failed! Check config.
) else (
    echo Watchdog test alert sent successfully! ✅
)

:: Return to scripts folder
cd /d C:\AI\BillarLanzarote\scripts

echo ==============================
echo All tests complete.
echo ==============================
pause
