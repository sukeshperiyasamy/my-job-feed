import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, "C:/sukesh/job")

from services.integration_bridge.models import Base, Resume
from services.resume_engine.engine import VerifiedFactsStore

DATABASE_PATH = "C:/sukesh/job/database/ai_job_hunter.db"
engine = create_engine(f"sqlite:///{DATABASE_PATH}")
Session = sessionmaker(bind=engine)
db = Session()

try:
    facts = VerifiedFactsStore()
    existing = db.query(Resume).filter(Resume.id == 1).first()
    if existing:
        existing.display_name = facts.full_name
        existing.original_filename = "Sukesh_Periyasamy_Resume.pdf"
        existing.file_path = "C:/sukesh/job/data/resumes/Sukesh_Periyasamy_Resume.pdf"
        existing.file_type = "pdf"
        existing.version = "2026.1"
        existing.skills_json = facts.skills
        existing.experience_summary = facts.summary
        print(f"[+] Updated Resume ID 1 for {facts.full_name}")
    else:
        new_resume = Resume(
            id=1,
            display_name=facts.full_name,
            original_filename="Sukesh_Periyasamy_Resume.pdf",
            file_path="C:/sukesh/job/data/resumes/Sukesh_Periyasamy_Resume.pdf",
            file_type="pdf",
            version="2026.1",
            skills_json=facts.skills,
            experience_summary=facts.summary,
            is_active=True
        )
        db.add(new_resume)
        print(f"[+] Created Resume record for {facts.full_name}")

    db.commit()
finally:
    db.close()
