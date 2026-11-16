import sys
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root dynamically
root_dir = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, root_dir)

from services.job_collector.collector import run_jobspy_discovery
from services.integration_bridge.models import Base, Job, ApplicationState

DATABASE_PATH = "C:/sukesh/job/database/ai_job_hunter.db"
# If running in WSL, convert path
if Path("/mnt/c/sukesh/job").exists():
    DATABASE_PATH = "/mnt/c/sukesh/job/database/ai_job_hunter.db"

engine = create_engine(f"sqlite:///{DATABASE_PATH}")
Session = sessionmaker(bind=engine)
db = Session()

searches = [
    {"term": "AI Engineer", "loc": "Bengaluru", "count": 3},
    {"term": "React Native Developer", "loc": "Bengaluru", "count": 3},
    {"term": "Biomedical Engineer", "loc": "India", "count": 3}
]

total_added = 0

try:
    for s in searches:
        print(f"\n[*] Discovering '{s['term']}' in '{s['loc']}'...")
        jobs = run_jobspy_discovery(
            search_term=s['term'],
            location=s['loc'],
            sites=["indeed"],
            results_wanted=s['count'],
            hours_old=120,
            country_indeed="India"
        )
        for j in jobs:
            existing = db.query(Job).filter(Job.canonical_url == j["canonical_url"]).first()
            if not existing:
                new_job = Job(
                    source=j["source"],
                    source_job_id=j.get("source_job_id"),
                    canonical_url=j["canonical_url"],
                    title=j["title"],
                    company_name=j["company_name"],
                    location=j["location"],
                    work_arrangement=j.get("work_arrangement", "Full-time"),
                    salary_min=j.get("salary_min"),
                    salary_max=j.get("salary_max"),
                    salary_currency=j.get("salary_currency", "INR"),
                    description=j.get("description", ""),
                    posting_date=j.get("posting_date", datetime.now(timezone.utc)),
                    discovery_date=datetime.now(timezone.utc),
                    status=ApplicationState.DISCOVERED
                )
                db.add(new_job)
                total_added += 1
                print(f"[+] Added to Database: {j['title']} at {j['company_name']}")

    db.commit()
    print(f"\n[+] Total newly discovered jobs added to database: {total_added}")
finally:
    db.close()
