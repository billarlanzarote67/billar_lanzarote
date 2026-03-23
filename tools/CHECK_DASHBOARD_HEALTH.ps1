
$ErrorActionPreference = "Continue"
$Db = "C:\AI\BillarLanzarote\database\sqlite\billar_lanzarote.sqlite"
$Py = "C:\Program Files\Python312\python.exe"

Write-Host "DB exists: $([bool](Test-Path $Db))"
Write-Host "Python exists: $([bool](Test-Path $Py))"

if (Test-Path $Db -and Test-Path $Py) {
    & $Py -c "import sqlite3; db=r'C:\AI\BillarLanzarote\database\sqlite\billar_lanzarote.sqlite'; con=sqlite3.connect(db); cur=con.cursor(); cur.execute('SELECT COUNT(*) FROM players'); print('players =', cur.fetchone()[0]); con.close()"
}

Write-Host ""
Write-Host "Expected URLs:" -ForegroundColor Yellow
Write-Host "AI dashboard:      http://127.0.0.1:8787"
Write-Host "Player stats:      http://127.0.0.1:8099"
Write-Host "Player H2H:        http://127.0.0.1:8791"
