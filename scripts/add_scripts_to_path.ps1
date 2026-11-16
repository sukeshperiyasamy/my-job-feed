$dir = "C:\AI-Job-Hunter\scripts"
$currentPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if ($currentPath -notlike "*$dir*") {
    [Environment]::SetEnvironmentVariable('Path', "$dir;$currentPath", 'User')
}
Write-Output "Scripts dir added to User PATH: $dir"
