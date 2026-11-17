import enum
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float,
    ForeignKey, Enum, Index, JSON, create_engine
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

class ApplicationState(str, enum.Enum):
    DISCOVERED = "Discovered"
    NORMALIZED = "Normalized"
    MATCHED = "Matched"
    DOCUMENT_READY = "Document Ready"
    PENDING_APPROVAL = "Pending Approval"
    APPLYING = "Applying"
    SUBMITTED = "Submitted"
    FAILED = "Failed"
    MANUAL_ACTION_REQUIRED = "Manual Action Required"
    SKIPPED = "Skipped"

class ApplicationMode(str, enum.Enum):
    DISCOVERY_ONLY = "discovery_only"
    FORM_PREPARATION = "form_preparation"
    APPROVAL_REQUIRED = "approval_required"
    SELECTIVE_AUTO = "selective_auto"

class JobSource(Base):
    __tablename__ = "job_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)  # e.g. linkedin, indeed, naukri, greenhouse
    enabled = Column(Boolean, default=True, nullable=False)
    rate_limit_seconds = Column(Integer, default=5)
    last_run_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    domain = Column(String(255), nullable=True)
    careers_url = Column(String(1024), nullable=True)
    ats_provider = Column(String(100), nullable=True)  # workday, greenhouse, lever, ashby
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(100), nullable=False)
    source_job_id = Column(String(255), nullable=True)
    canonical_url = Column(String(2048), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    work_arrangement = Column(String(100), nullable=True)  # Remote, Hybrid, On-site
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    salary_currency = Column(String(10), default="USD")
    experience_level = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    posting_date = Column(DateTime, nullable=True)
    discovery_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_verified_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # AI Matching & Scoring
    match_score = Column(Float, nullable=True)  # 0.0 - 100.0 or 1 - 10
    match_reason = Column(Text, nullable=True)
    is_eligible = Column(Boolean, default=True)
    status = Column(Enum(ApplicationState), default=ApplicationState.DISCOVERED, nullable=False)

    # Relationships
    applications = relationship("Application", back_populates="job")

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    display_name = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(1024), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf, docx
    version = Column(String(50), default="1.0")
    skills_json = Column(JSON, default=list)
    experience_summary = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    generated_documents = relationship("GeneratedDocument", back_populates="base_resume")

class GeneratedDocument(Base):
    __tablename__ = "generated_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    base_resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    document_type = Column(String(50), nullable=False)  # tailored_resume_pdf, cover_letter_pdf, docx
    file_path = Column(String(1024), nullable=False)
    tailored_text = Column(Text, nullable=True)
    ats_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    base_resume = relationship("Resume", back_populates="generated_documents")

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, unique=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)
    state = Column(Enum(ApplicationState), default=ApplicationState.PENDING_APPROVAL, nullable=False)
    application_mode = Column(Enum(ApplicationMode), default=ApplicationMode.APPROVAL_REQUIRED, nullable=False)
    idempotency_key = Column(String(255), unique=True, nullable=False)
    submitted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    job = relationship("Job", back_populates="applications")
    attempts = relationship("ApplicationAttempt", back_populates="application")

class ApplicationAttempt(Base):
    __tablename__ = "application_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    worker_id = Column(String(100), nullable=False)
    attempt_number = Column(Integer, default=1)
    status = Column(String(50), nullable=False)  # success, failure, dry_run, halted
    is_dry_run = Column(Boolean, default=True)
    screenshot_path = Column(String(1024), nullable=True)
    error_message = Column(Text, nullable=True)
    attempted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    application = relationship("Application", back_populates="attempts")

class AutomationSchedule(Base):
    __tablename__ = "automation_schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_name = Column(String(100), unique=True, nullable=False)  # e.g. job_discovery, resume_scoring
    interval_hours = Column(Integer, default=6)
    last_executed_at = Column(DateTime, nullable=True)
    next_scheduled_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    service = Column(String(100), nullable=False)
    level = Column(String(20), default="INFO")
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class WatchedCompany(Base):
    __tablename__ = "watched_companies"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    careers_url = Column(String(2048), unique=True, nullable=False)
    region = Column(String(100), nullable=False)
    sector = Column(String(100), default="MedTech")
    company_type = Column(String(100), default="Company")
    evidence_url = Column(String(2048), nullable=True)
    notes = Column(Text, default="")
    enabled = Column(Boolean, default=True)
    content_hash = Column(String(64), nullable=True)
    last_checked_at = Column(DateTime, nullable=True)
    last_status = Column(String(100), default="Not checked")
    last_error = Column(Text, nullable=True)
    last_new_jobs = Column(Integer, default=0)
    details = Column(JSON, nullable=True)

class FreelanceLead(Base):
    __tablename__ = "freelance_leads"
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    url = Column(String(2048), unique=True, nullable=False)
    platform = Column(String(120), default="Direct client")
    service = Column(String(100), default="Python & automation")
    budget = Column(String(200), default="Undisclosed")
    description = Column(Text, default="")
    proposal = Column(Text, default="")
    status = Column(String(40), default="Saved")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class JobVerification(Base):
    __tablename__ = "job_verifications"
    job_id = Column(Integer, ForeignKey("jobs.id"), primary_key=True)
    provider = Column(String(80), nullable=True)
    source_name = Column(String(200), nullable=True)
    source_url = Column(String(2048), nullable=True)
    collected_at = Column(DateTime, nullable=True)
    availability = Column(String(30), default="unchecked", nullable=False)
    checked_at = Column(DateTime, nullable=True)
    reason = Column(Text, nullable=True)
    details = Column(JSON, default=dict)
