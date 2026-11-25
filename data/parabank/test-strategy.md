# Test Strategy — Digital Banking QA Portfolio

| Item | Detail |
|---|---|
| Project | Digital Banking QA Portfolio |
| Document owner | Tegar |
| Version | 1.0 |
| Last updated | 2026-11-23 |
| Application under test | ParaBank public demo — https://parabank.parasoft.com/parabank/index.htm |
| Companion documents | Test Plan (`docs/test-plans/test-plan.md`), QA master workbook (`test-cases.xlsx`), Risk Assessment (`docs/risk-assessment.md`), Test Environment (`docs/test-environment.md`) |
| Status | Living document; updated as scope and evidence grow |

> This is a learning and demonstration portfolio built against a public demo application. It does not represent testing of a production banking system.

## 1. Objectives

1. Demonstrate end-to-end QA practice on a banking-like application: requirements analysis, test design, manual execution, defect reporting, API testing, SQL testing, UI automation, and CI.
2. Keep every reported result traceable to real execution evidence. Unexecuted work is reported as `Not Run`; results that cannot be verified are reported as `Not Verified`.
3. Build a regression suite that runs unattended in CI (GitHub Actions) and locally (pytest / Jenkins).

## 2. Scope

### In scope (requirements FR-001..FR-011 in the workbook)

- Homepage access and logout/session behaviour (FR-010, FR-011)
- User login and registration (FR-001, FR-002)
- Account overview (FR-003)
- Transfer funds (FR-004)
- Bill payment (FR-005)
- Find transactions (FR-006)
- Update contact info (FR-007)
- Request loan (FR-008)
- Open new account (FR-009)
- ParaBank public REST API equivalents of the above flows
- SQL validation against a **local synthetic dataset only**

### Out of scope

- Load, performance, and security/penetration testing against the public demo service
- Any access to ParaBank's real backend database
- Real customer data, real credentials, or real money movement
- Mobile applications and cross-browser matrices beyond Chrome (may be added later)

## 3. Test levels and types

| Level / type | Approach | Where it lives |
|---|---|---|
| Exploratory testing | Session-based charters per feature; findings feed designed test cases | Workbook: Exploratory Testing sheet |
| System testing (manual) | Designed scenarios and test cases per requirement, positive and negative | Workbook: Test Scenarios, Test Cases |
| API testing | REST checks against the ParaBank demo services; status codes, payload fields, error handling | Workbook: API Test Cases; Postman collection in `api-testing/` |
| Database testing | SQL queries over a local synthetic dataset mirroring banking concepts (accounts, transactions, balances) | Workbook: SQL Test Cases; `database-testing/` |
| UI automation | Selenium + pytest, Page Object Model, headless Chrome | `automation/` |
| Regression | Automated smoke subset on every push/PR in CI; wider manual regression per release of this portfolio | GitHub Actions workflow |
| UAT | Not applicable — demo application, no business users | — |

## 4. Test design techniques

- Equivalence partitioning and boundary value analysis (amounts, dates, loan thresholds)
- Decision tables for transfer/bill-pay field combinations
- Error guessing based on exploratory findings
- State transition thinking for session behaviour (login → active → logout → protected page access)

Business rules are only designed against **after the actual application behaviour has been observed**; assumptions are never written into test cases as facts.

## 5. Entry and exit criteria

**Entry (per feature):** requirement captured in the workbook (FR-xx) with acceptance criteria; test environment reachable; test data available (public demo account or synthetic data).

**Exit (per phase):** all designed cases executed or explicitly deferred with a reason; defects logged with reproducible steps; execution evidence stored (CI run links, reports, screenshots); RTM updated so every requirement shows its real coverage status.

## 6. Defect management

- Defects are recorded in the workbook's Bug Reports sheet with severity, priority, steps to reproduce, expected vs actual result, and environment.
- A defect row is created **only for behaviour actually observed** during execution. Design-time suspicions stay in the Risk Assessment until reproduced.
- Severity guidance: Critical = money movement wrong or data loss; High = core flow blocked; Medium = flow works with workaround or wrong non-critical data; Low = cosmetic.

## 7. Test deliverables

- Test Plan and this Test Strategy
- QA master workbook (`test-cases.xlsx`): Requirements, Test Scenarios, Test Cases, RTM, Bug Reports, Test Execution, API Test Cases, SQL Test Cases, Test Summary
- Automation framework and CI configuration
- Execution evidence: GitHub Actions runs, pytest HTML/JUnit reports, failure screenshots

## 8. Tools

| Purpose | Tool |
|---|---|
| Test management | Excel workbook (project template) |
| UI automation | Python, Selenium WebDriver, pytest, pytest-html |
| API testing | curl / Postman |
| Database testing | SQLite with a local synthetic dataset (`database-testing/`) |
| CI | GitHub Actions; Jenkins (local, Docker Compose) |
| Version control | Git / GitHub |

## 9. Risks and mitigation

See `docs/risk-assessment.md`. The headline risks for this portfolio are demo-data resets on the public ParaBank instance, environment reachability differences between local runs and CI, and the temptation to over-claim — mitigated by the evidence-only reporting rule in section 1.
