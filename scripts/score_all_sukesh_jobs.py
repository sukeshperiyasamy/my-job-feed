import sys
import requests

API_BASE = "http://127.0.0.1:8000"

print("[*] Fetching all newly discovered jobs for Sukesh...")
jobs = requests.get(f"{API_BASE}/api/jobs").json()

for j in jobs:
    if j.get("status") == "Discovered":
        job_id = j["id"]
        title = j["title"]
        company = j["company_name"]
        print(f"\n[*] Scoring Job #{job_id}: {title} at {company} via Antigravity CLI...")
        try:
            res = requests.post(f"{API_BASE}/api/jobs/{job_id}/score", timeout=45).json()
            print(f"[+] Match Score: {res.get('match_score')}%")
            print(f"[+] Reason: {res.get('match_reason')}")
            print(f"[+] Tailored PDF: {res.get('pdf_url')}")
        except Exception as e:
            print(f"[!] Error scoring job #{job_id}: {e}")

print("\n[*] Batch scoring complete! Check http://localhost:8000 to review.")
