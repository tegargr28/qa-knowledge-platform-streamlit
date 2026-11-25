# Test Plan — CHALIGULA QA Phase 1

**Project:** CHALIGULA e-commerce web app (live deployment)
**Web:** https://chaligula.netlify.app
**API:** https://chaligula-api.vercel.app
**Phase dates:** 25 November 2026
**Tester:** Tegar

## Objective

Verify that the live CHALIGULA deployment works as a shop: visitors can browse the catalog, customers can register, log in, manage addresses and place orders, and admin functions are protected. Record everything in the project workbook with real execution results only.

## Scope

In scope for Phase 1:

- Homepage and product catalog (8 seeded products, 4 categories)
- Product detail pages and variant selection (size, colour, stock)
- Registration and login, including negative cases
- Shopping bag behaviour (kept in the browser; there is no cart API)
- Saved addresses and order placement through the API
- Order history
- Admin access control at API level
- Search and category filtering at API level

Out of scope for Phase 1:

- Payment completion. The deployment uses placeholder Midtrans keys, so orders remain PENDING. Payment cases are written as Blocked and move to Phase 2 when sandbox keys are installed. (Phase 2 update, 25 November 2026: the shop switched to Xendit test mode and PAY-TC-001 was executed and passed — see EXEC-004 in the workbook.)
- Direct database testing. SQL cases are designed in the workbook and will be executed in Phase 2 with read-only access to the Neon database.
- Performance and load testing.
- Real product photography checks. The seed data uses one sample image for all products (logged as BUG-002).

## Approach

- Manual UI testing in a real browser session against the live site, using the seeded demo customer account.
- API testing with scripted requests against the live API, covering positive, negative and authorization cases. Raw results are kept in `reports/api-execution-results.json`.
- Automation with pytest: API tests with requests, UI smoke tests with Playwright. The suite repeats the most important manual checks so regressions can be caught quickly.
- Exploratory sessions to discover the real API contract (endpoints, required fields, error messages). Findings are converted into documented test cases.

## Test data

- Seeded demo accounts that ship with the app: a demo customer and a demo admin.
- Synthetic accounts and addresses created only for testing (for example qa.phase1.tester@example.com).
- No real customer data exists in this system and none is used.

## Entry and exit criteria

Entry: the deployment is live, the seeded catalog and demo accounts are in place, and the API answers its health check.

Exit: all in-scope cases are executed or explicitly marked Not Run or Blocked with a reason; every failure is logged as a defect with reproduction steps; the workbook, the automation suite and the execution evidence agree with each other.

## Risks

- The free serverless tier is slow on cold starts, which can look like a timeout in a test client. Executions use generous timeouts and re-runs before any failure is recorded.
- The sandbox used for automation blocks local browser traffic through its proxy, so Playwright runs may be blocked there while the same suite works on a normal network. Blocked runs are recorded as blocked, never as passed.
