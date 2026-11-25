# Digital Banking QA Portfolio

[![QA Smoke Tests](https://github.com/tegargr28/digital-banking-qa/actions/workflows/qa-smoke.yml/badge.svg)](https://github.com/tegargr28/digital-banking-qa/actions/workflows/qa-smoke.yml)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![Selenium](https://img.shields.io/badge/Selenium-WebDriver-green)
![Pytest](https://img.shields.io/badge/Pytest-automation-orange)

This is my QA portfolio project. I tested the ParaBank public demo banking app end to end: writing requirements and test cases, running the tests manually, reporting the bugs I found, and automating the most important flows so they run in CI on every change.

Everything reported here comes from tests I actually ran. Test cases that have not been executed are marked Not Run in the workbook, and all test data is fictional.

Application under test: https://parabank.parasoft.com/parabank/index.htm

My GitHub profile: https://github.com/tegargr28

## Results at a glance

| Area | Result |
|---|---|
| Requirements | 11 (FR-001 to FR-011), all validated by executed tests |
| Test scenarios | 13 (SCN-001 to SCN-013) |
| UI test cases executed | 33, with 23 Pass and 10 Fail |
| API test cases executed | 8, all Pass |
| SQL test cases executed | 6, all Pass |
| Defects found | 8 in total: 3 Critical, 3 High, 2 Low |
| Execution records | 10 sessions (EXEC-001 to EXEC-010) |
| Automation | 4 Selenium tests running in CI, green on every merge to main |

The full detail is in the workbook [test-cases.xlsx](test-cases.xlsx). It has separate sheets for requirements, scenarios, test cases, the traceability matrix, bug reports, execution records, and the API and SQL cases.

## What this project covers

| Skill | Where to see it |
|---|---|
| Test design | 13 scenarios and 47 test cases (positive, negative, and boundary), each traced to a requirement in the RTM |
| Manual testing | All 33 UI cases executed across the 9 main features of the app |
| Bug reporting | 8 defect reports with reproduction steps, expected and actual results, severity, and priority |
| API testing | Postman collection for the ParaBank REST API, with transfer results checked against the exact balance changes |
| SQL testing | A local synthetic banking dataset in SQLite, checked for integrity, reconciliation, and duplicates |
| Test automation | Python and Selenium with Pytest, Page Object Model, headless Chrome, and a screenshot on failure |
| CI/CD | GitHub Actions runs the automated tests on every pull request, and code is only merged when the run is green |
| Documentation | Requirements spec, test strategy, test plan, automation guide, CI/CD notes, and a troubleshooting guide |

## Bugs I found

These are real defects in the demo application, found while executing the test cases above. Each one is documented in the Bug Reports sheet of the workbook with the steps to reproduce it.

| ID | Severity | What happens |
|---|---|---|
| BUG-001 | Critical | The web login accepts a wrong password and still opens the Accounts Overview. The REST API rejects the same password correctly, so the problem is in the web login. |
| BUG-002 | High | Transfers of zero or negative amounts go through. A negative amount even moves the money in the opposite direction. |
| BUG-003 | Critical | A transfer larger than the balance is accepted, and the account ends up at -$1,000.00. |
| BUG-004 | High | Clicking the Transfer button twice posts the same transfer twice. |
| BUG-005 | Low | Submitting a transfer with an empty amount shows a generic internal error instead of a validation message. |
| BUG-006 | Critical | Bill Pay says the payment was successful, but the payment is never posted. The balance does not change and nothing appears in the account activity. It also accepts amounts far above the balance. |
| BUG-007 | High | Saving the Update Contact Info form always ends in a generic internal error, and the changes are never saved. |
| BUG-008 | Low | Submitting a loan request with an empty amount shows the same generic internal error instead of a validation message. |

Short STAR summaries of the most interesting findings are in [docs/interview-prep.md](docs/interview-prep.md).

## Repository layout

| Path | Contents |
|---|---|
| test-cases.xlsx | The QA workbook: requirements, scenarios, test cases, RTM, bug reports, execution records |
| automation/ | Selenium UI tests using the Page Object Model (homepage, login, transfer) |
| api-testing/ | Postman collection and API testing notes |
| database-testing/ | Synthetic SQL dataset, the test queries, and the runner script |
| docs/ | Project documentation (see the index below) |
| .github/workflows/ | The GitHub Actions pipeline |
| Jenkinsfile, docker-compose.yml | Jenkins pipeline and a local Jenkins setup, as an alternative to GitHub Actions |

## Running the automated tests

You need Python and Google Chrome installed. On Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pytest -m smoke
```

To run headless, the same way CI does, and get an HTML report:

```powershell
$env:HEADLESS="true"
pytest -m smoke --html=reports/report.html --self-contained-html
```

Settings are read from environment variables; see .env.example for the list. Please only use the public demo account and fictional data, and do not run load or security tests against the public service.

## Documentation

| Document | What it is for |
|---|---|
| [docs/requirements-specification.md](docs/requirements-specification.md) | The 11 functional requirements and their validation status |
| [docs/test-strategy.md](docs/test-strategy.md) | Overall test approach, test levels, and tools |
| [docs/test-plans/test-plan.md](docs/test-plans/test-plan.md) | Scope, approach, and entry and exit criteria |
| [docs/test-scenarios/test-scenarios.md](docs/test-scenarios/test-scenarios.md) | Index of the 13 test scenarios (the workbook is the main record) |
| [docs/risk-assessment.md](docs/risk-assessment.md) | Product and project risks |
| [docs/test-environment.md](docs/test-environment.md) | Test environments and test data rules |
| [docs/automation-guide.md](docs/automation-guide.md) | How the automation is structured and how to run it |
| [docs/ci-cd.md](docs/ci-cd.md) | The pipeline, its reports, and the merge rules |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Problems I ran into while building this, and how I solved them |
| [api-testing/README.md](api-testing/README.md) | Postman collection and API execution notes |
| [database-testing/README.md](database-testing/README.md) | The synthetic dataset and the SQL test results |
| [docs/interview-prep.md](docs/interview-prep.md) | STAR summaries of the key findings |

## How the project was built

| Phase | What was done |
|---|---|
| 0. Audit | Reviewed the starter repository and listed what was missing |
| 1. Automation foundation | Fixed the browser setup so tests run headless, added failure screenshots, built the QA workbook, CI green |
| 2. Documentation and login tests | Wrote the test strategy, risk assessment, and environment docs; automated the login tests and found BUG-001 |
| 3. API testing | Built the Postman collection and executed all 8 API cases |
| 4. SQL and full UI execution | Ran the 6 SQL cases on a synthetic dataset, then executed the remaining UI cases and found BUG-002 to BUG-005 |
| 5. Transfer automation | Automated the valid transfer case, checking the exact balance change on both accounts |
| 6. Remaining features | Tested Bill Pay, Update Contact Info, Request Loan, and Open New Account; found BUG-006 to BUG-008 |
| 7. Documentation | Added the requirements spec, automation guide, CI/CD, and troubleshooting documents |

## A note on honesty

This is a learning portfolio, not production banking work. The application is a public demo run by Parasoft, and its data is reset from time to time, which is why the tests never rely on fixed account numbers or balances. I have kept the results exactly as they came out, including the failures, because the failures are where the interesting findings are.
