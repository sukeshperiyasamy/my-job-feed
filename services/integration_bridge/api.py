import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, field_validator
from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, "C:/sukesh/job")

from services.integration_bridge.models import (
    Base, Job, Resume, GeneratedDocument, Application,
    ApplicationAttempt, ApplicationState, ApplicationMode,
    JobSource, ExecutionLog, JobVerification
)
from services.resume_engine.engine import VerifiedFactsStore, match_job_with_llm, generate_ats_pdf
from services.resume_engine.template_builder import generate_resume_filename
from services.application_engine.engine import ApplicationEngine
from services.integration_bridge.operations import create_operations
from services.job_collector.careers import canonical_url
from services.job_collector.matching import assess_job,campaign_config
from services.integration_bridge.opportunities import catalog_router
from services.integration_bridge.connections import create_connections_router
from services.integration_bridge.application_profile import profile_router
from services.integration_bridge.freelancing import freelance_router

DATABASE_PATH = os.environ.get("JOB_HUNTER_DATABASE", "C:/sukesh/job/database/ai_job_hunter.db")
Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Job Hunter Integration Bridge & Gateway",
    version="1.0.0",
    description="Central coordination API for jobs, resume generation, browser automation, and approval queue."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def require_local_browser_origin(request, call_next):
    origin = request.headers.get("origin")
    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and origin and origin not in {"http://127.0.0.1:8000", "http://localhost:8000"}:
        return JSONResponse(status_code=403, content={"detail": "Application actions must originate from the local dashboard."})
    return await call_next(request)

# Mount screenshots and generated documents for dashboard preview
screenshots_dir = Path("C:/sukesh/job/screenshots")
screenshots_dir.mkdir(parents=True, exist_ok=True)
app.mount("/screenshots", StaticFiles(directory=str(screenshots_dir)), name="screenshots")

pdf_dir = Path("C:/sukesh/job/data/generated-pdfs")
pdf_dir.mkdir(parents=True, exist_ok=True)
app.mount("/pdfs", StaticFiles(directory=str(pdf_dir)), name="pdfs")

resumes_dir = Path("C:/sukesh/job/data/resumes")
resumes_dir.mkdir(parents=True, exist_ok=True)
app.mount("/resumes", StaticFiles(directory=str(resumes_dir)), name="resumes")

app.mount("/dashboard-assets", StaticFiles(directory="C:/sukesh/job/dashboard/assets"), name="dashboard-assets")

@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    dashboard_file = Path("C:/sukesh/job/dashboard/index.html")
    if dashboard_file.exists():
        return dashboard_file.read_text(encoding="utf-8")
    return "<h1>Unified Dashboard Ready</h1>"

# Pydantic Schemas
class JobCreateSchema(BaseModel):
    source: str
    canonical_url: str
    title: str
    company_name: str
    location: Optional[str] = "India"
    work_arrangement: Optional[str] = "Full-time"
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = "INR"
    description: Optional[str] = ""

    @field_validator("canonical_url")
    @classmethod
    def valid_url(cls, value):
        return canonical_url(value)

class ResumeCreateSchema(BaseModel):
    display_name: str
    full_name: str
    email: str
    phone: str
    location: str
    skills: List[str]
    summary: str

class ApprovalDecisionSchema(BaseModel):
    application_id: int
    decision: str  # "approve" or "reject" or "skip"

operations_router, application_sessions = create_operations(SessionLocal)
app.include_router(operations_router)
app.include_router(catalog_router(SessionLocal))
app.include_router(freelance_router(SessionLocal))
app.include_router(create_connections_router())
app.include_router(profile_router(application_sessions))

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": "sqlite_active",
        "project_root": "C:\\sukesh\\job"
    }

