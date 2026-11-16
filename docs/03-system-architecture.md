# 03 — System Architecture

**Project Root:** `C:\sukesh\job`  
**Host Architecture:** Windows 11 Pro 64-bit + WSL2 Ubuntu-24.04 (Noble)  
**Hardware:** Intel Core i7-12700F, 64 GB RAM, NVIDIA RTX 5060 Ti  

---

## Architecture Overview

The Autonomous AI Job Hunter Platform operates as a modular, self-hosted micro-pipeline coordinating discovery, scoring, document generation, and human-in-the-loop application submission.

```
                    ┌──────────────────────────────────────────────┐
                    │          Unified Web Dashboard               │
                    │   (FastAPI Gateway & Web UI on :8000)        │
                    └──────────────────────┬───────────────────────┘
                                           │
         ┌───────────────────┬─────────────┴─────────────┬───────────────────┐
         ▼                   ▼                           ▼                   ▼
┌──────────────────┐┌──────────────────┐┌──────────────────────┐┌──────────────────┐
│   Job Collector  ││ AI Resume Engine ││  Application Engine  ││ Dedicated Browser│
│(JobSpy multi-src)││(Local AI + Report││ (Playwright + 4-Mode ││ (Chromium Profile│
│ LinkedIn/Indeed  ││ Lab ATS PDF Gen) ││  Approval Guard)     ││  Isolation)      │
└────────┬─────────┘└────────┬─────────┘└──────────┬───────────┘└────────┬─────────┘
         │                   │                     │                     │
         └───────────────────┴──────────┬──────────┴─────────────────────┘
                                        ▼
                   ┌────────────────────────────────────────┐
                   │    SQLite Integration Database         │
                   │ (`database/ai_job_hunter.db`)          │
                   └────────────────────────────────────────┘
```

## Key Subsystems

1. **Discovery Layer:** JobSpy library queries LinkedIn, Indeed, Glassdoor, and ZipRecruiter, stripping tracking tokens to create canonical URLs.
2. **AI & ATS Document Engine:** Integrates with local LM Studio (`http://127.0.0.1:1234/v1`) using RTX 5060 Ti GPU. Employs a strict Verified Facts Store to guarantee zero hallucinated claims, rendering ATS-compliant single-column PDFs via ReportLab.
3. **Dedicated Browser Manager:** Controls Playwright Chromium instances with isolated persistent profiles in `browser-profiles/`. Bypasses Windows AppLocker by using signed system binaries in `Program Files`.
4. **Safety & Approval Gateway:** Enforces a 4-tier application policy (Default: Mode 3 Approval Required). Captures full-page screenshots before and after form submission, with cryptographic idempotency keys preventing duplicate submissions.
