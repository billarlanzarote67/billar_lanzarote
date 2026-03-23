@echo off
setlocal enabledelayedexpansion
title Billar Lanzarote - INSTALL ALL v5

set ROOT=C:\AI\BillarLanzarote
set LOG=%ROOT%\logs\system\install_all_v5.log

mkdir "%ROOT%\logs\system" 2>nul
echo [%date% %time%] INSTALL_ALL_v5 started > "%LOG%"

for %%F in (
  "00_INSTALL_PACK_01_v5.bat"
  "00_INSTALL_PACK_02_INGEST_WATCHDOG.bat"
  "00_INSTALL_PACK_03_CUESCORE_CONTEXT.bat"
  "00_INSTALL_PACK_04_OVERLAY_STATE.bat"
  "00_INSTALL_PACK_05_AI_STATE_BASELINE_v5.bat"
  "00_INSTALL_PACK_06_v5.bat"
  "00_INSTALL_PACK_07_v5.bat"
  "00_INSTALL_PACK_08_v5.bat"
  "00_INSTALL_PACK_09_v5.bat"
  "00_INSTALL_PACK_10_v5.bat"
  "00_INSTALL_PACK_11_v5.bat"
  "00_INSTALL_PACK_12_v5.bat"
) do (
  if exist "%%~F" (
    echo Running %%~F
    echo [%date% %time%] Running %%~F >> "%LOG%"
    call "%%~F"
    if errorlevel 1 (
      echo [ERROR] %%~F failed. Stopping.
      echo [%date% %time%] ERROR %%~F failed >> "%LOG%"
      exit /b 1
    )
  ) else (
    echo [WARN] Missing installer %%~F
    echo [%date% %time%] WARN missing %%~F >> "%LOG%"
  )
)

echo [OK] INSTALL_ALL_v5 complete
echo [%date% %time%] INSTALL_ALL_v5 complete >> "%LOG%"
