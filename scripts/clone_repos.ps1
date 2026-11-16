Set-Location 'C:\AI-Job-Hunter\apps'

$repos = @(
    @{ name='jobspy'; url='https://github.com/speedyapply/JobSpy.git' },
    @{ name='jobnavigator'; url='https://github.com/vesaias/JobNavigator.git' },
    @{ name='jobops'; url='https://github.com/DaKheera47/job-ops.git' },
    @{ name='applypilot'; url='https://github.com/TheSahil/applypilot.git' },
    @{ name='resume-matcher'; url='https://github.com/srbhr/Resume-Matcher.git' }
)

foreach ($r in $repos) {
    Write-Output "=== Inspecting $($r.name) ==="
    $target = Join-Path (Get-Location) $r.name
    $items = Get-ChildItem -Path $target -Force -ErrorAction SilentlyContinue
    if (-not $items -or $items.Count -eq 0) {
        Remove-Item -Path $target -Force -Recurse -ErrorAction SilentlyContinue
        Write-Output "Cloning $($r.url) into $($r.name)..."
        git clone --depth 1 $r.url $r.name
    } else {
        Write-Output "$($r.name) has $($items.Count) items."
    }
}
