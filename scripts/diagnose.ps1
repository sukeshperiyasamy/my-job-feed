Write-Output "=== SYSTEM DIAGNOSTIC TRACE ==="
Write-Output "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Output "Project Location: C:\sukesh\job"

Write-Output "`n[1] Hardware & Environment:"
Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, BuildNumber | Format-List
Get-PSDrive -Name C | Select-Object Root, @{N='Free_GB';E={[math]::Round($_.Free/1GB, 2)}} | Format-Table

Write-Output "`n[2] Developer Runtimes:"
Write-Output "Python: $(& 'C:\sukesh\job\.venv\Scripts\python.exe' --version 2>&1)"
Write-Output "Node: $(node -v 2>&1)"
Write-Output "Git: $(git --version 2>&1)"
Write-Output "WSL2 Ubuntu: $(wsl -d Ubuntu-24.04 -e uname -r 2>&1)"
Write-Output "Docker Engine: $(wsl -d Ubuntu-24.04 -e docker --version 2>&1)"

Write-Output "`n[3] Service Connectivity:"
try {
    $res = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 2
    Write-Output "Dashboard API (:8000): HEALTHY"
} catch {
    Write-Output "Dashboard API (:8000): DOWN"
}

try {
    $res = Invoke-RestMethod -Uri "http://127.0.0.1:1234/v1/models" -TimeoutSec 2
    Write-Output "LM Studio API (:1234): ONLINE"
} catch {
    Write-Output "LM Studio API (:1234): DOWN"
}

Write-Output "`n[4] Database Records:"
try {
    $overview = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/overview" -TimeoutSec 2
    Write-Output "Total Discovered Jobs: $($overview.total_jobs_discovered)"
    Write-Output "Matched Jobs: $($overview.jobs_matched)"
    Write-Output "Pending Approvals: $($overview.pending_approvals)"
    Write-Output "Submitted: $($overview.applications_submitted)"
} catch {
    Write-Output "Could not fetch database stats."
}

Write-Output "`nDiagnostic complete."
