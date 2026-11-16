# 02 — Installation & Runtime Validation Report

**Deployment Root:** `D:\AI-Job-Hunter` (Mounted to `C:\AI-Job-Hunter`)  
**Validation Timestamp:** 2026-11-16 14:45 IST  

---

## 1. Installed Software Status & Validation Matrix

| Component | Installation Source | Verified Version | Execution Path / Interface | Verification Status |
| :--- | :--- | :--- | :--- | :--- |
| **Git** | Native Windows Installer | `2.56.0.windows.4` | `git` (in PATH) | Verified Healthy |
| **WSL2** | Microsoft WSL2 Subsystem | Kernel 5.15+, Ubuntu-24.04 | `wsl -d Ubuntu-24.04` | Verified (`systemd=true`) |
| **Docker Engine** | Ubuntu APT Repository | `29.1.3` | `docker` via Windows wrapper & WSL | Verified (`hello-world` test passed) |
| **Docker Compose** | Ubuntu APT Repository | `2.40.3` | `docker-compose` wrapper & WSL | Verified |
| **Python (Windows)** | Python Software Foundation | `3.12.10` (64-bit) | `python`, `pip 25.0.1` | Verified Healthy |
| **Python (WSL)** | Ubuntu Noble Canonical | `3.12.3` | `python3` in WSL2 | Verified |
| **Node.js (LTS)** | WinGet Portable Distribution | `v24.20.0` | `node` (in User PATH) | Verified (`node -v`) |
| **npm** | WinGet / Node.js Bundle | `11.19.0` | `npm` (in User PATH) | Verified (`npm -v`) |
| **Local AI Engine** | LM Studio (NVIDIA GPU) | Local Server | `http://127.0.0.1:1234/v1` | Verified Active with 6 models |

---

## 2. Docker & Container Network Validation

- **Daemon Status:** `systemctl is-active docker` returns `active`.
- **User Group:** Default user `lokikende` added to `docker` group for passwordless access.
- **Port Forwarding:** WSL2 localhost mirror automatically forwards ports (e.g. 3000, 5678, 8000, 5432) to Windows host `localhost`.
- **Host Bridge Wrapper:** Windows-side CLI bridges `docker.cmd` and `docker-compose.cmd` in `D:\AI-Job-Hunter\scripts` allow direct invocation from PowerShell and Windows Terminal.

---

## 3. Storage Hierarchy Validation

- Root path `D:\AI-Job-Hunter` mapped via NTFS drive substitution.
- WSL access path: `/mnt/c/AI-Job-Hunter`.
- Subdirectories initialized: `apps/`, `services/`, `dashboard/`, `browser-profiles/`, `data/`, `database/`, `backups/`, `logs/`, `screenshots/`, `config/`, `docker/`, `scripts/`, `tests/`, `docs/`.
