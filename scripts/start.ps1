Write-Output "Starting AI Job Hunter Services..."

# 1. Start Docker Daemon in WSL2
wsl -d Ubuntu-24.04 -u root -e systemctl start docker

# 2. Check if Unified Dashboard is already running
$running = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*services.integration_bridge.api:app*" }
if (-not $running) {
    Write-Output "Launching Unified Web Dashboard on http://127.0.0.1:8000..."
    Start-Process -FilePath "C:\sukesh\job\.venv\Scripts\python.exe" -ArgumentList "-m uvicorn services.integration_bridge.api:app --app-dir C:/sukesh/job --host 127.0.0.1 --port 8000" -WindowStyle Hidden
} else {
    Write-Output "Unified Web Dashboard is already running."
}

# 3. Check Status
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\sukesh\job\scripts\status.ps1"
