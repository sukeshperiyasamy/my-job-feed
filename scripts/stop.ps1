Write-Output "Stopping AI Job Hunter Services..."

# 1. Stop Dashboard / Uvicorn processes
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*services.integration_bridge.api:app*" } | ForEach-Object {
    Write-Output "Terminating Dashboard process ID: $($_.ProcessId)"
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}

# 2. Stop Docker Compose containers if any
wsl -d Ubuntu-24.04 -e bash -c "cd /mnt/c/sukesh/job/apps/jobnavigator 2>/dev/null && docker compose down 2>/dev/null || true"

Write-Output "All AI Job Hunter services stopped safely."
