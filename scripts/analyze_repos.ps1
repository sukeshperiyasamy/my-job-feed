$base = 'C:\AI-Job-Hunter\apps'
$apps = Get-ChildItem -Path $base -Directory

foreach ($app in $apps) {
    Write-Output "========================================"
    Write-Output "APP: $($app.Name)"
    Set-Location $app.FullName
    $commit = git rev-parse HEAD 2>$null
    $date = git log -1 --format=%cd 2>$null
    $subject = git log -1 --format=%s 2>$null
    Write-Output "Commit: $commit ($date)"
    Write-Output "Latest message: $subject"
    $files = Get-ChildItem -Path $app.FullName | Select-Object -ExpandProperty Name
    Write-Output "Root files: $($files -join ', ')"
}
