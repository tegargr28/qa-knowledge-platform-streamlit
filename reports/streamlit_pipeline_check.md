# Streamlit pipeline check

All golden questions run through streamlit_core.answer_question() (the function streamlit_app.py calls), with the app's default session settings (extractive, no key). Scoring rules are the same as eval/run_eval.py.

Score: 25/25
Answerable passed: 20/20. Traps refused: 5/5.

| # | Type | Question | Expected | Top score | Result | Detail |
|---|---|---|---|---|---|---|
| 1 | answerable | What happens when a customer orders a quantity far above the available stock in  | chaligula:BUG-001 | 0.5899 | PASS | ok |
| 2 | answerable | What bug was found when logging in to the ParaBank web application with an inval | parabank:BUG-001 | 0.8769 | PASS | ok |
| 3 | answerable | What happens if a transfer is larger than the source account balance in ParaBank | parabank:BUG-003 | 0.7376 | PASS | ok |
| 4 | answerable | Does Bill Pay in ParaBank actually post the payment to the account after it repo | parabank:BUG-006 | 0.7076 | PASS | ok |
| 5 | answerable | Why do all products and categories in Chaligula display the same placeholder ima | chaligula:BUG-002 | 0.7837 | PASS | ok |
| 6 | answerable | Which test case covers a customer paying for an order with Xendit, and what orde | chaligula:PAY-TC-001 | 0.8447 | PASS | ok |
| 7 | answerable | Which test case checks that the ParaBank homepage loads with the ParaBank title? | parabank:HOME-TC-001 | 0.7647 | PASS | ok |
| 8 | answerable | What bugs were found in the ParaBank demo application while executing the tests? | parabank:README-bugs-i-found* | 0.7296 | PASS | ok |
| 9 | answerable | What risks are listed in the Chaligula test plan, for example about the free ser | chaligula:test-plan-risks* | 0.6263 | PASS | ok |
| 10 | answerable | What happens when a user tries to update their contact info in ParaBank? | parabank:BUG-007 | 0.7784 | PASS | ok |
| 11 | answerable | Which API test case checks login with invalid credentials on the ParaBank API? | parabank:API-AUTH-002 | 0.9003 | PASS | ok |
| 12 | answerable | Which SQL test case verifies that a transfer posts exactly one debit and one cre | parabank:DB-TRF-002 | 0.947 | PASS | ok |
| 13 | answerable | What happens if a user enters a transfer amount of zero or a negative amount in  | parabank:BUG-002 | 0.6844 | PASS | ok |
| 14 | answerable | What happens if a user double-clicks the Transfer button and submits the Transfe | parabank:BUG-004 | 0.7486 | PASS | ok |
| 15 | answerable | What error appears when a user submits a transfer with an empty amount in ParaBa | parabank:BUG-005 | 0.7971 | PASS | ok |
| 16 | answerable | What error appears when a user applies for a loan with an empty loan amount in P | parabank:BUG-008 | 0.8173 | PASS | ok |
| 17 | answerable | Which SQL test case checks that no product variant stock in Chaligula is negativ | chaligula:DB-STK-001 | 0.9029 | PASS | ok |
| 18 | answerable | Which SQL test case checks that the stored order totals in Chaligula match the s | chaligula:DB-ORD-001 | 0.8693 | PASS | ok |
| 19 | answerable | Which requirement covers online payment with Xendit in Chaligula, and which test | chaligula:FR-011 | 0.7751 | PASS | ok |
| 20 | answerable | How many API test cases were executed for Chaligula in the EXEC-002 session, and | chaligula:EXEC-002 | 0.966 | PASS | ok |
| 21 | trap | Who is the CEO of ParaBank? | (refusal) | 0.4966 | PASS | refused |
| 22 | trap | What is the production database password used by the Chaligula application? | (refusal) | 0.5902 | PASS | refused |
| 23 | trap | Which bug was found in the ParaBank forgot password flow that sends an SMS OTP c | (refusal) | 0.6444 | PASS | refused |
| 24 | trap | Which bug report describes a refund to a credit card failing in Chaligula? | (refusal) | 0.5449 | PASS | refused |
| 25 | trap | What is the monthly salary of the QA team members who executed these tests? | (refusal) | 0.5534 | PASS | refused |
