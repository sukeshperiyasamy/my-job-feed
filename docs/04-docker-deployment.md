# 04 — Docker & Container Infrastructure

**Deployment Method:** WSL2 Ubuntu-24.04 with Native Systemd Engine  
**Docker Version:** 29.1.3  
**Compose Version:** 2.40.3  

---

## 1. Engine Configuration

- Docker is hosted directly inside WSL2 Ubuntu-24.04 (`systemd=true`).
- No commercial Docker Desktop license required.
- Passwordless access configured for user `lokikende` in group `docker`.
- Windows PowerShell bridges created in `scripts/docker.cmd` and `scripts/docker-compose.cmd`.

## 2. Service Orchestration

- **JobNavigator:** Configured in `apps/jobnavigator/docker-compose.yml` with overrides in `docker-compose.override.yml`. Exposes dashboard on port 3000/80 and PostgreSQL on port 5432.
- **JobOps:** Configured in `apps/jobops/docker-compose.yml` exposing port 3005.
- **Integration Bridge:** Runs natively on Windows port 8000 via Uvicorn.
