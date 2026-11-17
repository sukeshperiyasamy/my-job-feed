# Career Ops discovery and availability

Open `http://127.0.0.1:8000/#careerops`. Career Ops is integrated through a separate
read-only adapter; its own dashboard and application workflow do not replace this
project's dashboard, saved answers, verified profile or approval queue.

## Use

1. Select public sources, a career lane and an import cap. **Scan selected sources**
   imports matching India/remote leads into Job explorer. Higher-experience roles
   are excluded by default. Unknown qualifications and India eligibility remain
   under review; collected means discovered, not independently verified open.
2. **Add employer board** connects a real public board URL for one supported
   provider. It does not create an employer account or provide API credentials.
3. Check up to five saved jobs, or use **Check availability** in job details.
   API checks run first. Optional anonymous-browser inspection uses a separate
   ephemeral browser, with URL/DNS guards and robots checks. It never attaches to
   the project account browser, logs in, solves CAPTCHA or submits a form.
4. Availability appears in Job explorer and can be filtered. `active` means the
   API lists a posting or a page has an application control; it does not guarantee
   employer responsiveness, fresh posting age, eligibility or a successful application.
   Blocks, timeouts and unsupported pages stay `uncertain`. An uncertain recheck
   does not clear a preceding definitive `expired` verdict. Expired postings cannot
   start an application until a positive recheck changes that state.

## Included scope

Eight upstream providers: Greenhouse, Lever, Ashby, SmartRecruiters, Recruitee,
Himalayas, Remotive and We Work Remotely. Seven starting source cards: Dozee,
HackerRank, Enterpret, DehazeLabs and the three remote feeds. Other supported
employer boards can be added. This does not enable all upstream providers or its
global reverse-ATS/company-directory scanner. Research admissions keep their
separate official-source verification workflow.

Each source is capped at two pages, twelve HTTP requests and 400 returned records,
then at the selected import cap. A cap/partial response is reported; scans are not
exhaustive. Employer results are cached for 15 minutes, We Work Remotely for one
hour, Remotive for six hours, and Himalayas for 24 hours. Feed cadence and cached
source time are separate from individual availability checks. Manual rescans use
the same cached feed rather than bypassing publisher cadence limits.

Native URLs are canonicalized for deduplication, including Lever's `/apply` alias.
Existing application states are preserved. Salary/date fields are retained when
the provider supplies them, without inventing unknown dates or currency. Where
upstream annualizes compensation, its as-posted pay period/range remains in
provenance metadata. Remote results retain publisher URLs and visible attribution;
Himalayas' supplied application link is not replaced by an employer URL.

## Installation and ownership

Run `powershell -File scripts/install_career_ops.ps1` from this workspace on a new
installation. Node must meet upstream's requirement (`^22.13.0 || >=23.4.0`);
the live installation uses Node 24.20.0. The helper installs revision
`0ad9049f726105894bc9e85843ab7f510646baf0`, then installs locked dependencies with
package scripts disabled. The adapter's readiness check refuses an unexpected
upstream revision. Updating that pin requires deliberate integration testing.

The upstream checkout/dependencies live under ignored `apps/career-ops`. Runtime
cache and custom source metadata live under ignored `data/career-ops`. No CV,
saved answer, browser cookie or account password is copied into upstream. Its
profile, AI, application and tracker commands are not run. The MIT license and
attribution are under `integrations/career-ops`.

`job_verifications` is an additive SQLite table created by the existing metadata
startup path. Availability/provenance stay separate from application status.
Scans/checks share the existing collection lock, durable results and restart
interruption reporting. Use one gateway process; this is not a multi-worker queue.

## Validation

`tests/test_career_ops_api.py` checks ingestion, duplicate prevention, provenance,
cache cadence, failures, limits, origin protection and expiry guards. The Node
adapter fixture harness exercises actual upstream parser modules, source routing,
404/429 handling and public-network guards. The UI test mocks actions and checks
scanning, source attribution, batch checking, detail controls and mobile overflow.

Live checks exercised Dozee's feed, a Greenhouse posting API and an anonymous
browser inspection. A three-source scan imported 12 leads before stricter staff/
quality-manager filtering was added; these remain reviewable, with screening
updated on read. Repeated scans deduplicate them. No real application was submitted.
