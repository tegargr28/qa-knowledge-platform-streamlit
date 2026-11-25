# Interview Preparation — STAR Stories from This Portfolio

Short, honest summaries of the real work in this repository, in Situation–Task–Action–Result form. Everything below is backed by the workbook (`test-cases.xlsx`), the execution records (EXEC-001..EXEC-010), and the GitHub Actions history.

## 1. "Tell me about a bug you found" — BUG-001, login accepts any password

- **Situation:** While automating the login tests for the ParaBank demo, the negative test (wrong password must be rejected) failed in CI.
- **Task:** Determine whether the failure was a test bug or an application bug before recording anything.
- **Action:** Reproduced the behaviour three ways — a manual browser session (wrong password opened the Accounts Overview, no error), an HTTP cross-check (POST to the login endpoint returned a redirect to the overview), and the REST API (the same wrong password was rejected correctly with HTTP 400). Isolated the defect to the web login flow only.
- **Result:** Recorded as BUG-001 (Critical, Open) with steps, expected/actual results and evidence. The automated test is marked `xfail` referencing the bug so CI stays green without hiding the failure, and the workbook keeps the honest Fail.

## 2. "How do you test transfers?" — BUG-002..BUG-004, missing transfer validation

- **Situation:** Executing the designed Transfer Funds cases manually against the live demo (EXEC-008).
- **Task:** Verify valid transfers move money exactly, and probe the invalid-input boundaries: zero, negative, empty, above-balance, and duplicate submission.
- **Action:** Recorded balances before and after every attempt and compared exact deltas. Valid transfers of $10.00 and $10.55 reconciled to the cent (TRF-TC-001/006 Pass). The boundary probes showed: $0.00 accepted; -$50.00 accepted and reversed the money flow; $1454.95 accepted against a $454.95 balance (account ended at -$1000.00); a double-clicked submission posted the same $5.00 transfer twice (verified in the activity list).
- **Result:** Four defects recorded (BUG-002..BUG-005) with severities based on financial impact; the happy path is also covered by a Selenium test that asserts exact balance deltas on both accounts.

## 3. "How do you verify API results beyond status codes?" — EXEC-006

- **Situation:** API test cases for the ParaBank REST API, executed with curl and captured in a Postman collection.
- **Task:** Prove a transfer actually moved money, not just that the endpoint returned 200.
- **Action:** Read both accounts' balances before the POST, executed the transfer, then re-read both accounts and checked the deltas matched the amount exactly (source -$10.00, destination +$10.00).
- **Result:** API-TRF-001 passed with balance-level evidence. A same-day re-check of a login case also exposed that the shared demo data had changed underneath the tests — recorded honestly as a note (risk RSK-101) instead of rewriting the earlier result.

## 4. "What do you do when you can't access the real database?" — SQL testing, EXEC-007

- **Situation:** ParaBank does not expose its database, so claiming SQL results against it would be fabrication.
- **Task:** Still demonstrate database testing skills — referential integrity, reconciliation, duplicate detection — with real executions.
- **Action:** Built a small synthetic banking dataset in SQLite (fictional customers, accounts, transfers) with the expected invariants documented in the seed file, then wrote one check query per test case and a runner that builds the dataset fresh and reports actual outputs.
- **Result:** All 6 SQL cases executed and passed (EXEC-007), and each check has a defined failure mode, so a future data change that breaks an invariant fails loudly. The README states plainly that the dataset is simulated.

## 5. "Why do you verify beyond the confirmation page?" — BUG-006, the payment that never happened

- **Situation:** Testing Bill Pay, the result page announced "Bill Payment … was successful" for a $5.00 payment.
- **Task:** Confirm the payment actually happened, not just that the message appeared.
- **Action:** Compared the source account's activity list and balance immediately before and after the payment — no $5.00 entry, no balance change. Repeated with $99,999.00 against an $810.00 balance: again "successful", again nothing posted, showing there is also no funds check. The form's own validations (mismatched account numbers, empty amount) were verified separately and do work.
- **Result:** Recorded as BUG-006 (Critical): the success message cannot be trusted because the posting step silently does nothing. The case's expected result had been written to require both the confirmation *and* the ledger entry, which is exactly what caught it.

## 6. "How do you keep a portfolio honest?"

- Statuses are recorded only after real execution; unexecuted work stays **Not Run**. While Bill Payment, Update Contact Info, Request Loan, and Open New Account were still unexplored, that gap was written down in the RTM instead of being papered over — and closed later by exploring the features first and only then designing cases (Phase 6).
- When the demo environment blocked a test, it was recorded as **Blocked** with the reason, not quietly dropped.
- Every reported number traces to an execution record (EXEC-xxx) or a CI run.
