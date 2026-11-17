import re
import urllib.parse
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import pandas as pd
from jobspy import scrape_jobs

def sanitize_job_url(raw_url: str) -> str:
    """Strip tracking query parameters (utm_*, refId, trackingId, etc.) to get canonical URL."""
    if not raw_url:
        return ""
    parsed = urllib.parse.urlparse(raw_url)
    clean_params = []
    # Drop known tracking parameters
    for k, v in urllib.parse.parse_qsl(parsed.query):
        k_lower = k.lower()
        if k_lower.startswith("utm_") or k_lower in {"refid", "trackingid", "trk", "midtoken", "fcta", "origin", "src"}:
            continue
        clean_params.append((k, v))
    new_query = urllib.parse.urlencode(clean_params)
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, ""))

def run_jobspy_discovery(
    search_term: str = "Software Engineer",
    location: str = "India",
    sites: Optional[List[str]] = None,
    results_wanted: int = 15,
    hours_old: int = 72,
    country_indeed: str = "India",
    raise_errors: bool = False
) -> List[Dict[str, Any]]:
    """
    Executes multi-board scrape via JobSpy and returns normalized job records.
    """
    if sites is None:
        sites = ["linkedin", "indeed", "glassdoor", "zip_recruiter"]

    print(f"[*] Starting JobSpy discovery: '{search_term}' in '{location}' across {sites}")
    try:
        df: pd.DataFrame = scrape_jobs(
            site_name=sites,
            search_term=search_term,
            location=location,
            results_wanted=results_wanted,
            hours_old=hours_old,
            country_indeed=country_indeed
        )
    except Exception as e:
        if raise_errors:
            raise
        print(f"[!] Scrape encounter warning: {e}")
        return []

    if df is None or df.empty:
        print("[-] No jobs returned from current search parameters.")
        return []

    normalized_jobs = []
    for _, row in df.iterrows():
        raw_url = str(row.get("job_url", "") or "")
        canonical_url = sanitize_job_url(raw_url)
        if not canonical_url:
            continue

        salary_min = None
        salary_max = None
        if pd.notna(row.get("min_amount")):
            try:
                salary_min = float(row.get("min_amount"))
            except (ValueError, TypeError):
                pass
        if pd.notna(row.get("max_amount")):
            try:
                salary_max = float(row.get("max_amount"))
            except (ValueError, TypeError):
                pass

        posting_date = None
        if pd.notna(row.get("date_posted")):
            try:
                posting_date = pd.to_datetime(row.get("date_posted")).to_pydatetime()
            except Exception:
                posting_date = None

        job_record = {
            "source": str(row.get("site", "jobspy")).lower(),
            "source_job_id": str(row.get("id", "") or ""),
            "canonical_url": canonical_url,
            "title": str(row.get("title", "") or "Untitled Position"),
            "company_name": str(row.get("company", "") or "Unknown Company"),
            "location": str(row.get("location", "") or location),
            "work_arrangement": str(row.get("job_type", "") or "Full-time"),
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_currency": str(row.get("currency", "INR") or "INR"),
            "description": str(row.get("description", "") or ""),
            "posting_date": posting_date,
            "discovery_date": datetime.now(timezone.utc),
            "is_eligible": True,
            "status": "Discovered"
        }
        normalized_jobs.append(job_record)

    print(f"[+] Successfully normalized {len(normalized_jobs)} jobs.")
    return normalized_jobs
