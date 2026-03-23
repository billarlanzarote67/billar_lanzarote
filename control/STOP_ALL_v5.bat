@echo off
setlocal
title Billar Lanzarote - STOP ALL v5

set ROOT=C:\AI\BillarLanzarote

for %%F in (
  "%ROOT%\launchers\STOP_WATCHDOG.bat"
  "%ROOT%\launchers\STOP_CUESCORE_CONTEXT.bat"
  "%ROOT%\launchers\STOP_OVERLAY_STATE.bat"
  "%ROOT%\launchers\STOP_AI_STATE_BASELINE_v5.bat"
  "%ROOT%\launchers\STOP_PACK_06_v5.bat"
  "%ROOT%\launchers\STOP_PACK_07_v5.bat"
  "%ROOT%\launchers\STOP_PACK_08_v5.bat"
  "%ROOT%\launchers\STOP_PACK_09_v5.bat"
  "%ROOT%\launchers\STOP_PACK_10_v5.bat"
  "%ROOT%\launchers\STOP_PACK_11_v5.bat"
  "%ROOT%\launchers\STOP_PACK_12_v5.bat"
) do (
  if exist %%F call %%F
)

taskkill /FI "WINDOWTITLE eq Dashboard v5" /T /F >nul 2>nul
echo [OK] STOP_ALL_v5 stop signals sent
