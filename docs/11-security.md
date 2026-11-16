# 11 — Security & Privacy Architecture

**Standard:** Zero Exposure, Localhost Bound  

---

## 1. Network Security

- Dashboard and API bind exclusively to `127.0.0.1`.
- Remote access strictly recommended via Tailscale or SSH tunnels.
- Browser remote debugging ports are never exposed to public interfaces.

## 2. Credential & Data Protection

- No plaintext passwords or credentials committed to source repositories.
- Browser session states are isolated in local user-only directories (`browser-profiles/`).
- Idempotency hashing prevents accidental re-submissions.
