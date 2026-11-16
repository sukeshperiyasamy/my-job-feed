$moreRepos = @(
    @{ name='jobsync'; url='https://github.com/Gsync/jobsync.git' },
    @{ name='job-forager'; url='https://github.com/nipunsomani/job-forager.git' },
    @{ name='openapply'; url='https://github.com/nturl/openapply.git' },
    @{ name='jobpilot'; url='https://github.com/suxrobGM/jobpilot.git' },
    @{ name='autoapply'; url='https://github.com/AbhishekMandapmalvi/AutoApply.git' }
)

foreach ($r in $moreRepos) {
    Write-Output "Checking $($r.name) at $($r.url)..."
    git ls-remote --heads $r.url 2>$null | Select-Object -First 2
}
