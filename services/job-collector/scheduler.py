import time
import requests
from datetime import datetime, timezone

API_BASE = "http://127.0.0.1:8000"

def run_scheduled_cycle():
    print(f"[*] [{datetime.now(timezone.utc).isoformat()}] Starting scheduled job hunter cycle...")
    
    # 1. Check health
    try:
        r = requests.get(f"{API_BASE}/health", timeout=5)
        if r.status_code != 200:
            print("[!] API health check failed.")
            return
    except Exception as e:
        print(f"[!] Cannot reach API: {e}")
        return

    # 2. Add sample newly discovered jobs (or invoke JobSpy)
    sample_jobs = [
        {
            "source": "indeed",
            "canonical_url": f"https://www.indeed.com/viewjob?jk=sample_{int(time.time())}",
            "title": "Lead Python Engineer",
            "company_name": "NextGen FinTech",
            "location": "Hyderabad, India",
            "work_arrangement": "Hybrid",
            "description": "Looking for Lead Python Engineer with experience in FastAPI, Docker, and Playwright."
        }
    ]

    for job in sample_jobs:
        resp = requests.post(f"{API_BASE}/api/jobs", json=job)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "created":
                job_id = data["job_id"]
                print(f"[+] Discovered new job #{job_id}: {job['title']} at {job['company_name']}")
                
                # 3. Trigger AI Scoring & Tailoring
                score_resp = requests.post(f"{API_BASE}/api/jobs/{job_id}/score")
                if score_resp.status_code == 200:
                    s_data = score_resp.json()
                    print(f"[+] Scored job #{job_id}: {s_data['match_score']}% match. PDF ready at {s_data['pdf_url']}")

    print("[*] Scheduled cycle finished. Next run according to configured schedule.")

if __name__ == "__main__":
    run_scheduled_cycle()
