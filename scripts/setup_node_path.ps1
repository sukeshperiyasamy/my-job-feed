$nodeExe = Get-ChildItem -Path "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\OpenJS.NodeJS.LTS_Microsoft.Winget.Source_8wekyb3d8bbwe" -Recurse -Filter "node.exe" | Select-Object -First 1
if ($nodeExe) {
    $nodeDir = $nodeExe.DirectoryName
    $currentPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    if ($currentPath -notlike "*$nodeDir*") {
        [Environment]::SetEnvironmentVariable('Path', "$nodeDir;$currentPath", 'User')
    }
    Write-Output "Node Path: $nodeDir"
    & "$nodeDir\node.exe" -v
    & "$nodeDir\npm.cmd" -v
} else {
    Write-Error "node.exe not found"
}
