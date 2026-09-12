# Cred Capstone Task 13 RAG Triad Report

- LLM mode: `MOCK_LLM (no external API calls)`; no external API calls.
- Fixed input collection: `sentence`; calibrated threshold: `0.1376`.
- Judge prompt template:

```text
You are MOCK_LLM judging a local RAG result. Score each criterion as 0 or 1.
Context relevance: does retrieved context support the expected topic or a correct out-of-scope fallback?
Groundedness: is the answer exactly retrieved context or the required fallback?
Answer relevance: does the answer satisfy the query without inventing policy?
Query: {query}
Expected source: {expected_source}
Retrieved context: {context}
Answer: {answer}
Return scores and concise deterministic reasoning.
```

## 1. What affects eligibility for a home loan?

- Expected source: `KB-001`
- Source IDs: ['KB-001']
- Retrieved context: This is fictional policy content created solely for the Cred capstone and does not describe an actual Cred policy. Personal and auto loan applicants in this fictional example must demonstrate a regular income source, while home-loan applicants must provide property-related documents.
- Answer: This is fictional policy content created solely for the Cred capstone and does not describe an actual Cred policy. Personal and auto loan applicants in this fictional example must demonstrate a regular income source, while home-loan applicants must provide property-related documents.
- Context relevance: 1
- Groundedness: 1
- Answer relevance: 1
- Judge reasoning: Expected KB-001; retrieved sources ['KB-001']. Answer matches retrieved context.

## 2. How is my EMI calculated?

- Expected source: `KB-002`
- Source IDs: ['KB-002']
- Retrieved context: This is fictional policy content created solely for the Cred capstone and does not describe an actual Cred policy. The monthly installment is calculated from the approved principal, annual interest rate, and selected repayment tenure. Any change to the approved amount or tenure produces a revised installment schedule before disbursal.
- Answer: This is fictional policy content created solely for the Cred capstone and does not describe an actual Cred policy. The monthly installment is calculated from the approved principal, annual interest rate, and selected repayment tenure. Any change to the approved amount or tenure produces a revised installment schedule before disbursal.
- Context relevance: 1
- Groundedness: 1
- Answer relevance: 1
- Judge reasoning: Expected KB-002; retrieved sources ['KB-002']. Answer matches retrieved context.

## 3. Which card fees may apply?

- Expected source: `KB-003`
- Source IDs: ['KB-003']
- Retrieved context: This is fictional policy content created solely for the Cred capstone and does not describe an actual Cred policy. The sample card product may charge an annual membership fee and a late-payment fee when the minimum due is missed. Cash advances and foreign-currency transactions can carry separate disclosed charges in this fictional fee schedule.
- Answer: This is fictional policy content created solely for the Cred capstone and does not describe an actual Cred policy. The sample card product may charge an annual membership fee and a late-payment fee when the minimum due is missed. Cash advances and foreign-currency transactions can carry separate disclosed charges in this fictional fee schedule.
- Context relevance: 1
- Groundedness: 1
- Answer relevance: 1
- Judge reasoning: Expected KB-003; retrieved sources ['KB-003']. Answer matches retrieved context.

## 4. Which KYC documents are required?

- Expected source: `KB-004`
- Source IDs: ['KB-004']
- Retrieved context: This is fictional policy content created solely for the Cred capstone and does not describe an actual Cred policy. Applicants submit a valid identity document, address document, and recent photograph for verification. Additional documents may be requested when submitted information is incomplete or inconsistent.
- Answer: This is fictional policy content created solely for the Cred capstone and does not describe an actual Cred policy. Applicants submit a valid identity document, address document, and recent photograph for verification. Additional documents may be requested when submitted information is incomplete or inconsistent.
- Context relevance: 1
- Groundedness: 1
- Answer relevance: 1
- Judge reasoning: Expected KB-004; retrieved sources ['KB-004']. Answer matches retrieved context.

## 5. How can I report an unrecognized transaction?

- Expected source: `KB-005`
- Source IDs: ['KB-005']
- Retrieved context: The sample review process examines transaction evidence and communicates a resolution after the investigation is complete.
- Answer: The sample review process examines transaction evidence and communicates a resolution after the investigation is complete.
- Context relevance: 1
- Groundedness: 1
- Answer relevance: 1
- Judge reasoning: Expected KB-005; retrieved sources ['KB-005']. Answer matches retrieved context.

## 6. How do I close an account?

- Expected source: `KB-006`
- Source IDs: ['KB-006']
- Retrieved context: This is fictional policy content created solely for the Cred capstone and does not describe an actual Cred policy. An account-closure request is processed after outstanding balances, pending charges, and linked-service obligations are settled.
- Answer: This is fictional policy content created solely for the Cred capstone and does not describe an actual Cred policy. An account-closure request is processed after outstanding balances, pending charges, and linked-service obligations are settled.
- Context relevance: 1
- Groundedness: 1
- Answer relevance: 1
- Judge reasoning: Expected KB-006; retrieved sources ['KB-006']. Answer matches retrieved context.

## 7. How are interest-rate slabs assigned?

