# CHALIGULA QA — Phase 1

This is my QA portfolio project for CHALIGULA, an e-commerce web app I deployed myself. The shop is live, and every test in this project runs against the real deployment, not a local copy.

- Web shop: https://chaligula.netlify.app
- API: https://chaligula-api.vercel.app
- App repository: https://github.com/tegargr28/chaligula

## What is in here

- `test-cases.xlsx` — the main workbook. Requirements, test scenarios, manual test cases, API test cases, SQL test cases (designed, execution planned), bug reports, traceability matrix, execution log and a summary sheet. It uses the same workbook format as my digital banking QA project.
- `api-testing/run_api_tests.py` — the script I used for the first API execution round. It calls the live API and writes the raw results to `reports/api-execution-results.json`.
- `automation/` — a pytest suite. API tests use requests, UI smoke tests use Playwright. See `automation/README.md` for how to run it.
- `reports/` — execution evidence: raw API results, pytest output and a JUnit report.
- `docs/test-plan.md` — the short test plan for this phase.
- `build_workbook.py` — the script that builds the workbook from my template, so the numbers in it can be reproduced.

## Phase 1 results (25 November 2026)

- Manual UI testing in a real browser session: login, product page, bag and logout work. 7 cases passed, 1 failed (see BUG-002).
- API testing: 29 cases executed. 28 passed, 1 failed (BUG-001).
- Automation: 26 API tests in the pytest suite — 25 passed and 1 expected failure that documents BUG-001. The 4 UI smoke tests are written and mirror the manual session; they could not run inside my sandbox because its proxy blocks the local browser, so their status is recorded honestly as blocked there. The same checks passed when I ran them manually in a browser.
- Payment testing is blocked for now. The deployment still uses placeholder Midtrans keys, so orders stay in PENDING status. That is planned for Phase 2, together with the SQL test execution.

## Phase 2 results (25 November 2026)

- Online payment now runs on Xendit test mode. The shop was switched from Midtrans to Xendit (the old Midtrans account could not be recovered), the test-mode keys are installed on the server, and checkout redirects to a Xendit hosted invoice page.
- PAY-TC-001 executed and passed end to end: order CHG-MWV5GGWP-8715 (Rp415.000) was paid with a simulated BCA virtual account payment, the Xendit webhook set the order and the payment to PAID, and the result was verified again through the API (EXEC-004 in the workbook). Test mode only — no real money was involved.
- Still open: the 4 SQL cases are designed but not executed yet, and BUG-001 and BUG-002 are still open.

## Defects found

- BUG-001 (Medium): ordering a quantity far above the available stock returns HTTP 500 "Internal server error" instead of a clean validation message. The order itself is correctly not created.
- BUG-002 (Low): every product and category shows the same placeholder image, because the seed data uses one sample image URL for all of them.

## Test data

The tests use the seeded demo accounts that ship with the app (a demo customer and a demo admin) plus synthetic accounts created only for testing, such as qa.phase1.tester@example.com. No real customer data is involved anywhere.

Security note (25 November 2026): the demo admin password was changed and is not published anywhere anymore. The API runner and the automation suite read it from the CHALIGULA_ADMIN_PASSWORD environment variable and skip the admin cases when it is not set. The demo customer account stays public on purpose, so anyone can still try the shop.
