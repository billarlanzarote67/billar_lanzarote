$target = "C:\AI\BillarLanzarote\scripts\START_MASTER_SYSTEM_CANONICAL_v1.bat"
$working = "C:\AI\BillarLanzarote\scripts"
$desktop = [Environment]::GetFolderPath("Desktop")
$link = Join-Path $desktop "Billar Lanzarote Master System.lnk"
$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($link)
$shortcut.TargetPath = $target
$shortcut.WorkingDirectory = $working
$shortcut.WindowStyle = 1
$shortcut.IconLocation = "C:\Windows\System32\shell32.dll,220"
$shortcut.Save()
Write-Host "Shortcut created: $link"
