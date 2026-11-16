$base = 'C:\AI-Job-Hunter'
$dirs = @(
    'apps\jobnavigator',
    'apps\jobops',
    'apps\jobsync',
    'apps\resume-matcher',
    'apps\applypilot',
    'services\api-gateway',
    'services\job-collector',
    'services\job-normalizer',
    'services\resume-engine',
    'services\application-engine',
    'services\browser-manager',
    'services\notification-service',
    'services\integration-bridge',
    'dashboard',
    'browser-profiles',
    'data\resumes',
    'data\generated-pdfs',
    'data\cover-letters',
    'data\jobs',
    'data\applications',
    'data\exports',
    'database',
    'backups',
    'logs',
    'screenshots',
    'config',
    'docker',
    'scripts',
    'tests',
    'docs'
)

foreach ($d in $dirs) {
    $full = Join-Path $base $d
    if (-not (Test-Path $full)) {
        New-Item -ItemType Directory -Path $full -Force | Out-Null
    }
}

Write-Output "Created directories under $base successfully."
Get-ChildItem -Path $base | Select-Object Name
