# Profile search campaigns and eligibility screening

Open **Job explorer → Search my career lanes**. Choose lanes, a supported public-search source, batch size (1–24 searches), and results per search. The default is 12 searches on Naukri. This collects jobs without tailoring, approving or submitting applications.

`config/search-campaigns.json` defines seven lanes: medical-device software/R&D, embedded/firmware, software QA/V&V, Python/full-stack/mobile, AI/GenAI/RAG, internships/graduate trainees, and JRF/biosensor research. The configuration targets 0–2 years and records no GATE/NET/CEED. It contains 74 keyword/location combinations: Bengaluru, Chennai, Coimbatore, Mysuru, Visakhapatnam and Remote for job lanes, and India for research. Edit this file to adjust keywords, locations or resume directions; the API reads it on each request.

Search batches interleave lanes and persist their next position in collection logs. The same lane selection and sources continue from the previous position across gateway restarts. A changed lane/source selection has a separate cursor. Failed source searches are reported and advanced past rather than blocking every future batch. Failed searches can be retried when the rotation returns. A restart can replay the last unfinished search; canonical URL deduplication prevents duplicate rows. Only one collection task runs at a time in the supported single-gateway configuration.

The automatic cycle now calls these campaigns instead of three identical Biomedical Engineer searches. It avoids automatically tailoring roles screened outside target. Existing approval and submission policies are unchanged.

## Screening

Every loaded job is screened on read, including older jobs; no database migration is needed. Use the eligibility and career-lane filters, then open a job for quoted evidence and a resume direction.

- **Potential match:** relevant text and an entry-level/experience signal without detected restrictions. This is not confirmed eligibility.
- **Needs review:** unknown experience, degree equivalence, graduation/enrollment rules, preferred higher experience, exam mentions/waivers/funding conditions, remote-country restrictions or unclear technical relevance.
- **Outside target:** detected higher required experience, senior title, or mandatory exam not in the configured qualifications. Rows remain stored and accessible under All or Outside target; they are not deleted or automatically rejected.

Exam conditions tied to institute assistantships remain under review. They do not prove a project-funded alternative exists. M.Tech Medical Technology/MCA equivalence is never inferred. Remote text never proves hiring from India. Matching is deterministic text screening, with limitations around unusual wording, tables and custom qualification clauses. The employer's original current listing is authoritative.

Research searches here use the selected public job board, not a new official institute collector. Existing research-source verification remains separate. No new login integrations or source adapters are claimed.

Collection now retains supplied salary, currency, source ID and posting date. Unknown posting dates remain unknown for new collections; previously stored dates cannot be repaired without source evidence. Numeric salary units/periods still require checking against the original listing.

## API and verification

- `GET /api/search-campaigns`: configuration and plan size.
- `POST /api/search-campaigns/run`: optional `campaign_ids`, `sites`, `max_searches`, `results_wanted`; progress/errors via `/api/collection/status`.
- `GET /api/jobs`: additive `screening` object; optional `eligibility` and `campaign` filters operate on the most recent `limit` loaded jobs.

32 checks passed: 11 matching fixtures, 17 isolated API tests, 3 existing dashboard checks and 1 campaign browser workflow. Tests cover mandatory/preferred experience, degree and exam uncertainty, funding restrictions, .NET versus NET, remote restrictions, rotation, collector failures, salary/date preservation, UI filters, evidence and mobile overflow. UI campaign starts and API collectors are mocked in tests; live discovery is not proof that a vacancy is still accepting applications.
