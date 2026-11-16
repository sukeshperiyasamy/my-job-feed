# Application automation and regional watchlist

The local dashboard is at http://127.0.0.1:8000. This version uses a bounded Playwright form worker with optional local-model contact-field mapping. It does not install or claim to use browser-use or ApplyPilot's Claude integration.

## Daily workflow

1. Open **Company watchlist**, choose Tamil Nadu, Bengaluru, or Andhra Pradesh, and check career pages. Twelve official company/hub pages are seeded. Regional targets are not guarantees of individual job locations. Adjacent industrial AI and biologics companies are labelled separately.
2. Open **Job portals → Discover jobs** for Naukri and other public sources. HirePro is an employer-specific application platform: add the employer's actual HirePro URL using **Add opportunity**. No imaginary HirePro job feed is used.
3. In **Job explorer**, select **AI tailor**. It creates a role-specific PDF, a conservative text cover letter from verified facts, and a queue entry.
4. In **Approval queue**, choose **Prepare form** to fill a supported application without submitting. The dedicated persistent project browser opens (see docs/17-project-browser-connections.md). Complete login, OTP, CAPTCHA, custom widgets, consent and questions in that browser. Click **Continue** in the dashboard. The same browser remains open for up to 20 minutes at a pause; it closes on completion, explicit close, or timeout.
5. **Approve & submit** approves that one application. In a preparation session, it allows the final submit. An already-approved session can submit after you complete missing fields and click Continue.

The worker fills contact details and resume uploads using associated labels, accessibility labels, IDs, or recognized contact names. It follows supported Next/Continue steps. It does not guess salary, notice period, experience, eligibility, legal answers or consent. Optional local-model mapping only chooses known contact fact keys; it cannot write invented answers or execute arbitrary code.

## Facts and standard answers

- `config/profile.json`: existing verified profile; no new experience or credentials are invented.
- **Settings → Verified application answers** edits `config/application-answers.json`. Keys are exact question labels, with punctuation normalized for matching. Values are text/numbers or booleans for exact checkboxes. Unknown and custom controls pause for the user.
- Browser sessions are reused from `browser-profiles/project-browser`; personal Chrome profiles are not used.

## Submission gate

`config/application-policy.json` starts with an empty `auto_submit_domains` list. No unattended external submission is enabled by this change. Settings lets you explicitly approve exact employer hostnames and a daily limit (default 15). A shared host such as `jobs.lever.co` includes all employers on that host; there are no wildcard domain rules. The source/domain gate and unknown-answer checks are independent.

The approved-queue endpoint starts only pending, tailored applications whose exact current source hostname is allowlisted. It does not create applications or approve other jobs. One browser runs at a time, including paused sessions. Naukri one-click applications may use the saved portal resume instead of the tailored upload; the user must opt in for that individual application. LinkedIn, Indeed and other discovery-only sources require an employer application link.

## Evidence and retries

The dashboard shows current worker status, missing questions, screenshots, and confirmation text. SQLite execution logs and application attempts persist results; `data/application-runs` stores step logs. Screenshots are in `screenshots`.

Only positive visible confirmation text produces Submitted; no synthetic confirmation ID is generated. An uncertain submit is marked Manual Action Required and automatic retry is blocked. **I checked: not submitted** is a user attestation that permits another attempt after verifying the portal. Submitted applications cannot be reset. A service restart interrupts live browsers and flags in-flight applications for manual verification rather than replaying them.

## Collection and scheduling

Career monitoring collects identifiable JobPosting data and Lever public postings. Other career links and page changes remain reviewable on watchlist cards. Email-only pages, PDF recruitment notices, JavaScript-only lists and blocked sites are not converted to fake jobs. Canonical job URLs have a unique database constraint; tracking parameters are removed for new imports.

Run a full cycle with the server already running:

```powershell
& C:/sukesh/job/.venv/Scripts/python.exe C:/sukesh/job/scripts/automation_cycle.py --score-new
```

It checks the watchlist, searches Naukri for biomedical roles in Chennai, Bengaluru and Visakhapatnam, tailors at most three new technical roles, and processes up to three eligible allowlisted applications. The loop stops when a browser needs the user or a result is still pending. The Codex recurring automation invokes this cycle every six hours while the PC and app are available. Login, security checks, and unknown answers require the user; there is no CAPTCHA bypass or automatic assessment taking.

## Validation and limits

Offline fixtures cover dry-run gating, approved submission with actual confirmation text, unknown questions/consent, resumable login, CAPTCHA, browser launch errors and exact domain matching. API tests use a separate SQLite database and verify deduplication, portal capabilities, submitted-job protection and missing-document checks.

A live Dozee/Lever dry run filled contact fields and attached the master resume, then paused on employer questions without submitting. No real application was submitted during implementation. Naukri discovery returned real public listings. HirePro, Workday, and custom employer forms still require live employer-specific verification; arbitrary forms are not guaranteed to work.

## Official source pages checked

- https://www.lifesigns.us/careers/ and https://www.lifesigns.us/contact/
- https://www.perfinthealthcare.com/careers.php
- https://www.phoenixmedicalsystems.com/career
- https://www.trivitron.com/careers
- https://detecttechnologies.com/current-openings
- https://www.dozeehealth.ai/careers (links to https://jobs.lever.co/dozee)
- https://innaccel.com/careers/
- https://niramai.com/careers
- https://www.janitri.in/company/careers
- https://www.amtz.in/latest-notification/
- https://www.svastek.com/ (links to https://svastek.zohorecruit.in/jobs/Careers)
- https://www.leelabiologics.com/careers
- https://support.hirepro.in/language21hiring/