- Expected source: `KB-007`
- Source IDs: ['KB-007']
- Retrieved context: This is fictional policy content created solely for the Cred capstone and does not describe an actual Cred policy. This sample lending program assigns applicants to rate slabs using loan type, repayment tenure, and a modeled risk assessment. The final rate and applicable slab are shown in the fictional approval summary before acceptance.
- Answer: This is fictional policy content created solely for the Cred capstone and does not describe an actual Cred policy. This sample lending program assigns applicants to rate slabs using loan type, repayment tenure, and a modeled risk assessment. The final rate and applicable slab are shown in the fictional approval summary before acceptance.
- Context relevance: 1
- Groundedness: 1
- Answer relevance: 1
- Judge reasoning: Expected KB-007; retrieved sources ['KB-007']. Answer matches retrieved context.

## 8. What charge can apply when I prepay a loan early?

- Expected source: `KB-008`
- Source IDs: ['KB-008']
- Retrieved context: This is fictional policy content created solely for the Cred capstone and does not describe an actual Cred policy. The sample policy permits partial or full prepayment after the first three completed installments. A disclosed charge may apply based on the remaining balance and the loan product selected in this fictional scenario.
- Answer: This is fictional policy content created solely for the Cred capstone and does not describe an actual Cred policy. The sample policy permits partial or full prepayment after the first three completed installments. A disclosed charge may apply based on the remaining balance and the loan product selected in this fictional scenario.
- Context relevance: 1
- Groundedness: 1
- Answer relevance: 1
- Judge reasoning: Expected KB-008; retrieved sources ['KB-008']. Answer matches retrieved context.

## 9. What is the minimum balance requirement?

- Expected source: `KB-009`
- Source IDs: ['KB-009']
- Retrieved context: This is fictional policy content created solely for the Cred capstone and does not describe an actual Cred policy. The fictional savings account requires a stated average monthly balance, which may differ by account variant. If the balance requirement is not met, the sample account terms may apply a disclosed maintenance charge.
- Answer: This is fictional policy content created solely for the Cred capstone and does not describe an actual Cred policy. The fictional savings account requires a stated average monthly balance, which may differ by account variant. If the balance requirement is not met, the sample account terms may apply a disclosed maintenance charge.
- Context relevance: 1
- Groundedness: 1
- Answer relevance: 1
- Judge reasoning: Expected KB-009; retrieved sources ['KB-009']. Answer matches retrieved context.

## 10. Which factors affect a credit score?

- Expected source: `KB-010`
- Source IDs: ['KB-010']
- Retrieved context: This is fictional policy content created solely for the Cred capstone and does not describe an actual Cred policy. The illustrative credit assessment considers repayment history, outstanding debt, credit-use ratio, and length of credit history. It is a simplified capstone example and does not calculate or represent any real customer's credit score.
- Answer: This is fictional policy content created solely for the Cred capstone and does not describe an actual Cred policy. The illustrative credit assessment considers repayment history, outstanding debt, credit-use ratio, and length of credit history. It is a simplified capstone example and does not calculate or represent any real customer's credit score.
- Context relevance: 1
- Groundedness: 1
- Answer relevance: 1
- Judge reasoning: Expected KB-010; retrieved sources ['KB-010']. Answer matches retrieved context.

## 11. How does joint-account authorization work?

- Expected source: `KB-011`
- Source IDs: ['KB-011']
- Retrieved context: This is fictional policy content created solely for the Cred capstone and does not describe an actual Cred policy. Each proposed joint holder must complete the same fictional verification requirements before the account is opened. The account mandate specifies whether either holder may transact alone or whether joint authorization is required.
- Answer: This is fictional policy content created solely for the Cred capstone and does not describe an actual Cred policy. Each proposed joint holder must complete the same fictional verification requirements before the account is opened. The account mandate specifies whether either holder may transact alone or whether joint authorization is required.
- Context relevance: 1
- Groundedness: 1
- Answer relevance: 1
- Judge reasoning: Expected KB-011; retrieved sources ['KB-011']. Answer matches retrieved context.

## 12. Who can apply for an NRI account?

- Expected source: `KB-012`
- Source IDs: ['KB-012']
- Retrieved context: Eligibility is confirmed only after the fictional review verifies that the requested account variant supports the applicant's declared status.
- Answer: Eligibility is confirmed only after the fictional review verifies that the requested account variant supports the applicant's declared status.
- Context relevance: 1
- Groundedness: 1
- Answer relevance: 1
- Judge reasoning: Expected KB-012; retrieved sources ['KB-012']. Answer matches retrieved context.

## 13. What is the weather in Mumbai today?

- Expected source: `None`
- Source IDs: []
- Retrieved context: The fictional service confirms closure through the registered contact method once the final review is complete.
- Answer: I don't know based on the knowledge base.
- Context relevance: 1
- Groundedness: 1
- Answer relevance: 1
- Judge reasoning: Out-of-scope query correctly used the required fallback.

## 14. Who won the latest cricket match?

- Expected source: `None`
- Source IDs: []
- Retrieved context: The fictional service confirms closure through the registered contact method once the final review is complete.
- Answer: I don't know based on the knowledge base.
- Context relevance: 1
- Groundedness: 1
- Answer relevance: 1
- Judge reasoning: Out-of-scope query correctly used the required fallback.

## 15. How many moons does Neptune have?

- Expected source: `None`
- Source IDs: []
- Retrieved context: Education and business loan requests are assessed against course or business details alongside repayment capacity.
- Answer: I don't know based on the knowledge base.
- Context relevance: 1
- Groundedness: 1
- Answer relevance: 1
- Judge reasoning: Out-of-scope query correctly used the required fallback.

## Averages

- Average context relevance: 1.000
- Average groundedness: 1.000
- Average answer relevance: 1.000