@app.get("/api/overview")
def get_dashboard_overview():
    db = SessionLocal()
    try:
        total_jobs = db.query(Job).count()
        matched_jobs = db.query(Job).filter(Job.match_score.isnot(None)).count()
        documents_generated = db.query(GeneratedDocument).count()
        pending_approvals = db.query(Application).filter(Application.state == ApplicationState.PENDING_APPROVAL).count()
        submitted = db.query(Application).filter(Application.state == ApplicationState.SUBMITTED).count()
        failed = db.query(Application).filter(Application.state == ApplicationState.FAILED).count()

        return {
            "total_jobs_discovered": total_jobs,
            "jobs_matched": matched_jobs,
            "documents_generated": documents_generated,
            "pending_approvals": pending_approvals,
            "applications_submitted": submitted,
            "failed_applications": failed,
            "system_health": "Operational",
            "active_workers": int(application_sessions.active is not None),
            "ai_engine": "Codex CLI → Antigravity CLI → LM Studio → deterministic fallback (configured order)",
            "browser_engine": "Playwright with persistent project Edge/Chrome profile"
        }
    finally:
        db.close()

@app.get("/api/jobs")
def list_jobs(status: Optional[str] = None, limit: int = Query(50, ge=1, le=1000), eligibility: Optional[str] = None, campaign: Optional[str] = None):
    db = SessionLocal()
    try:
        q = db.query(Job)
        if status:
            q = q.filter(Job.status == status)
        jobs = q.order_by(Job.discovery_date.desc()).limit(limit).all()
        results = []
        screening_config=campaign_config()
        verifications={v.job_id:v for v in db.query(JobVerification).filter(JobVerification.job_id.in_([j.id for j in jobs])).all()}
        for j in jobs:
            screening=assess_job(j.title,j.description,j.location,screening_config)
            if eligibility and screening['status']!=eligibility:continue
            if campaign and campaign not in [c['id'] for c in screening['campaigns']]:continue
            clean_name = generate_resume_filename("Sukesh Periyasamy", j.title, j.company_name, "pdf")
            pdf_disk_path = Path(f"C:/sukesh/job/data/generated-pdfs/{clean_name}")
            compat_disk_path = Path(f"C:/sukesh/job/data/generated-pdfs/job_{j.id}_tailored.pdf")
            has_pdf = pdf_disk_path.exists() or compat_disk_path.exists()
            actual_filename = clean_name if pdf_disk_path.exists() else f"job_{j.id}_tailored.pdf"

            results.append({
                "id": j.id,
                "source": j.source,
                "canonical_url": j.canonical_url,
                "title": j.title,
                "company_name": j.company_name,
                "location": j.location,
                "work_arrangement": j.work_arrangement,
                "description": j.description,
                "discovery_date": j.discovery_date.isoformat() if j.discovery_date else None,
                "posting_date": j.posting_date.isoformat() if j.posting_date else None,
                "salary_min": j.salary_min, "salary_max": j.salary_max, "salary_currency": j.salary_currency,
                "match_score": j.match_score,
                "match_reason": j.match_reason,
                "screening": screening,
                "availability": {'status':verifications[j.id].availability,'checked_at':verifications[j.id].checked_at.isoformat() if verifications[j.id].checked_at else None,'reason':verifications[j.id].reason} if j.id in verifications else {'status':'unchecked'},
                "source_attribution": {'name':verifications[j.id].source_name,'url':verifications[j.id].source_url,'provider':verifications[j.id].provider} if j.id in verifications and verifications[j.id].source_name else None,
                "discovery_evidence": (verifications[j.id].details or {}).get('freehire') if j.id in verifications else None,
                "status": j.status.value if hasattr(j.status, 'value') else str(j.status),
                "pdf_filename": actual_filename if has_pdf else None,
                "cover_letter_url": f"/pdfs/{Path(actual_filename).with_suffix(chr(46)+"txt").name}" if has_pdf and Path(f"C:/sukesh/job/data/generated-pdfs/{actual_filename}").with_suffix(".txt").exists() else None,
                "pdf_url": f"/pdfs/{actual_filename}" if has_pdf else None
            })
        return results
    finally:
        db.close()

@app.post("/api/jobs")
def create_or_update_job(job_in: JobCreateSchema):
    db = SessionLocal()
    try:
        existing = db.query(Job).filter(Job.canonical_url == job_in.canonical_url).first()
        if existing:
            return {"status": "exists", "job_id": existing.id}

        new_job = Job(
            source=job_in.source,
            canonical_url=job_in.canonical_url,
            title=job_in.title,
            company_name=job_in.company_name,
            location=job_in.location,
            work_arrangement=job_in.work_arrangement,
            salary_min=job_in.salary_min,
            salary_max=job_in.salary_max,
            salary_currency=job_in.salary_currency,
            description=job_in.description,
            status=ApplicationState.DISCOVERED
        )
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
        return {"status": "created", "job_id": new_job.id}
    finally:
        db.close()

