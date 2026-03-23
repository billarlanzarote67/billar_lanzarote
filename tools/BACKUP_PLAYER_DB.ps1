$Db = "C:\AI\BillarLanzarote\database\sqlite\billar_lanzarote.sqlite"
$Dir = "C:\AI\BillarLanzarote\database\sqlite"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Out = Join-Path $Dir ("billar_lanzarote_BACKUP_" + $Stamp + ".sqlite")
Copy-Item $Db $Out -Force
Write-Host "Backup created: $Out" -ForegroundColor Green
