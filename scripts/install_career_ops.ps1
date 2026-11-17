$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskRepo = Join-Path $taskRoot 'apps/career-ops'
$taskConfig = Get-Content -LiteralPath (Join-Path $taskRoot 'config/career-ops.json') -Raw | ConvertFrom-Json
if (-not (Test-Path -LiteralPath (Join-Path $taskRepo '.git'))) {
    git clone --no-checkout $taskConfig.repository $taskRepo
    if ($LASTEXITCODE -ne 0) { throw 'Career Ops clone failed.' }
    git -C $taskRepo fetch --depth 1 origin $taskConfig.commit
    if ($LASTEXITCODE -ne 0) { throw 'Cannot fetch the pinned revision.' }
    git -C $taskRepo checkout --detach $taskConfig.commit
    if ($LASTEXITCODE -ne 0) { throw 'Cannot check out the pinned revision.' }
}
$taskHead = git -C $taskRepo rev-parse HEAD
if ($taskHead -ne $taskConfig.commit) { throw 'Existing checkout differs from the tested revision. Keep it separate; no existing files were overwritten.' }
Copy-Item -LiteralPath (Join-Path $taskRoot 'integrations/career-ops/package-lock.json') -Destination (Join-Path $taskRepo 'package-lock.json')
Push-Location $taskRepo
try {
    npm ci --ignore-scripts --omit=dev --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) { throw 'Career Ops dependencies could not be installed.' }
} finally { Pop-Location }
Write-Output 'Career Ops read-only adapter installed. No personal profile, account or application data was copied.'
