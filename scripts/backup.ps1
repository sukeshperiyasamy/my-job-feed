$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "C:\sukesh\job\backups\backup_$timestamp"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

Write-Output "Creating backup at $backupDir..."

# Backup SQLite Database
if (Test-Path "C:\sukesh\job\database\ai_job_hunter.db") {
    Copy-Item "C:\sukesh\job\database\ai_job_hunter.db" "$backupDir\" -Force
    Write-Output "[+] Database backed up."
}

# Backup Resumes & Generated PDFs
if (Test-Path "C:\sukesh\job\data") {
    Copy-Item "C:\sukesh\job\data" "$backupDir\data" -Recurse -Force
    Write-Output "[+] Data & documents backed up."
}

# Backup Config
if (Test-Path "C:\sukesh\job\config") {
    Copy-Item "C:\sukesh\job\config" "$backupDir\config" -Recurse -Force
    Write-Output "[+] Config backed up."
}

Write-Output "Backup completed successfully."
