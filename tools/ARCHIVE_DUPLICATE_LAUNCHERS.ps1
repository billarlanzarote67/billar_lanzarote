
$Root = "C:\AI\BillarLanzarote\launchers"
$Archive = "C:\AI\BillarLanzarote\ARCHIVE_OLD\launchers_" + (Get-Date -Format "yyyyMMdd_HHmmss")
New-Item -ItemType Directory -Force -Path $Archive | Out-Null

Get-ChildItem $Root -File | Where-Object {
    $_.BaseName -match "\(1\)|\(2\)|COPY|OLD|BACKUP"
} | ForEach-Object {
    Move-Item $_.FullName (Join-Path $Archive $_.Name) -Force
    Write-Host "Archived $($_.Name)" -ForegroundColor Yellow
}

Write-Host "Archive folder: $Archive" -ForegroundColor Green
