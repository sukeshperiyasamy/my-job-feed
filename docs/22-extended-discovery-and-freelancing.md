# Extended discovery and freelancing

Open `http://127.0.0.1:8000/#discovery` for **Discovery coverage**, and
`http://127.0.0.1:8000/#freelancing` for the separate freelance pipeline.

## Discovery

The user-provided `ai-job-search` checkout has six portal tools. This integration
reuses its FreeHire search and parsing implementation, pinned with source hashes
under `integrations/ai-job-search`. Four Denmark-specific tools are not enabled.
The LinkedIn scraper is not scheduled because its own documentation notes access
restrictions; the dashboard supplies a manual search link instead. FreeHire can
itself return LinkedIn URLs; these are counted as manual review links.

The Python bridge invokes the borrowed dependency-free TypeScript with Node 24.
Requests go only to FreeHire's public API, with cross-host redirects disabled and
a 40-second subprocess deadline. No CV, cookies, passwords or candidate profile
is sent. Queries use public career interests and India/global-remote scope.

Scans rotate through unique queries from existing career campaigns, with up to
six queries and 25 results each by default (API maximum eight and 50). The UI can
select a lane, India or global remote, and a 7/30/90-day posting window. A global
remote facet is not proof of India eligibility. Queries are cached for 15 minutes;
rotation and cache files stay under ignored `data/extended-search`.

Results use the existing conservative screening and canonical URL deduplication,
including Lever's apply alias. Exact duplicates preserve application state and
prior availability evidence. Same company/title with different URLs is retained
as a possible duplicate in provenance; it is not automatically merged because
multiple locations/requisitions can share a title. New jobs are `unchecked` until
an independent availability check succeeds. Missing pay is left undisclosed;
the borrowed search schema does not include structured compensation, so it is
not inferred from descriptions. Dates are aggregator-provided, not independently
verified employer publication dates.

Per-query counts show fetched, imported, already saved, excluded, malformed,
review-needed and potential matches. The reported source-wide total is never
presented as a count of suitable vacancies. API blocks/timeouts/errors remain
visible in results; they do not appear as a successful zero-result search.
The existing collection lock and durable execution logs cover extended scans.

`scripts/automation_cycle.py` includes one six-query India discovery pass after
the existing watchlist/Naukri pass. This extends callers of that script; it does
not create an additional scheduler or approve applications.

## Freelancing

Freelance leads use an additive `freelance_leads` SQLite table separate from jobs
and applications. Save a project URL, original brief, service and published budget.
Canonical URL duplicates are rejected. Stages are Saved, Drafting, Proposal sent,
Interview, Won and Closed. A review dialog saves editable proposals and stages.

Starter drafts are deterministic, editable templates, not an AI claim of project
understanding or previous client work. They do not overwrite an existing draft.
The UI does not send bids, messages or proposals. The platform cards are browse
links checked on 17 November 2026, not a feed of verified open freelance projects.
Services reflect the user's stated Python, AI/RAG, mobile, QA, ComfyUI and sensor
prototype skills; they do not assert medical-device regulatory certification.

## Validation on 17 November 2026

The first live six-query India scan fetched 150 records and saved 84 leads. After
tightening visible foreign-location and lead/Engineer III filters, those saved
records screen as 40 potential matches, 37 needing review and seven outside the
target. Screening is not a live-vacancy or eligibility guarantee. Existing records
were retained rather than deleted. A repeat of the same six cached queries saved
zero new records, recognised 77 existing relevant listings and excluded 73 records.

Eight isolated integration tests, eleven screening tests, seventeen existing
operations tests and eight Career Ops tests passed. Five browser tests covered
the new workflow and existing dashboard/Career Ops flows, including duplicate
counts, proposal persistence, escaped project briefs and mobile layout. Test
modules that own process-global temporary databases run in separate processes.
No application, bid or proposal was sent during validation.
