# 01 — Repository Evaluation & Architectural Assessment Report

**Report Timestamp:** 2026-11-16 14:47 IST  
**System Host:** DESKTOP-P8URD8B (Windows 11 Pro / WSL2 Ubuntu-24.04 / RTX 5060 Ti)  
**Main Project Root:** `D:\AI-Job-Hunter` (`C:\AI-Job-Hunter`)  

---

## 1. Candidate Repositories Evaluation Matrix

| Repository | Latest Tested Commit | License | Tech Stack | Auto-Submit | Self-Hosting | API / Integration | Status & Decision |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **JobNavigator**<br>`vesaias/JobNavigator` | `7558a0e` (2026-11-15) | MIT | FastAPI, React, PostgreSQL 16, Caddy | Assisted Autofill + Runner | Native Docker Compose | REST API (`:8000`) | **ADOPT** (Primary Dashboard & Runner Manager) |
| **JobSpy**<br>`speedyapply/JobSpy` | `68b88d6` (2026-10-27) | MIT | Python, Requests, Pandas, Pydantic | N/A (Scraper) | Local Python / MCP | Python Library + MCP | **ADOPT** (Primary Job Collector Service) |
| **ApplyPilot**<br>`TheSahil/applypilot` | `4a8d521` (2026-03-08) | AGPL-3.0 | Python 3.11+, Playwright, AI Agents | Yes (Dry-run & Auto-Apply) | CLI / Modular Python | CLI + JSON Interface | **ADOPT** (Core Browser Application Engine) |
| **Resume Matcher**<br>`srbhr/Resume-Matcher` | `959e458` (2026-11-16) | Apache-2.0 | Python, Streamlit/FastAPI, Qdrant/Chroma | N/A (Doc Gen) | Docker / Local Python | REST API / Python | **ADOPT** (ATS Resume Parsing & PDF Tailoring) |
| **JobOps**<br>`DaKheera47/job-ops` | `7fac74f` (2026-10-27) | MIT | Node.js, TypeScript, Playwright MCP, Tectonic | No (Discovery + Tracking) | Docker Compose (`:3005`) | MCP / Internal | **EVALUATE** (Alternative Discovery Pipeline) |
| **JobSync**<br>`Gsync/jobsync` | `97971ca` (2026-11) | MIT | Next.js, Node.js, SQLite/PostgreSQL | No (Tracking + Match) | Docker Compose | MCP Server + REST | **EVALUATE** (Alternative Tracker / MCP Integration) |
| **n8n**<br>`n8n-io/n8n` | Official Container | Sustainable Use | Node.js, TypeScript | N/A (Workflow) | Docker Compose (`:5678`) | REST Webhooks & Triggers | **ADOPT** (Scheduler & Webhook Coordinator) |
| **Job Forager**<br>`nipunsomani/job-forager` | `95976b0` | MIT | Python, Playwright | No | Python Script | None | **REJECT** (Redundant with JobSpy & JobNavigator) |
| **OpenApply**<br>`nturl/openapply` | `db7796e` | MIT | Python | Experimental | Python | Minimal | **REJECT** (Superseded by ApplyPilot autonomous agent) |
| **AutoApply**<br>`AbhishekMandapmalvi/AutoApply` | `d06252e` | MIT | Python, Selenium | Partial | Python | None | **REJECT** (Selenium-based, brittle vs Playwright) |

---

## 2. In-Depth Component Analysis

### 2.1 JobNavigator (Primary Dashboard)
- **Role:** Centralized user dashboard, multi-resume management, LLM job scoring, and runner execution.
- **Strengths:** Built-in runner-manager for background execution, native LM Studio / Ollama support (`LMSTUDIO_BASE_URL`), Caddy reverse-proxy, pre-configured PostgreSQL schema.
- **Security:** Strict CORS controls, isolated runner volumes, safe password management.
- **Decision:** **Adopted** as the core web portal on `http://localhost:3000` (or reverse-proxied via Caddy).

### 2.2 JobSpy (Discovery Collector)
- **Role:** Multi-board structured job discovery.
- **Supported Portals:** LinkedIn, Indeed, Glassdoor, ZipRecruiter, Naukri, Bayt, BDJobs, HelloWork.
- **Strengths:** High resilience against bot detection via TLS client emulation, direct Pandas DataFrame / JSON output, scheduled execution without overhead.
- **Decision:** **Adopted** as the headless collection engine feeding normalized jobs into PostgreSQL.

### 2.3 ApplyPilot (Application & Form Automation)
- **Role:** Autonomous job application and form completion with strict dry-run controls.
- **Supported Portals:** Workday, Greenhouse, Lever, Ashby, BambooHR, direct careers pages.
- **Strengths:** 6-stage pipeline (Discover -> Enrich -> Score -> Tailor -> Cover Letter -> Apply), native `--dry-run` flag for safe verification, verified facts isolation.
- **Decision:** **Adopted** for Phase 7 & 8 browser application execution under Playwright.

### 2.4 Resume Matcher (Document Generation Engine)
- **Role:** Resume parsing, vector-based skill matching, and ATS-compliant PDF generation.
- **Strengths:** Parses both PDF and DOCX, integrates with local LLMs (via LM Studio / Ollama) without external telemetry, produces clean ATS-formatted resumes.
- **Decision:** **Adopted** as the microservice for document tailoring.
