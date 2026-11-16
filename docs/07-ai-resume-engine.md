# 07 — AI Resume & Document Tailoring Engine

**Module:** `services/resume-engine/engine.py`  
**PDF Generator:** ReportLab 5.1.0  
**Verification:** PyPDF 7.1.0  
**Primary AI Engine:** Antigravity CLI (`agy.exe` v1.5.9)  
**Local Fallback Host:** LM Studio on port 1234 (`http://127.0.0.1:1234/v1`)  

---

## 1. Verified Facts Store

To prevent LLM hallucinations, candidates' verified experience, degrees, projects, and contact information are encapsulated in `VerifiedFactsStore`. The AI is strictly instructed to re-order and emphasize existing competencies rather than inventing new qualifications.

## 2. ATS Formatting Standards

- Single-column layout.
- Standard typography with clean hierarchy.
- No nested multi-cell tables that break optical parsing.
- Programmatic verification via PyPDF to confirm character extractability before storage.
