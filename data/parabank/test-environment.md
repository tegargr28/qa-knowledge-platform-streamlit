# Test Environment — Digital Banking QA Portfolio

| Item | Detail |
|---|---|
| Project | Digital Banking QA Portfolio |
| Document owner | Tegar |
| Version | 1.0 |
| Status | Active |
| Last updated | 2026-11-23 |
| Principle | No real banking systems, credentials, or data are used anywhere in this project. |

## Application under test

| Item | Value |
|---|---|
| Application | ParaBank (Parasoft public demo) |
| Base URL | https://parabank.parasoft.com/parabank/index.htm |
| REST API base | https://parabank.parasoft.com/parabank/services/bank |
| Test account | Public demo account published by Parasoft (`john` / `demo`), overridable via `PARABANK_USERNAME` / `PARABANK_PASSWORD` environment variables |
| Data note | Demo data resets periodically; IDs observed in one run may differ in the next. Results are recorded with dates and run IDs. |

## Execution environments

| Environment | Used for | Stack | Evidence |
|---|---|---|---|
| GitHub Actions (reference for UI automation) | Smoke suite on every push to `main` and every pull request | ubuntu-latest, Python 3.12, Chrome (headless, `--headless=new`) | Workflow run pages; HTML/JUnit report uploaded as the `pytest-report` artifact |
| Local Windows workstation | Manual testing, exploratory sessions, local automation runs | Windows, Chrome, Python venv | Workbook execution records; screenshots in `screenshots/` (gitignored) |
| Local Linux sandbox (development) | Workbook generation, API checks with curl, automation development | Python 3.12, Chrome for Testing (headless) | Workbook execution records EXEC-001/EXEC-002 |

Known environment limitation (observed 2026-11-23): browser traffic from the Linux development sandbox cannot reach the application (proxy tunnel failure), so UI executions from that sandbox are recorded as **Blocked — environment**, never as application results. UI execution evidence comes from GitHub Actions CI (EXEC-003).

## Configuration

Configuration is environment-driven; nothing sensitive is committed.

| Variable | Default | Purpose |
|---|---|---|
| `BASE_URL` | ParaBank index URL above | Application entry point |
| `BROWSER` | `chrome` | Browser for Selenium runs |
| `HEADLESS` | `false` locally; `true` in CI and Jenkins | Headless Chrome in unattended runs |
| `PARABANK_USERNAME` / `PARABANK_PASSWORD` | Public demo account | Login automation credentials |

`.env.example` documents the variables; a real `.env` file is gitignored and must never be committed.

## Test data

- **UI/API:** the public demo account and data created inside the demo application only.
- **SQL:** a local synthetic dataset (`database-testing/`) that mirrors banking concepts — customers, accounts, transactions — with fully fictional values. There is no connection to any real bank database.

## Entry checklist for an execution session

1. Application reachable (HTTP 200 on the base URL).
2. Correct environment and browser recorded for the execution record.
3. Test data available (demo account login works, or synthetic dataset loaded).
4. Previous execution records reviewed so re-runs are labelled as such.
