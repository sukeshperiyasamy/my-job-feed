# 05 — Dedicated Browser Automation Setup

**Engine:** Playwright Chromium 1.65.2  
**Profile Location:** `C:\sukesh\job\browser-profiles\`  
**Screenshots:** `C:\sukesh\job\screenshots\`  

---

## 1. Browser Profile Isolation

- Completely isolated from personal Chrome profiles.
- Each worker/portal session receives an independent folder under `browser-profiles/<profile_name>`.
- Preserves cookies and session states for portal logins without storing plaintext passwords.

## 2. Windows Application Control (WDAC / AppLocker) Compliance

- Unsigned executables in `AppData\Local` are blocked by host security policies.
- Playwright manager was configured to execute the signed browser binaries located in `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe` or `C:\Program Files\Google\Chrome\Application\chrome.exe`.
- Bypasses binary execution blocks while pointing strictly to custom user-data directories.
