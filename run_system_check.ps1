
$ErrorActionPreference = "Continue"

$TargetRoot = "C:\AI\BillarLanzarote"
$PythonPath = "C:\Program Files\Python312\python.exe"

function Out-Result($label, $ok, $details) {
    $state = if ($ok) { "OK" } else { "WARN" }
    Write-Host "[$state] $label - $details"
}

Out-Result "Root folder" (Test-Path $TargetRoot) $TargetRoot
Out-Result "Python 3.12" (Test-Path $PythonPath) $PythonPath
Out-Result "DB folder" (Test-Path "$TargetRoot\database\sqlite") "$TargetRoot\database\sqlite"
Out-Result "Player stats launcher" (Test-Path "$TargetRoot\launchers\START_PLAYER_STATS_DASHBOARD.bat") "$TargetRoot\launchers\START_PLAYER_STATS_DASHBOARD.bat"
Out-Result "CueScore importer launcher" (Test-Path "$TargetRoot\launchers\IMPORT_MATCH_URL.bat") "$TargetRoot\launchers\IMPORT_MATCH_URL.bat"
Out-Result "Tournament seeder launcher" (Test-Path "$TargetRoot\launchers\SEED_TOURNAMENT_77005630.bat") "$TargetRoot\launchers\SEED_TOURNAMENT_77005630.bat"
Out-Result "Photo cache folder" (Test-Path "$TargetRoot\data\players\photos") "$TargetRoot\data\players\photos"

try {
    $mtx = Get-Process mediamtx -ErrorAction SilentlyContinue
    Out-Result "MediaMTX process" ($null -ne $mtx) "mediamtx.exe"
} catch {
    Out-Result "MediaMTX process" $false "mediamtx.exe"
}

try {
    if (Test-Path $PythonPath) {
        & $PythonPath -c "import cv2, numpy, flask, requests, bs4; print('deps_ok')" | Out-Null
        Out-Result "Python deps" $true "cv2 numpy flask requests bs4"
    } else {
        Out-Result "Python deps" $false "Python missing"
    }
} catch {
    Out-Result "Python deps" $false "Import test failed"
}
