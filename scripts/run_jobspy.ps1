param (
    [string]$SearchTerm = "Python Developer",
    [string]$Location = "India",
    [int]$Results = 5
)

Write-Output "Running JobSpy live job discovery: '$SearchTerm' in '$Location' ($Results results)..."
wsl -d Ubuntu-24.04 -u lokikende -e bash -c "/mnt/c/sukesh/job/.venv-linux/bin/python3 -c \"
import sys
sys.path.insert(0, '/mnt/c/sukesh/job')
from services.job_collector.collector import run_jobspy_discovery
jobs = run_jobspy_discovery(search_term='$SearchTerm', location='$Location', results_wanted=$Results)
print(f'Successfully discovered {len(jobs)} jobs.')
for j in jobs:
    print(f'- {j[\"title\"]} at {j[\"company_name\"]} ({j[\"canonical_url\"]})')
\""
