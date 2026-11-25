# Full answer evaluation report (Tahap 3)

Pipeline: retriever + extractive provider + citation validator, the same ask_question() path as POST /ask. Questions: 25 (20 answerable, 5 traps) from eval/golden_questions.json.

Score: 25/25 (100%)
GATE (80%): PASS
Answerable passed: 20/20. Traps refused: 5/5.

## Refusal rule: score threshold plus grounding check

A question is refused before any provider is called when its top retrieved chunk scores below 0.65 AND its distinctive words are not demonstrably present in the retrieved text (the grounding check in src/grounding.py, rarity-weighted term coverage over the top 3 chunks). Below the score threshold an answer is still allowed when weighted union coverage is at least 0.6 and the best single chunk covers at least 0.45.

Top scores of the 20 answerable questions: min 0.590, max 0.966.
Top scores of the 5 trap questions: min 0.497, max 0.644.
The score ranges overlap, which is why the score alone is not the whole rule.

Measured grounding (weighted union / weighted best chunk):
- Answerable below the score threshold: "What happens when a customer orders a quantity far above the available" score 0.5899, grounding 0.8356 / 0.8356.
- Answerable below the score threshold: "What risks are listed in the Chaligula test plan, for example about th" score 0.6263, grounding 0.6798 / 0.4951.
- Trap: "Who is the CEO of ParaBank?" score 0.4966, grounding 0.2298 / 0.2298.
- Trap: "What is the production database password used by the Chaligula applica" score 0.5902, grounding 0.5255 / 0.3465.
- Trap: "Which bug was found in the ParaBank forgot password flow that sends an" score 0.6444, grounding 0.1264 / 0.1264.
- Trap: "Which bug report describes a refund to a credit card failing in Chalig" score 0.5449, grounding 0.2611 / 0.2611.
- Trap: "What is the monthly salary of the QA team members who executed these t" score 0.5534, grounding 0.0832 / 0.0832.

## Fix history

First full run (score threshold only): 22/25 (88%), GATE PASS, traps refused 5/5, but two real questions were refused by the threshold and one list question missed its expected source. Fix applied: the grounding rescue above, plus general list handling (wider search, records of the asked type, and the project document chunk that enumerates those same records included as a source; list answers enumerate the records). This run: 25/25 (100%).

## Per-question results

| # | Type | Question | Expected | Top score | Grounding | Result | Detail |
|---|---|---|---|---|---|---|---|
| 1 | answerable | What happens when a customer orders a quantity far above the available stock in  | chaligula:BUG-001 | 0.5899 | 0.8356 / 0.8356 | PASS | ok |
| 2 | answerable | What bug was found when logging in to the ParaBank web application with an inval | parabank:BUG-001 | 0.8769 | 0.637 / 0.637 | PASS | ok |
| 3 | answerable | What happens if a transfer is larger than the source account balance in ParaBank | parabank:BUG-003 | 0.7376 | 0.657 / 0.657 | PASS | ok |
| 4 | answerable | Does Bill Pay in ParaBank actually post the payment to the account after it repo | parabank:BUG-006 | 0.7076 | 1.0 / 0.8217 | PASS | ok |
| 5 | answerable | Why do all products and categories in Chaligula display the same placeholder ima | chaligula:BUG-002 | 0.7837 | 1.0 / 1.0 | PASS | ok |
| 6 | answerable | Which test case covers a customer paying for an order with Xendit, and what orde | chaligula:PAY-TC-001 | 0.8447 | 0.5839 / 0.5839 | PASS | ok |
| 7 | answerable | Which test case checks that the ParaBank homepage loads with the ParaBank title? | parabank:HOME-TC-001 | 0.7647 | 0.8231 / 0.8231 | PASS | ok |
| 8 | answerable | What bugs were found in the ParaBank demo application while executing the tests? | parabank:README-bugs-i-found* | 0.7296 | 1.0 / 1.0 | PASS | ok |
| 9 | answerable | What risks are listed in the Chaligula test plan, for example about the free ser | chaligula:test-plan-risks* | 0.6263 | 0.6798 / 0.4951 | PASS | ok |
| 10 | answerable | What happens when a user tries to update their contact info in ParaBank? | parabank:BUG-007 | 0.7784 | 0.5005 / 0.5005 | PASS | ok |
| 11 | answerable | Which API test case checks login with invalid credentials on the ParaBank API? | parabank:API-AUTH-002 | 0.9003 | 0.8326 / 0.8326 | PASS | ok |
| 12 | answerable | Which SQL test case verifies that a transfer posts exactly one debit and one cre | parabank:DB-TRF-002 | 0.947 | 0.6463 / 0.6463 | PASS | ok |
| 13 | answerable | What happens if a user enters a transfer amount of zero or a negative amount in  | parabank:BUG-002 | 0.6844 | 0.6601 / 0.5767 | PASS | ok |
| 14 | answerable | What happens if a user double-clicks the Transfer button and submits the Transfe | parabank:BUG-004 | 0.7486 | 0.7537 / 0.6601 | PASS | ok |
| 15 | answerable | What error appears when a user submits a transfer with an empty amount in ParaBa | parabank:BUG-005 | 0.7971 | 0.608 / 0.608 | PASS | ok |
| 16 | answerable | What error appears when a user applies for a loan with an empty loan amount in P | parabank:BUG-008 | 0.8173 | 0.5504 / 0.5504 | PASS | ok |
| 17 | answerable | Which SQL test case checks that no product variant stock in Chaligula is negativ | chaligula:DB-STK-001 | 0.9029 | 0.6559 / 0.6559 | PASS | ok |
| 18 | answerable | Which SQL test case checks that the stored order totals in Chaligula match the s | chaligula:DB-ORD-001 | 0.8693 | 0.8959 / 0.8157 | PASS | ok |
| 19 | answerable | Which requirement covers online payment with Xendit in Chaligula, and which test | chaligula:FR-011 | 0.7751 | 0.4654 / 0.4654 | PASS | ok |
| 20 | answerable | How many API test cases were executed for Chaligula in the EXEC-002 session, and | chaligula:EXEC-002 | 0.966 | 0.6735 / 0.6735 | PASS | ok |
| 21 | trap | Who is the CEO of ParaBank? | (refusal) | 0.4966 | 0.2298 / 0.2298 | PASS | refused |
| 22 | trap | What is the production database password used by the Chaligula application? | (refusal) | 0.5902 | 0.5255 / 0.3465 | PASS | refused |
| 23 | trap | Which bug was found in the ParaBank forgot password flow that sends an SMS OTP c | (refusal) | 0.6444 | 0.1264 / 0.1264 | PASS | refused |
| 24 | trap | Which bug report describes a refund to a credit card failing in Chaligula? | (refusal) | 0.5449 | 0.2611 / 0.2611 | PASS | refused |
| 25 | trap | What is the monthly salary of the QA team members who executed these tests? | (refusal) | 0.5534 | 0.0832 / 0.0832 | PASS | refused |
