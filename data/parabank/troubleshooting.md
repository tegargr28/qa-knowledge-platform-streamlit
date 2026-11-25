# Troubleshooting Guide

| Item | Detail |
|---|---|
| Document owner | Tegar |
| Version | 1.0 |
| Status | Active |
| Last updated | 2026-11-23 |

Each entry follows the same format: **Symptom → Cause → Resolution**. All entries are drawn from issues actually encountered while building this portfolio.

## 1. Smoke test errors locally with a driver/session error

- **Symptom:** `pytest` fails before any assertion, while creating the browser session.
- **Cause:** No matching Chrome/ChromeDriver pair in the local environment; the original factory assumed a locally installed driver.
- **Resolution:** The driver factory (`automation/utils/driver_factory.py`) is configuration-driven and creates a headless-capable Chrome session. In restricted environments, run the suite in CI instead (see entry 2).

## 2. Tests cannot reach ParaBank from a local or sandboxed network

- **Symptom:** Page loads time out locally, while the same tests pass in GitHub Actions.
- **Cause:** The local network or proxy blocks the demo site; the application itself is up.
- **Resolution:** Treat GitHub Actions as the reference execution environment (recorded as EXEC-002 *Blocked* locally vs EXEC-003 *Pass* in CI). Verify application availability with a lightweight HTTP check before concluding the site is down.

## 3. A test passes one day and fails the next with different account data

- **Symptom:** Balances, account IDs, or even the account holder's displayed name differ between runs.
- **Cause:** The ParaBank demo data is reset or changed by its operator without notice (Risk Assessment, RSK-101).
- **Resolution:** Never hard-code IDs or balances. Read values at runtime and assert exact *deltas* (for example, source −10.00 and destination +10.00 after a 10.00 transfer), as the transfer test does.

## 4. Accounts Overview table is empty immediately after login

- **Symptom:** Assertions on account rows fail intermittently right after logging in.
- **Cause:** The overview table is populated asynchronously; the page shell renders before the data.
- **Resolution:** Wait explicitly for table rows to appear (`AccountsOverviewPage` does this). Do not replace the wait with a fixed sleep.

## 5. Transfer test has fewer than two accounts to work with

- **Symptom:** After login, no transfer counterpart can be selected, even though the overview lists two accounts.
- **Cause:** The demo login's data varies between resets. Sometimes it holds a single account; after one reset it held a checking account plus a **loan account**, and loan accounts appear on the Accounts Overview but are not offered by the Transfer Funds form, so selecting one fails.
- **Resolution:** The test reads the account IDs the transfer form actually offers and picks the pair from those. If fewer than two are offered, it opens a savings account through the UI as part of its setup (Open New Account), then proceeds. The same setup approach was used in manual execution (EXEC-008).

## 6. AUTH-TC-002 reports "xfailed" — is the suite broken?

- **Symptom:** CI output shows one expected failure.
- **Cause:** The application accepts an invalid password in the web login (defect BUG-001). The test correctly asserts rejection, so it currently fails against the real application.
- **Resolution:** Nothing to fix in the test. The `xfail` marker keeps the defect visible without blocking the pipeline; if ParaBank fixes the login, the test reports XPASS and the marker is removed.

## 7. Bill Pay shows "successful" but the balance does not change

- **Symptom:** The confirmation message claims success, yet no activity entry appears and the balance is unchanged.
- **Cause:** Application defect, not a test problem — recorded as BUG-006 (Critical).
- **Resolution:** Verify payments by before/after balance and activity reads, never by the confirmation message alone. The defect is documented in `test-cases.xlsx`; no test-code workaround is applied.

## 8. References

- Automation Guide — `docs/automation-guide.md`
- CI/CD Documentation — `docs/ci-cd.md`
- Risk Assessment (RSK-101, demo data resets) — `docs/risk-assessment.md`
- Defect records BUG-001..BUG-008 — `test-cases.xlsx`, Bug Reports sheet
