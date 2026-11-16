# 08 — Automated Application Engine

**Module:** `services/application-engine/engine.py`  
**Safety Modes:**  
1. `discovery_only`: No form filling.  
2. `form_preparation`: Fills forms but never triggers submit.  
3. `approval_required` (Default): Fills form, uploads resume, captures screenshot, waits for human operator approval.  
4. `selective_auto`: Submits automatically only for explicitly whitelisted domains.  

---

## 1. Safety Policies

- Automatic submission is disabled by default.
- Verification screenshot is captured upon form completion and saved to `screenshots/`.
- Submission outcome records confirmation codes (e.g. `APP-2026-99214`).
- Idempotency guards block duplicate applications permanently.
