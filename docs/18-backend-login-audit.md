# Backend and login audit — 17 November 2026

Scope: gateway routes, connection metadata, dedicated browser lifecycle, application preparation/approval/retry controls, collectors, opportunity catalog, and dashboard integration. This is a targeted code and regression audit, not a guarantee that every external portal works.

## Fixed

- Preparation-only mode could click an ambiguous one-click Apply action when explicit approval was supplied. It now stops at the gate, including no-form entry buttons.
- Submission was recorded after clicking. A timeout after a server accepted the click could therefore look safe to retry. Submission uncertainty is now checkpointed before potentially submitting buttons; the session persists that checkpoint and retains it after an unexpected worker exception.
- An ambiguous Apply click could erase its attempted flag merely because inputs appeared. It now requires portal review instead of assuming no submission occurred.
- Tailoring could replace documents for an applying/submitted application and reset the job's status. Those states now reject replacement with HTTP 409.
- Failure to copy the worker's compatibility resume was silently ignored. Copy failures now fail the operation rather than reporting a ready application with a missing/stale worker document.
- Invalid watchlist URLs raised an internal error. They now return HTTP 422. Canonical job/career URLs reject embedded credentials and malformed ports; connection URLs reject malformed ports and blank account names.
- The overview always claimed one active worker and listed an outdated AI engine. It now counts the actual application session and labels the configured fallback order without claiming those engines were health-tested.

## Validation

52 regression checks passed across `test_form_worker.py` (13), `test_operations_api.py` (15), `test_connections_api.py` (7), `test_project_browser.py` (2), `test_opportunity_catalog.py` (11), `test_dashboard_ui.py` (3), and `test_connections_ui.py` (1). Changed Python services/scripts also passed compilation.

Browser checks use a separate local fixture profile: persistent test cookies survive browser reopen, user tabs survive worker cleanup, unrelated tabs are excluded, and an unrelated debugging-port listener is rejected. Application tests use local forms or mocked workers/collectors; no real application is sent. API tests use temporary databases.

## Remaining limits

- At the live audit check, the project browser was closed and zero connections had user-confirmed sign-in metadata. Actual Naukri, Google, HirePro, Workday and other account authentication has not been verified.
- “I'm signed in” records the user's confirmation; it is not an automatic login check. Browser data is reused, but sites control expiry, OTP, CAPTCHA and revocation. Permanent sign-in cannot be guaranteed.
- Connections are persistent browser access, not OAuth/API integrations. Several added boards remain browser-only. Public search does not prove a listing is still open; research/job reports require fresh source verification.
- The form worker supports standard controls and pauses for unknown answers/custom widgets. Every portal's real login, upload and submit flow still needs a reviewed trial. No unattended domains were configured at the policy inspection.
- Runtime application/collection coordination assumes one gateway process; do not run multiple Uvicorn workers or replicas against the same browser/database. Restart recovery marks interrupted applications for manual review.
- Dashboard health means the gateway/database query succeeded. It does not verify external portal availability, account authentication or AI-provider health. Starlette currently emits a TestClient/httpx deprecation warning; the tests pass.
