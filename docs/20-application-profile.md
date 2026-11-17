# Application Profile and new form questions

Open `http://127.0.0.1:8000/#profile` from the sidebar or the Approval queue.

## Workflow

1. Review **Your application details**. Contact defaults come from the verified master profile. Save changes or add pay, availability, qualifications, experience, address and other details. A custom detail can be added with its exact question label.
2. Prepare an application. The worker fills known contacts and saved answers. Unanswered visible text/select/radio/checkbox fields are captured with their source application and options, and the worker pauses. Optional blank fields also ask; explicitly choose to leave them blank if appropriate.
3. Open **New questions need you**, choose the actual answer and save it. New questions default to **This job only**. Employer/site and global reuse are explicit choices. Shared ATS boards on Lever/Greenhouse/Ashby are scoped to their employer board rather than all employers sharing that hostname.
4. Select **Continue application** to resume a waiting session using freshly loaded answers. This does not grant new submission approval. Existing per-application approval and domain allowlists still govern submission. A session that already attempted submission must be reviewed in the application queue.

Answers can be edited/deleted and given explicit alternate labels. Matching normalizes spacing/case/punctuation but keeps C++ and C# distinct. No semantic guess maps experience, salary, work authorization or consent to a different question. User-saved full name also supplies first/last name fields.

## Boundaries

- Passwords, OTP/security codes, CAPTCHA answers and identity/payment numbers are not stored in the answer bank; complete them on the official website.
- Checkboxes, consent, signatures and declarations use application-only answers. A saved No stays No; a mandatory checkbox may consequently prevent application completion.
- Required fields cannot be intentionally skipped through the question inbox. Optional questions can be saved as leave-blank within the selected scope.
- Uploads and unsupported custom widgets still require the application browser. This page does not implement general document uploading or arbitrary custom-control automation.
- These answers supply application forms. They do not silently rewrite the verified resume facts or enable automatic submission.
- Previously captured questions persist across gateway restarts. Website state still determines whether an old question/form is applicable; review its source link.

## Storage and compatibility

`data/application-profile/answers.json` contains user-provided answers and reuse scopes; `questions.json` contains question metadata/options/source URLs without harvesting field values. Both are excluded from new Git additions. Writes are locked and atomic in the supported single-gateway process.

`config/application-answers.json` remains a legacy exact-label fallback. The new scoped bank takes precedence, including contact overrides. The Settings JSON editor still edits the legacy fallback, not the new bank. Avoid storing conflicting answers in both places.

API: `GET /api/application-profile`, `POST /api/application-profile/answers`, and `DELETE /api/application-profile/answers/{id}`. A captured `question_id` binds the save to its real label, source URL and control type; client substitutions cannot redirect that answer.

Regression coverage includes scope precedence, employer-board separation, false checkbox answers, consent restrictions, required/optional behavior, option validation, secret rejection, aliases, deletion/re-prompting, first/last-name overrides, and the local unknown-question → save → resume → approval-gate workflow. Browser interaction tests mock writes and use fixture personal data; no real application is submitted.
