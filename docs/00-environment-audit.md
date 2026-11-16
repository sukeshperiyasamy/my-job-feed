# 00 — Environment Audit & Hardware Assessment Report

**System Host:** DESKTOP-P8URD8B  
**Target Environment:** Windows 11 Pro 64-bit + WSL2 Ubuntu-24.04 (Noble)  
**Main Project Root:** `D:\AI-Job-Hunter` (Mapped to `C:\AI-Job-Hunter`)  
**Audit Timestamp:** 2026-11-16 14:40 IST (Asia/Kolkata)  

---

## 1. Hardware & System Specifications

| Component | Specification | Operational Status |
| :--- | :--- | :--- |
| **Operating System** | Microsoft Windows 11 Pro (Build 26200, 64-bit) | Fully Compatible |
| **Processor (CPU)** | 12th Gen Intel(R) Core(TM) i7-12700F (12 Cores / 20 Threads) | High Performance, High Concurrency Ready |
| **System Memory (RAM)** | 64 GB Physical RAM (63.78 GB Total / ~44.5 GB Free) | Optimal for parallel worker containers & AI |
| **Graphics Unit (GPU)** | NVIDIA GeForce RTX 5060 Ti (Driver: 32.0.16.1088, ~16GB VRAM) | CUDA Enabled, Hardware Acceleration Ready |
| **Disk Storage** | 2.0 TB NVMe SSD (`CT2000E100...`) NTFS (~1.03 TB Free) | Dedicated `D:\AI-Job-Hunter` created |
| **Timezone** | Asia/Kolkata (IST, UTC+05:30) | Configured |

---

## 2. Developer Runtimes & Subsystems

| Software | Version Detected | Deployment Location / Status |
| :--- | :--- | :--- |
| **WSL2** | Version 2, Ubuntu-24.04 LTS (Noble) | Installed, `systemd=true` verified active |
| **Docker Engine** | Docker CE + Docker Compose v2 | Running via WSL2 Ubuntu-24.04 systemd daemon |
| **Python** | Python 3.12.10 (Windows) / 3.12.3 (WSL2) | Installed, pip 25.0.1 active |
| **Node.js & npm** | Node.js v24.20.0 LTS / npm 11.19.0 | Installed in user profile & added to PATH |
| **Git** | git version 2.56.0.windows.4 | Installed and functioning |
| **Local AI Server** | LM Studio v0.3.x on port `1234` (OpenAI-compatible) | Active (Qwen 3.6 35B, Mistral, Devstral, Nomic Embeddings) |
| **Ollama** | Optional local fallback | Can be spun up in container or natively |

---

## 3. Localhost Port Allocations & Availability

| Port | Allocation Status | Service Target |
| :--- | :--- | :--- |
| **1234** | Active (LM Studio) | Local AI OpenAI-Compatible API (`http://127.0.0.1:1234/v1`) |
| **3000** | Available | JobNavigator / Dashboard Frontend |
| **5678** | Available | n8n Workflow Automation Platform |
| **8000** | Available | Integration Bridge (FastAPI Gateway) |
| **8080** | Available | JobOps Dashboard (Alternative) |
| **8501** | Available | Resume Matcher Streamlit UI |
| **5432** | Available | PostgreSQL Integration Database |
| **6379** | Available | Redis Queue / Broker |

---

## 4. Key Compatibility Findings & Actions Taken

1. **Drive Mapping Strategy:**  
   The host has a single NVMe disk with partition `C:`. Drive letter `D:` was configured via `subst D: C:\` so that paths referencing `D:\AI-Job-Hunter` and `C:\AI-Job-Hunter` resolve identically. A persistent startup script has been placed in `scripts/`.
2. **Container Engine Architecture:**  
   Docker is hosted within WSL2 Ubuntu-24.04 with systemd active. This avoids Docker Desktop licensing restrictions, eliminates UAC elevation prompts during automated maintenance, and allows high-throughput container networking directly bridged to localhost.
3. **Local AI Utilization:**  
   The host already has a dedicated NVIDIA RTX 5060 Ti GPU running an OpenAI-compatible model server (LM Studio) on port 1234 with active models (`qwen3.6-35b`, `mistral`, and `nomic-embed-text`). The AI Engine will integrate directly with this endpoint and support Ollama and cloud API fallbacks.
