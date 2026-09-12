# Cred Capstone Tasks 11-12 API Demonstration

- `POST /ask` status: 200; route: `policy_rag`.
- `POST /add-document` status: 200; result: `Document stored and local indexes rebuilt.`.
- Fabricated-PII `POST /ask` status: 200.
- JSONL entries written: 3 (exactly one per API request).
- Raw fixed-format PAN, Aadhaar, and bank-account values absent from JSONL: `True`.
- The demo-created KB-099 document was removed after verification and the pre-demo indexes were rebuilt.
