# Test Plan — Digital Banking (ParaBank)

| Item | Detail |
|---|---|
| Document owner | Tegar |
| Version | 1.0 |
| Status | Active |
| Last updated | 2026-11-23 |
| Companion documents | Test Strategy (`docs/test-strategy.md`), Requirements Specification (`docs/requirements-specification.md`), QA master workbook (`test-cases.xlsx`) |

## 1. Objective

Validate the observable behaviour of the ParaBank public demo's core banking workflows (FR-001..FR-011) through manual testing, API testing, database testing on a local synthetic dataset, and selected UI automation, with all results backed by recorded execution evidence.

## 2. In scope

- Public homepage availability and navigation (FR-010).
- Authentication, registration, and session behaviour (FR-001, FR-002, FR-011).
- Account overview, transfers, bill payment, transaction search (FR-003..FR-006).
- Profile update, loan request, open new account (FR-007..FR-009).
- REST API behaviour for login, accounts, and transfers (Postman collection, `api-testing/`).
- SQL integrity checks on a local synthetic dataset (`database-testing/`).
- UI automation of the homepage, login, and transfer flows (`automation/`).

## 3. Out of scope

- Real banking transactions or any production system.
- Direct validation of the ParaBank server database (not accessible; a synthetic local dataset is used instead).
- Load, stress, penetration, or destructive security testing against the public demo.

## 4. Test approach

Exploratory testing first to learn actual behaviour, then documented scenarios and test cases in the workbook, then execution (manual, API, SQL), with stable high-value flows promoted to Selenium automation and run in CI on every change. Defects are recorded only from observed, reproduced behaviour.

## 5. Environment

- Application: https://parabank.parasoft.com/parabank/index.htm
- Browser: Chrome (headless in CI)
- Automation: Python 3.12 + Selenium + Pytest, Page Object Model
- Reference environment for UI execution: GitHub Actions (see `docs/test-environment.md`)

## 6. Entry criteria

Application reachable; demo account behaviour documented; test cases reviewed in the workbook.

## 7. Exit criteria

Planned tests executed with evidence recorded (workbook Test Execution sheet), defects documented with reproduction steps, and known limitations stated. As of 2026-11-23: 33 UI cases executed (23 Pass, 10 Fail), 8 API cases Pass, 6 SQL cases Pass, 8 defects Open (BUG-001..BUG-008).

## 8. Risks

The public demo may be reset, unavailable, or change without notice (see `docs/risk-assessment.md`, notably RSK-101). Only fictional data and the published demo account are used.
