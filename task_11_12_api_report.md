# Capstone Tasks 11-12 API Demonstration

- `/ask` status response route: `loan_status`
- `/add-document` response: `{'document_id': 'KB-013', 'filename': 'kb-013-api-demonstration-policy.md', 'status': 'indexed'}`
- Fabricated-PII `/ask` masked input: `Which KYC documents are required? PAN [PAN_REDACTED], Aadhaar [AADHAAR_REDACTED], bank account [BANK_ACCOUNT_REDACTED].`
- JSONL entries written: `3` (exactly one per API request)
- Required structured logging keys present: `True`
- Raw fixed-format PAN, Aadhaar, and bank-account values absent from logs: `True`
