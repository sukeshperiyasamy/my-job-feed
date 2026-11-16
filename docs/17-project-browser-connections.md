# Dedicated project browser and saved connections

Open **Connections** in the dashboard. **Open project browser** launches a visible Edge/Chrome window with the profile `browser-profiles/project-browser`, separate from personal profiles. The native **Job Hunter Browser** shortcut opens the same profile and starts the local gateway if needed.

## Sign in once

1. Pick a connection and select **Open & sign in**. Create an account or log in on the actual website. Complete OTP, CAPTCHA, passkey and consent steps yourself. Use the site's Remember me option if offered.
2. Return to Connections and select **I'm signed in**. This records your confirmation, not an automatic authentication test.
3. Application workers attach to this same project browser and create a separate application tab. They reuse the site's cookies and local storage within that profile.

Closing a worker tab or restarting the API does not intentionally clear browser data or close the user's project browser. Closing the browser manually retains its profile on disk; reopening reuses it. Website expiry, revocation, security policy, session-only cookies, logout actions, profile deletion or OS/account changes can still require sign-in. No permanent-login guarantee is possible. The project does not bypass verification or periodically refresh sessions behind the user's back.

## Employer accounts

HirePro and Workday often require separate accounts per employer. Use **Add employer / website** to save a distinct named connection with the actual employer portal URL. Greenhouse, Lever and Ashby forms may not need an account at all; no shared global login is assumed. The existing portal-specific profiles remain untouched; they are not imported into the new project profile, so account setup may be needed once here.

The Connections page includes job portals, employer forms, AI-training sites and freelance accounts. These are browser-session connections, not OAuth/API integrations. Account access does not imply an automation adapter exists or permit an application/proposal. Existing submission approval gates remain unchanged. Marketplace proposals, platform assessments and sign-ups remain manual.

## Direct links and shortcuts

The dashboard offers **Copy connection link**. A link such as `http://127.0.0.1:8000/connect/naukri` displays an explicit button that opens the account in the dedicated project browser. GET requests and link previews do not launch browsers. The project browser's home page is `/project-browser`.

`scripts/open_project_browser.py` is the native shortcut target. Windows shortcuts use `pythonw.exe`, so a terminal window is not required. They are shortcuts to this project only, not a change to the Windows default browser.

## Storage and ownership

- Browser account state stays in Chromium's native profile; cookies/passwords are not exported into application JSON.
- `data/connections/accounts.json` stores website URLs, names, open times and user-confirmed sign-in times only.
- `data/project-browser.json` stores process/profile/port metadata. It contains no authentication tokens.
- Browser control listens only on loopback port 9223. Ownership checks require the exact dedicated profile and debugging-port command line. An unrelated listener is rejected; personal browsers are never attached.
- Application workers track only the tab they created and its popups. Opening an unrelated connection tab does not redirect the worker into that account page. Worker cleanup closes its own tabs and disconnects without shutting the shared browser.

## Dependencies and validation

The existing Playwright/requests installation is reused. `requirements-connections.txt` adds psutil for browser process ownership checks.

Regression checks cover separate profile ownership, a blocked foreign debugging port, retained persistent test state across browser reopen, user tab survival after worker cleanup, unrelated-tab isolation, and metadata-only connection confirmation. Test account state uses only local fixture cookies; no real password or account session is inspected.
