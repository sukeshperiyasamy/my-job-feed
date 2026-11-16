# Autonomous AI Job Hunter & Application Platform

A complete, self-hosted, modular platform for discovering jobs across multiple job portals, performing ATS-compliant resume tailoring with local AI, filling application forms via dedicated Playwright browser automation, and managing human-in-the-loop approvals.

---

## 1. Quick Start

### Start All Services:
```powershell
powershell -ExecutionPolicy Bypass -File C:\sukesh\job\scripts\start.ps1
```

### Access Dashboards:
- **Unified Command Center:** [http://localhost:8000](http://localhost:8000)
- **Local AI Engine (LM Studio):** [http://127.0.0.1:1234/v1](http://127.0.0.1:1234/v1)

### Check Health & Status:
```powershell
powershell -ExecutionPolicy Bypass -File C:\sukesh\job\scripts\status.ps1
```

### Stop All Services:
```powershell
powershell -ExecutionPolicy Bypass -File C:\sukesh\job\scripts\stop.ps1
```

---

## 2. Directory Architecture

```text
C:\sukesh\job\
├── apps\                # Cloned and verified third-party tools (jobnavigator, jobops, jobspy, applypilot, resume-matcher)
├── services\
│   ├── job-collector\   # Multi-board JobSpy scrapers (LinkedIn, Indeed, Glassdoor, ZipRecruiter)
│   ├── resume-engine\   # ReportLab ATS single-column PDF generator & verified facts store
│   ├── browser-manager\ # Playwright Chromium dedicated isolate (bypasses Windows AppLocker)
│   ├── application-engine\ # Multi-mode autofill & submission engine
│   └── integration-bridge\ # FastAPI gateway, SQLite database, and REST coordination
├── dashboard\           # Modern unified web interface
├── browser-profiles\    # Dedicated persistent browser data (never touches personal Chrome)
├── data\
│   ├── resumes\         # User master resumes
│   └── generated-pdfs\  # Tailored ATS PDFs created per job
├── database\            # SQLite integration database (`ai_job_hunter.db`)
├── backups\             # Snapshot archives
├── screenshots\         # Verification screenshots taken during automation
├── scripts\             # Management and diagnosis scripts (PowerShell)
├── tests\               # Full automated unit, integration, and E2E test suites
└── docs\                # Comprehensive system documentation
```

---

## 3. Operational CLI Commands

| Action | Command |
| :--- | :--- |
| **Run Live Job Scraper** | `powershell -File C:\sukesh\job\scripts\run_jobspy.ps1 -SearchTerm "Python" -Results 5` |
| **Run E2E Pipeline Test**| `& C:\sukesh\job\.venv\Scripts\python.exe C:\sukesh\job\tests\test_end_to_end_flow.py` |
| **Create Backup** | `powershell -File C:\sukesh\job\scripts\backup.ps1` |
| **System Status** | `powershell -File C:\sukesh\job\scripts\status.ps1` |

---

## 4. Key Safety Principles

1. **Human Approval by Default:** Form applications stop at `Pending Approval` mode. Submissions are only triggered after the user approves via the dashboard.
2. **Strict Hallucination Prevention:** The `VerifiedFactsStore` prevents AI models from inventing degrees, companies, dates, or skills.
3. **Browser Isolation:** Runs in a dedicated Chromium instance using separate profile directories. Personal Chrome cookies and data are never accessed.
4. **Idempotency Protection:** Every application attempt carries an idempotency key. A submitted job can never be submitted a second time.

# my-job-feed
