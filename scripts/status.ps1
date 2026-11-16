Write-Output "=================================================="
Write-Output "   AI JOB HUNTER & APPLICATION PLATFORM STATUS    "
Write-Output "=================================================="

# Check Unified Dashboard API
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 3 -ErrorAction Stop
    Write-Output "[+] Unified Web Dashboard (:8000): HEALTHY (Status: $($health.status))"
} catch {
    Write-Output "[-] Unified Web Dashboard (:8000): OFFLINE or UNREACHABLE"
}

# Check Local AI Engine
try {
    $models = Invoke-RestMethod -Uri "http://127.0.0.1:1234/v1/models" -TimeoutSec 3 -ErrorAction Stop
    $modelCount = $models.data.Count
    Write-Output "[+] Local AI Engine LM Studio (:1234): ONLINE ($modelCount models loaded)"
} catch {
    Write-Output "[-] Local AI Engine LM Studio (:1234): OFFLINE"
}

# Check Docker in WSL2
try {
    $dockerPs = wsl -d Ubuntu-24.04 -e docker ps --format "{{.Names}}: {{.Status}}"
    Write-Output "[+] Docker Engine (WSL2): RUNNING"
    if ($dockerPs) {
        Write-Output "    Active Containers:"
        $dockerPs | ForEach-Object { Write-Output "    - $_" }
    } else {
        Write-Output "    No containers currently active."
    }
} catch {
    Write-Output "[-] Docker Engine (WSL2): OFFLINE"
}

# Check Database
$dbFile = "C:\sukesh\job\database\ai_job_hunter.db"
if (Test-Path $dbFile) {
    $size = (Get-Item $dbFile).Length / 1KB
    Write-Output "[+] SQLite Integration Database: PRESENT ($([math]::Round($size, 1)) KB)"
} else {
    Write-Output "[-] SQLite Integration Database: NOT FOUND"
}

Write-Output "=================================================="
