
$ErrorActionPreference = "Continue"

$PackRoot = Split-Path -Parent $PSScriptRoot
$TargetRoot = "C:\AI\BillarLanzarote"
$PythonPath = "C:\Program Files\Python312\python.exe"
$CoreDir = Join-Path $PackRoot "packages\core"
$TempRoot = Join-Path $env:TEMP "BillarLanzarote_Pack5_Extract"
$Releases = @(
    "BillarLanzarote_FULL_SYSTEM_v1.zip",
    "BillarLanzarote_CueScore_Importer_v1.zip",
    "BillarLanzarote_Player_Stats_Dashboard_v1.zip",
    "BillarLanzarote_Stats_System_Upgrade_v2.zip"
)

function Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Good($msg) { Write-Host "[OK]   $msg" -ForegroundColor Green }

Info "Starting Pack 5 core stack install"
Info "Target root: $TargetRoot"

New-Item -ItemType Directory -Force -Path "$PackRoot\install_logs" | Out-Null
New-Item -ItemType Directory -Force -Path $TargetRoot | Out-Null
New-Item -ItemType Directory -Force -Path $TempRoot | Out-Null

$folders = @(
    "$TargetRoot\config",
    "$TargetRoot\calibration",
    "$TargetRoot\state",
    "$TargetRoot\data\events\mesa1",
    "$TargetRoot\data\events\mesa2",
    "$TargetRoot\data\clips\mesa1",
    "$TargetRoot\data\clips\mesa2",
    "$TargetRoot\data\players\photos",
    "$TargetRoot\data\raw_cuescore\matches",
    "$TargetRoot\data\raw_cuescore\profiles",
    "$TargetRoot\data\raw_cuescore\screenshots\matches",
    "$TargetRoot\data\raw_cuescore\screenshots\profiles",
    "$TargetRoot\data\raw_cuescore\review",
    "$TargetRoot\database\sqlite",
    "$TargetRoot\launchers",
    "$TargetRoot\scripts",
    "$TargetRoot\sql",
    "$TargetRoot\logs"
)
foreach ($f in $folders) { New-Item -ItemType Directory -Force -Path $f | Out-Null }

if (Test-Path $PythonPath) {
    Good "Python 3.12 found"
    & $PythonPath -m pip install --upgrade pip
    & $PythonPath -m pip install opencv-python numpy flask requests beautifulsoup4 playwright
    try {
        & $PythonPath -m playwright install
    } catch {
        Warn "Playwright browser install skipped/failed"
    }
    & $PythonPath -c "import cv2, numpy, flask, requests, bs4; print('Python deps OK')"
} else {
    Warn "Python 3.12 not found at $PythonPath"
}

foreach ($zipName in $Releases) {
    $zipPath = Join-Path $CoreDir $zipName
    if (-not (Test-Path $zipPath)) {
        Warn "Missing package: $zipPath"
        continue
    }

    $tempExtract = Join-Path $TempRoot ([System.IO.Path]::GetFileNameWithoutExtension($zipName))
    if (Test-Path $tempExtract) { Remove-Item -Recurse -Force $tempExtract }
    New-Item -ItemType Directory -Force -Path $tempExtract | Out-Null

    Info "Extracting $zipName"
    Expand-Archive -LiteralPath $zipPath -DestinationPath $tempExtract -Force

    Info "Copying files from $zipName"
    robocopy $tempExtract $TargetRoot /E /NFL /NDL /NJH /NJS /NC /NS | Out-Null
}

$launcherFixes = @{
    "$TargetRoot\launchers\START_MESA1_AI.bat" = "@echo off`r`ncd /d C:\AI\BillarLanzarote`r`n`"C:\Program Files\Python312\python.exe`" core\ai_engine\vision_core.py C:\AI\BillarLanzarote\config\mesa1_config.json`r`npause`r`n"
    "$TargetRoot\launchers\START_MESA2_AI.bat" = "@echo off`r`ncd /d C:\AI\BillarLanzarote`r`n`"C:\Program Files\Python312\python.exe`" core\ai_engine\vision_core.py C:\AI\BillarLanzarote\config\mesa2_config.json`r`npause`r`n"
    "$TargetRoot\launchers\START_DASHBOARD.bat" = "@echo off`r`ncd /d C:\AI\BillarLanzarote\dashboard\web_ui`r`n`"C:\Program Files\Python312\python.exe`" app.py`r`npause`r`n"
    "$TargetRoot\launchers\IMPORT_MATCH_URL.bat" = "@echo off`r`nset /p URL=Paste CueScore finished match URL: `r`ncd /d C:\AI\BillarLanzarote\scripts`r`n`"C:\Program Files\Python312\python.exe`" import_finished_match.py `"%URL%`"`r`npause`r`n"
    "$TargetRoot\launchers\IMPORT_PLAYER_PROFILE_URL.bat" = "@echo off`r`nset /p URL=Paste CueScore player profile URL: `r`ncd /d C:\AI\BillarLanzarote\scripts`r`n`"C:\Program Files\Python312\python.exe`" import_player_profile.py `"%URL%`"`r`npause`r`n"
    "$TargetRoot\launchers\START_PLAYER_STATS_DASHBOARD.bat" = "@echo off`r`ncd /d C:\AI\BillarLanzarote\scripts`r`n`"C:\Program Files\Python312\python.exe`" player_stats_dashboard.py`r`npause`r`n"
    "$TargetRoot\launchers\START_CUESCORE_AUTO_IMPORT_WATCHER.bat" = "@echo off`r`ncd /d C:\AI\BillarLanzarote\scripts`r`n`"C:\Program Files\Python312\python.exe`" auto_import_watcher.py`r`npause`r`n"
    "$TargetRoot\launchers\SEED_TOURNAMENT_77005630.bat" = "@echo off`r`ncd /d C:\AI\BillarLanzarote\scripts`r`n`"C:\Program Files\Python312\python.exe`" seed_tournament_players.py`r`npause`r`n"
    "$TargetRoot\launchers\SUGGEST_ALIASES.bat" = "@echo off`r`ncd /d C:\AI\BillarLanzarote\scripts`r`n`"C:\Program Files\Python312\python.exe`" suggest_aliases.py`r`npause`r`n"
}
foreach ($pair in $launcherFixes.GetEnumerator()) {
    Set-Content -Path $pair.Key -Value $pair.Value -Encoding UTF8
}

$Seeder = "$TargetRoot\scripts\seed_tournament_players.py"
if ((Test-Path $PythonPath) -and (Test-Path $Seeder)) {
    Info "Running tournament seeder 77005630"
    try {
        & $PythonPath $Seeder
        Good "Tournament seeding executed"
    } catch {
        Warn "Tournament seeding failed; rerun later with launcher"
    }
} else {
    Warn "Tournament seeder not run automatically"
}

Good "Pack 5 core install complete"
Write-Host ""
Write-Host "NEXT" -ForegroundColor Magenta
Write-Host "1. RUN_SYSTEM_CHECK.bat"
Write-Host "2. Start MediaMTX if needed"
Write-Host "3. Start player stats dashboard"
Write-Host "4. Manual import remains available"
Write-Host "5. Leave later_optional alone for now"
