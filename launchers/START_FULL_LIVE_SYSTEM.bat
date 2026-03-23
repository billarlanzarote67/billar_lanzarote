@echo off
set ROOT=C:\AI\BillarLanzarote
set PY="C:\Program Files\Python312\python.exe"
start "BillarLanzarote Match Watcher" cmd /k %PY% %ROOT%\automation\match_watcher_v1.py
start "BillarLanzarote Stream Controller" cmd /k %PY% %ROOT%\automation\stream_controller_v1.py
start "BillarLanzarote Telegram Controller" cmd /k %PY% %ROOT%\automation\telegram_controller_v1.py
start "BillarLanzarote Overlay Server" cmd /k %PY% %ROOT%\overlay\overlay_server.py
start "BillarLanzarote Control Panel" cmd /k %PY% %ROOT%\dashboard\control_panel\app.py
start http://127.0.0.1:8788