@app.post("/api/jobs/{job_id}/score")
def score_and_tailor_job(job_id: int):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        existing_app = db.query(Application).filter(Application.job_id == job.id).first()
        if existing_app and existing_app.state in [ApplicationState.APPLYING, ApplicationState.SUBMITTED]:
            raise HTTPException(409, "Cannot replace application documents while applying or after submission.")

        facts = VerifiedFactsStore()
        resume = db.query(Resume).filter(Resume.is_active == True).first()

        tailored = match_job_with_llm(job.title, job.description or "", facts)
        tailored["target_role"] = job.title
        job.match_score = float(tailored.get("match_score", 75))
        job.match_reason = tailored.get("match_reason", "")
        job.status = ApplicationState.MATCHED

        # Generate ATS Tailored PDF with professional role naming convention
        clean_filename = generate_resume_filename(facts.full_name, job.title, job.company_name, "pdf")
        pdf_path = f"C:/sukesh/job/data/generated-pdfs/{clean_filename}"
        generate_ats_pdf(facts, tailored, pdf_path)

        # Also maintain compatibility alias
        compat_path = f"C:/sukesh/job/data/generated-pdfs/job_{job.id}_tailored.pdf"
        import shutil
        shutil.copy2(pdf_path, compat_path)

        # A conservative cover letter uses the verified summary without invented claims.
        cover_letter = f"Dear Hiring Team,\n\nI am applying for the {job.title} position at {job.company_name}.\n\n{facts.summary}\n\nPlease find my tailored resume attached. I would welcome the opportunity to discuss my experience and this role.\n\nSincerely,\n{facts.full_name}"
        Path(compat_path).with_suffix(".txt").write_text(cover_letter, encoding="utf-8")
        Path(pdf_path).with_suffix(".txt").write_text(cover_letter, encoding="utf-8")

        doc = GeneratedDocument(
            base_resume_id=resume.id if resume else 1,
            job_id=job.id,
            document_type="tailored_resume_pdf",
            file_path=pdf_path,
            ats_score=job.match_score
        )
        db.add(doc)

        # Create or update Application in PENDING_APPROVAL
        idempotency_key = f"app_job_{job.id}_{uuid.uuid4().hex[:8]}"
        existing_app = db.query(Application).filter(Application.job_id == job.id).first()
        if not existing_app:
            app_record = Application(
                job_id=job.id,
                resume_id=resume.id if resume else None,
                state=ApplicationState.PENDING_APPROVAL,
                application_mode=ApplicationMode.APPROVAL_REQUIRED,
                idempotency_key=idempotency_key
            )
            db.add(app_record)

        db.commit()
        return {
            "job_id": job.id,
            "match_score": job.match_score,
            "match_reason": job.match_reason,
            "pdf_filename": clean_filename,
            "pdf_url": f"/pdfs/{clean_filename}",
            "state": existing_app.state.value if existing_app else "Pending Approval"
        }
    finally:
        db.close()

@app.get("/api/applications")
def list_applications():
    db = SessionLocal()
    try:
        apps = db.query(Application).order_by(Application.updated_at.desc()).all()
        results = []
        for a in apps:
            results.append({
                "id": a.id,
                "job_id": a.job_id,
                "job_title": a.job.title if a.job else "Unknown",
                "company": a.job.company_name if a.job else "Unknown",
                "state": a.state.value if hasattr(a.state, 'value') else str(a.state),
                "mode": a.application_mode.value if hasattr(a.application_mode, 'value') else str(a.application_mode),
                "idempotency_key": a.idempotency_key,
                "submitted_at": a.submitted_at.isoformat() if a.submitted_at else None,
                "automation": application_sessions.status(a.id),
                "updated_at": a.updated_at.isoformat() if a.updated_at else None
            })
        return results
    finally:
        db.close()

