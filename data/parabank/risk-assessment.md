# Risk Assessment — Digital Banking QA Portfolio

| Item | Detail |
|---|---|
| Project | Digital Banking QA Portfolio |
| Document owner | Tegar |
| Version | 1.0 |
| Status | Active |
| Last updated | 2026-11-23 |
| Application under test | ParaBank public demo |
| Method | Risks are reviewed at each phase. A risk becomes a defect only when the underlying behaviour is actually observed and reproduced. |

## Product risks (application behaviour to probe)

| ID | Area | Risk | Impact if present | Likelihood | Mitigation / test response |
|---|---|---|---|---|---|
| RSK-001 | Authentication | Invalid credentials accepted, or valid credentials rejected | Critical | Low | Positive and negative login cases (AUTH-TC-001, AUTH-TC-002); API equivalents |
| RSK-002 | Session | Protected pages remain accessible after logout | High | Medium | Session cases SESS-TC-001/002: logout, then direct navigation and back-button checks |
| RSK-003 | Transfer funds | Transfer succeeds with insufficient funds, or balances update incorrectly | Critical | Medium | Boundary and negative amount cases; balance before/after comparison (TRF-TC-002..004) |
| RSK-004 | Transfer funds | Same-account transfer (from = to) is not rejected | Medium | Medium | TRF-TC-005 decision case |
| RSK-005 | Amounts | Zero, negative, or non-numeric amounts are processed instead of rejected | High | Medium | Negative cases across Transfer and Bill Pay (TRF-TC-003) |
| RSK-006 | Bill payment | Payment is recorded without a payee or with an unverified account number | High | Medium | Bill Pay cases under SCN-010 (in design) |
| RSK-007 | Data display | Account overview or transaction history shows another customer's data | Critical | Low | Account isolation checks in exploratory sessions EXP-002 follow-ups |
| RSK-008 | Loan request | Loan approved above reasonable limits or with invalid down payment | Medium | Unknown — behaviour not yet observed | Explore first (FR-008); design cases only from observed rules |
| RSK-009 | Registration | Duplicate username or incomplete profile is accepted | Medium | Medium | Registration cases to be designed after exploration (FR-002) |

## Project risks (portfolio execution)

| ID | Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|---|
| RSK-101 | ParaBank demo data resets periodically, so account/customer IDs in evidence change between runs | Evidence appears inconsistent | High | Record execution dates and run IDs with every result; note the reset behaviour in the workbook; assert on behaviour, not on fixed IDs, in automation |
| RSK-102 | Local network restrictions block browser access to the application while CI can reach it (observed 2026-11-23) | Local UI executions recorded as Blocked | Medium | Treat CI (GitHub Actions) as the reference UI execution environment; keep local Blocked records as environment history, not application results |
| RSK-103 | Public demo is unavailable or changes without notice | Executions blocked; locators break | Medium | Keep automation locators in Page Objects so fixes are single-point; record outages as Blocked with evidence |
| RSK-104 | Results are over-claimed (unexecuted tests reported as passed) | Portfolio credibility destroyed | Low | Evidence-only rule: statuses change only with an execution record (EXEC-xx) or CI run link; RTM shows coverage gaps openly |
| RSK-105 | Credentials or sensitive data are committed to the repository | Security incident; portfolio rejected | Low | Only the published public demo account is used; `.env` is gitignored; a secret check runs before every publication |

## Review log

| Date | Change |
|---|---|
| 2026-11-23 | Initial assessment created with Phase 2 documentation. RSK-102 recorded from the observed local-execution limitation (workbook EXEC-002) and its CI resolution (EXEC-003). |
