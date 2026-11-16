# AI Job Hunter - Automated Background Startup Script
$logFile = "C:\sukesh\job\logs\autostart.log"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $logFile -Value "[$timestamp] System reboot/login detected. Initializing AI Job Hunter services..."

# 1. Start WSL2 Docker daemon
try {
    Add-Content -Path $logFile -Value "[$timestamp] Starting WSL2 Docker daemon..."
    wsl -d Ubuntu-24.04 -u root -e systemctl start docker
    Start-Sleep -Seconds 2
} catch {
    Add-Content -Path $logFile -Value "[$timestamp] Error starting Docker daemon: $_"
}

# 2. Start JobNavigator containers
try {
    Add-Content -Path $logFile -Value "[$timestamp] Bringing up JobNavigator containers..."
    wsl -d Ubuntu-24.04 -e bash -c "cd /mnt/c/sukesh/job/apps/jobnavigator && docker compose up -d"
} catch {
    Add-Content -Path $logFile -Value "[$timestamp] Error starting JobNavigator: $_"
}

# 3. Check and Start Unified Web Dashboard (Port 8000)
try {
    $running = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*services.integration_bridge.api:app*" }
    if (-not $running) {
        Add-Content -Path $logFile -Value "[$timestamp] Starting Unified Dashboard (FastAPI/Uvicorn on port 8000)..."
        Start-Process -FilePath "C:\sukesh\job\.venv\Scripts\python.exe" -ArgumentList "-m uvicorn services.integration_bridge.api:app --app-dir C:/sukesh/job --host 127.0.0.1 --port 8000" -WindowStyle Hidden
    } else {
        Add-Content -Path $logFile -Value "[$timestamp] Unified Dashboard already running (PID: $($running.ProcessId))."
    }
} catch {
    Add-Content -Path $logFile -Value "[$timestamp] Error starting Unified Dashboard: $_"
}

Add-Content -Path $logFile -Value "[$timestamp] Autostart sequence completed successfully. http://localhost:8000 and http://localhost:3000 are ready."
