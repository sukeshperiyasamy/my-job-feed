# 06 — Job Collectors & Discovery

**Module:** `services/job-collector/collector.py`  
**Underlying Library:** `python-jobspy` (v1.4.1)  

---

## 1. Supported Portals

- LinkedIn
- Indeed (India & Global)
- Glassdoor
- ZipRecruiter
- Bayt / Naukri

## 2. Normalization & Deduplication

- Strips tracking tokens (`utm_*`, `refId`, `trackingId`, `midToken`, `fcta`, `origin`).
- Generates canonical URLs to prevent duplicate entries across scrape cycles.
- Normalizes salary ranges into standard min/max numbers with currency tags.
- Saves structured records to SQLite / PostgreSQL database.
