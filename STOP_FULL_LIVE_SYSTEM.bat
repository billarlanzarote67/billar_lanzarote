@echo off
taskkill /FI "WINDOWTITLE eq BillarLanzarote Match Watcher*" /F
taskkill /FI "WINDOWTITLE eq BillarLanzarote Stream Controller*" /F
taskkill /FI "WINDOWTITLE eq BillarLanzarote Telegram Controller*" /F
taskkill /FI "WINDOWTITLE eq BillarLanzarote Overlay Server*" /F
taskkill /FI "WINDOWTITLE eq BillarLanzarote Control Panel*" /F
pause
