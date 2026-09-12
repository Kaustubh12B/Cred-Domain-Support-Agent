# Cred Capstone Tasks 4 and 5 Report

## Reproducible configuration

- Embedding model: `all-MiniLM-L6-v2` (local SentenceTransformer)
- Answer strategy: `sentence`
- Chroma distance space: `cosine`; displayed score: `1 - distance`
- Evaluation retrieval depth: 3 chunks per strategy

## Task 4 threshold calibration

### In-scope top-1 scores

- `What affects eligibility for a home loan?`: 0.5042
- `How is my EMI calculated?`: 0.2175
- `Which KYC documents are required?`: 0.3089

### Out-of-scope top-1 scores

- `What is the weather in Mumbai today?`: -0.0002
- `Who won the latest cricket match?`: 0.0577

Selected threshold: **0.1376**

## Grounded-answer demonstration

### What affects eligibility for a home loan?

Top-1 score: 0.5042

Answer: This is fictional policy content created solely for the Cred capstone and does not describe an actual Cred policy. Personal and auto loan applicants in this fictional example must demonstrate a regular income source, while home-loan applicants must provide property-related documents.

### How is my EMI calculated?

Top-1 score: 0.2175

Answer: This is fictional policy content created solely for the Cred capstone and does not describe an actual Cred policy. The monthly installment is calculated from the approved principal, annual interest rate, and selected repayment tenure. Any change to the approved amount or tenure produces a revised installment schedule before disbursal.

### Which KYC documents are required?

Top-1 score: 0.3089

Answer: This is fictional policy content created solely for the Cred capstone and does not describe an actual Cred policy. Applicants submit a valid identity document, address document, and recent photograph for verification. Additional documents may be requested when submitted information is incomplete or inconsistent.

### What charge can apply when I prepay a loan early?

Top-1 score: 0.5314

Answer: This is fictional policy content created solely for the Cred capstone and does not describe an actual Cred policy. The sample policy permits partial or full prepayment after the first three completed installments. A disclosed charge may apply based on the remaining balance and the loan product selected in this fictional scenario.

### How does joint-account authorization work?

Top-1 score: 0.5425

Answer: This is fictional policy content created solely for the Cred capstone and does not describe an actual Cred policy. Each proposed joint holder must complete the same fictional verification requirements before the account is opened. The account mandate specifies whether either holder may transact alone or whether joint authorization is required.

### What is the weather in Mumbai today?

Top-1 score: -0.0002

Answer: I don't know based on the knowledge base.

## Task 5 document-level evaluation

### fixed_character

- Query: What affects eligibility for a home loan?
  - Expected parent: `KB-001`
  - Deduplicated retrieved parents: ['KB-001', 'KB-007']
  - Precision@3 = 1/3 = 0.333
  - Recall@3 = 1/1 = 1.000
- Query: How is my EMI calculated?
  - Expected parent: `KB-002`
  - Deduplicated retrieved parents: ['KB-002', 'KB-007']
  - Precision@3 = 1/3 = 0.333
  - Recall@3 = 1/1 = 1.000
- Query: Which KYC documents are required?
  - Expected parent: `KB-004`
  - Deduplicated retrieved parents: ['KB-001', 'KB-004', 'KB-011']
  - Precision@3 = 1/3 = 0.333
  - Recall@3 = 1/1 = 1.000
- Query: What charge can apply when I prepay a loan early?
  - Expected parent: `KB-008`
  - Deduplicated retrieved parents: ['KB-008', 'KB-007', 'KB-009']
  - Precision@3 = 1/3 = 0.333
  - Recall@3 = 1/1 = 1.000
- Query: How does joint-account authorization work?
  - Expected parent: `KB-011`
  - Deduplicated retrieved parents: ['KB-011', 'KB-006']
  - Precision@3 = 1/3 = 0.333
  - Recall@3 = 1/1 = 1.000
- Average Precision@3: 0.333
- Average Recall@3: 1.000

### sentence

- Query: What affects eligibility for a home loan?
  - Expected parent: `KB-001`
  - Deduplicated retrieved parents: ['KB-001', 'KB-007']
  - Precision@3 = 1/3 = 0.333
  - Recall@3 = 1/1 = 1.000
- Query: How is my EMI calculated?
  - Expected parent: `KB-002`
  - Deduplicated retrieved parents: ['KB-002', 'KB-009', 'KB-008']
  - Precision@3 = 1/3 = 0.333
  - Recall@3 = 1/1 = 1.000
- Query: Which KYC documents are required?
  - Expected parent: `KB-004`
  - Deduplicated retrieved parents: ['KB-004', 'KB-012', 'KB-001']
  - Precision@3 = 1/3 = 0.333
  - Recall@3 = 1/1 = 1.000
- Query: What charge can apply when I prepay a loan early?
  - Expected parent: `KB-008`
  - Deduplicated retrieved parents: ['KB-008', 'KB-003', 'KB-007']
  - Precision@3 = 1/3 = 0.333
  - Recall@3 = 1/1 = 1.000
- Query: How does joint-account authorization work?
  - Expected parent: `KB-011`
  - Deduplicated retrieved parents: ['KB-011', 'KB-006', 'KB-012']
  - Precision@3 = 1/3 = 0.333
  - Recall@3 = 1/1 = 1.000
- Average Precision@3: 0.333
- Average Recall@3: 1.000

## Deployment recommendation

Recommend the sentence strategy because it achieved the strongest measured document-level result (average Precision@3 0.333, Recall@3 1.000). Keep the calibrated fallback enabled so queries outside this small fictional policy set do not receive unsupported answers. Re-evaluate the threshold and metrics when the knowledge base changes.
