# Software Requirements Specification — Digital Banking QA Portfolio

| Item | Detail |
|---|---|
| Document owner | Tegar |
| Version | 1.0 |
| Status | Active |
| Last updated | 2026-11-23 |
| Application under test | ParaBank public demo — https://parabank.parasoft.com/parabank/index.htm |

## 1. Purpose

This document specifies the functional requirements that the QA portfolio verifies. The requirements describe the **observable behaviour** of the ParaBank public demo application; they were derived from the application's user interface and public documentation, not from access to any production banking system.

## 2. Scope

In scope: the eleven functional requirements FR-001 to FR-011 below, covering the customer-facing workflows of the demo application. Out of scope: performance, penetration testing, and any behaviour that requires administrator or back-end access to the demo.

The authoritative test-management record for these requirements is the QA master workbook (`test-cases.xlsx`, Requirements and RTM sheets). This document and the workbook are kept consistent; if they ever disagree, the workbook's execution evidence takes precedence and this document is corrected.

## 3. Functional requirements

| ID | Feature | Requirement |
|---|---|---|
| FR-001 | User Login | A registered user shall be able to log in with a valid username and password and be taken to the Accounts Overview. |
| FR-002 | User Registration | A visitor shall be able to register a new account using fictional personal data and then log in with the new credentials. |
| FR-003 | Account Overview | After login, the user shall see all of their accounts with account number, type and balance. |
| FR-004 | Transfer Funds | A logged-in user shall be able to transfer funds between their own accounts, and both balances shall update consistently. |
| FR-005 | Bill Payment | A logged-in user shall be able to pay a bill to a payee with a valid amount from a selected account. |
| FR-006 | Find Transactions | A logged-in user shall be able to find transactions by criteria such as date range or amount. |
| FR-007 | Update Contact Info | A logged-in user shall be able to update their contact information and see the change reflected in their profile. |
| FR-008 | Request Loan | A logged-in user shall be able to request a loan and receive a clear approval/decline decision based on the demo rules. |
| FR-009 | Open New Account | A logged-in user shall be able to open a new checking or savings account. |
| FR-010 | Homepage Access | The ParaBank homepage shall be publicly accessible and identify the application. |
| FR-011 | Logout & Session | A logged-in user shall be able to log out; after logout, protected pages shall require authentication again. |

## 4. Validation status (as of 2026-11-23)

All eleven requirements have been exercised by executed test cases (see the workbook RTM). Eight requirements behave as specified. Three requirements are affected by open defects:

| Requirement | Status | Linked defects |
|---|---|---|
| FR-001 | Validated with defect | BUG-001 — an invalid password is accepted by the web login |
| FR-004 | Validated with defects | BUG-002, BUG-003, BUG-004, BUG-005 — amount validation and duplicate-submission defects |
| FR-005 | Validated with defect | BUG-006 — payment reported successful but never posted |
| FR-007 | Validated with defect | BUG-007 — profile updates always fail with a generic error |
| FR-008 | Validated with defect | BUG-008 — empty loan amount returns a generic error |
| FR-002, FR-003, FR-006, FR-009, FR-010, FR-011 | Validated | — |

## 5. Constraints and assumptions

- The demo application and its data are controlled by Parasoft and may be reset or changed without notice (see Risk Assessment, RSK-101). Account IDs, balances, and displayed names are therefore never treated as stable requirement data.
- Only fictional data and the published public demo account are used. No real personal or financial data appears anywhere in this project.
- A requirement is marked *Validated* only after at least one linked test case has been executed with recorded evidence (workbook, Test Execution sheet).

## 6. References

- Test Strategy — `docs/test-strategy.md`
- Test Plan — `docs/test-plans/test-plan.md`
- QA master workbook (Requirements, Test Scenarios, Test Cases, RTM) — `test-cases.xlsx`
- Risk Assessment — `docs/risk-assessment.md`
