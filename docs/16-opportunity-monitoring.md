# Internships, research and remote opportunities

Dashboard tabs: `#internships`, `#research`, `#remote`. The existing Job explorer remains the working application queue; these tabs add evidence and eligibility review before a lead is saved there.

## Source and detail workflow

Each card links its discovery source and original application/posting separately. Full details include location, experience, eligibility, tests, funding/pay, assistantship restrictions, selection dates, deadline with timezone where supplied, source date, check time, technologies, regulatory requirements, fit and recommended resume. Missing information stays explicitly unknown. An employer homepage, programme page, HTTP 200 or search snippet is not proof of an accepting vacancy.

The initial baseline includes Dozee Biomedical Intern (Jaipur), HackerRank's six-month January 2027 Bengaluru software internship, and Enterpret's Bengaluru backend internship. Enterpret's current-enrollment and prior-internship requirements are flagged. Old/unverified internship leads, verified winter admission notices and closed cycles are separated. Search coverage is partial. The source directory includes all 19 requested MedTech companies, additional employers, all 23 IITs and 31 NITs, research institutions and remote/platform sources. A directory target is not a verified vacancy or proof it has already been checked.

`config/opportunity-seeds.json` supplies initial reviewed records. Subsequent `POST /api/opportunities` updates are stored durably in `data/opportunities/catalog.json`; seed files are not overwritten. The API requires original source and application URLs. Verified-open records require dated evidence. A passed deadline automatically becomes Expired. Records not rechecked for three days become Needs recheck. Date-only deadlines use `deadline_date` and an explicit note; no 11:59 pm closing time is invented.

## Updating a reviewed opportunity

Post JSON to `http://127.0.0.1:8000/api/opportunities` with:

- `category`: internship, job, research or remote
- `title`, `organization`, `location`, `source_name`, `source_url`, `application_url`
- `status`: Verified open, Unverified, Expired, Upcoming or Hiring signal
- `verified_at`: timezone-aware ISO timestamp of source review
- `source_date`: publication/update date or null, not search crawl date
- `deadline`: timezone-aware exact timestamp when published, otherwise null
- `deadline_date`: YYYY-MM-DD only when a date but no time is published
- `deadline_note`, `evidence`, and `details`

`details` can contain department, supervisor, experience, eligibility, exams, funding/pay, assistantship, selection_dates, duration, technologies, regulatory, india_eligibility, fit, recommended_resume, apply_mode, description and additional_sources. Do not infer degree equivalence. Separate admission eligibility from assistantship and actual project hiring. Do not treat a JRF job as guaranteed PhD admission. Civil/mechanical/automobile/production and unrelated research should not enter the matching catalog.

After completing each review, run:

```powershell
& C:/sukesh/job/.venv/Scripts/python.exe C:/sukesh/job/scripts/publish_opportunity_report.py
```

It persists a timestamped source-linked Markdown report and compares material details with the previous report. The first run is a baseline. Later runs explicitly state 'No new verified openings' per lane when applicable. Read previous reports before claiming hiring changes. Record attempted-source failures/coverage gaps alongside the report; do not silently call an incomplete pass exhaustive.

## Morning/evening automation

The existing Codex heartbeat is updated to 09:00 and 18:00 Asia/Kolkata. It performs source research and updates the catalog, with priority for Tamil Nadu and deadlines within 14 days, plus Bengaluru early-career roles and nationwide research. It retains the existing collection/tailoring loop where needed and leaves submission allowlists unchanged. PC/app availability is required; this is not a cloud service guarantee.

## Remote work boundaries

Employer roles require explicit country/India eligibility review. For Canonical's seeded graduate role, the bachelor's completion-year condition does not match the user's 2022 BSc; its prohibition on AI-generated answers is clearly displayed and it is not sent to automation. A USD learning allowance is not salary.

Mercor, Turing, micro1 and Outlier are manual sign-up/screening/assessment lanes. Work availability and income are not guaranteed. Marketplace entries are directories for manual proposals, not scraped live tasks; no sign-ups, assessments, proposals or messages are sent automatically. Fiverr, Freelancer and PeoplePerHour terms have not been comprehensively reviewed. Never pay to apply, transfer money for a job, or upload sensitive documents to an unverified domain.

## Validation

Regression tests cover effective expiry and stale verification, exact source/application links, date-only deadlines, source fields and responsive internship cards. Existing application guards remain in place. No real application is submitted by this feature.
