import sys
from pathlib import Path

# Add project root dynamically (works on both Windows and WSL Linux)
root_dir = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, root_dir)

from services.job_collector.collector import run_jobspy_discovery

def test_discovery():
    print("[*] Running JobSpy live discovery verification...")
    # Scrape jobs from Indeed
    jobs = run_jobspy_discovery(
        search_term="Python Developer",
        location="India",
        sites=["indeed"],
        results_wanted=3,
        hours_old=72,
        country_indeed="India"
    )
    print(f"[+] Total jobs retrieved: {len(jobs)}")
    if jobs:
        sample = jobs[0]
        print(f"[+] Sample Job Title: {sample['title']}")
        print(f"[+] Sample Company: {sample['company_name']}")
        print(f"[+] Canonical URL: {sample['canonical_url']}")
        assert "canonical_url" in sample
        assert "title" in sample
        print("[+] JobSpy test passed successfully!")
    else:
        print("[!] Scraper executed cleanly.")

if __name__ == "__main__":
    test_discovery()
