# Retrieval evaluation report

Embedding provider: sentence-transformers (sentence-transformers/all-MiniLM-L6-v2), 321 chunks indexed.
Scoring mode: hybrid (vector + keyword bonus). Questions: 12 (fixed set in eval/retrieval_questions.json, run against the retriever only).

Hit@1: 7/12 (58%)
Hit@5: 11/12 (92%)

| # | Question | Expected | Top 1 returned | Hit@1 | Hit@5 |
|---|---|---|---|---|---|
| 1 | What happens when a customer orders a quantity far above the available stock in Chaligula? | chaligula:BUG-001 | chaligula:BUG-001 | yes | yes |
| 2 | What bug was found when logging in to the ParaBank web application with an invalid password? | parabank:BUG-001 | parabank:BUG-001 | yes | yes |
| 3 | What happens if a transfer is larger than the source account balance in ParaBank? | parabank:BUG-003 | parabank:BUG-003 | yes | yes |
| 4 | Does Bill Pay in ParaBank actually post the payment to the account after it reports success? | parabank:BUG-006 | parabank:BUG-006 | yes | yes |
| 5 | Why do all products and categories in Chaligula display the same placeholder image? | chaligula:BUG-002 | chaligula:BUG-002 | yes | yes |
| 6 | Which test case covers a customer paying for an order with Xendit, and what order status is expected after the payment completes? | chaligula:PAY-TC-001 | chaligula:PAY-TC-001 | yes | yes |
| 7 | Which test case checks that the ParaBank homepage loads with the ParaBank title? | parabank:HOME-TC-001 | parabank:FR-010 | no | yes |
| 8 | What bugs were found in the ParaBank demo application while executing the tests? | parabank:README-bugs-i-found* | parabank:automation-guide-6-design-rules | no | no |
| 9 | What risks are listed in the Chaligula test plan, for example about the free serverless tier? | chaligula:test-plan-risks* | chaligula:test-plan-test-plan-chaligula-qa-phase-1 | no | yes |
| 10 | What happens when a user tries to update their contact info in ParaBank? | parabank:BUG-007 | parabank:FR-007 | no | yes |
| 11 | Which API test case checks login with invalid credentials on the ParaBank API? | parabank:API-AUTH-002 | parabank:EXP-001 | no | yes |
| 12 | Which SQL test case verifies that a transfer posts exactly one debit and one credit entry? | parabank:DB-TRF-002 | parabank:DB-TRF-002 | yes | yes |
