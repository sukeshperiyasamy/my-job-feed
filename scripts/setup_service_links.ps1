$services = @('browser-manager', 'job-collector', 'job-normalizer', 'resume-engine', 'application-engine', 'notification-service', 'integration-bridge', 'api-gateway')
foreach ($s in $services) {
    $underscore = $s.Replace('-', '_')
    $source = Join-Path 'C:\sukesh\job\services' $s
    $target = Join-Path 'C:\sukesh\job\services' $underscore
    if (-not (Test-Path $target)) {
        cmd /c mklink /J "$target" "$source"
    }
}
Get-ChildItem 'C:\sukesh\job\services' | Select-Object Name
