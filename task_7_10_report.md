# Cred Capstone Tasks 7-10 Report

- LLM mode: `MOCK_LLM (no external API calls)`; no external LLM or API is called.
- Fixed RAG input: sentence-based Chroma collection (`sentence`).
- Calibrated policy threshold: `0.1376`.
- LangGraph nodes: `input_guardrail`, `intent_router`, `policy_rag_tool`, `loan_status_tool`, and `response_validator` (plus an injection-refusal branch).
- All final turns were Pydantic-validated with `AgentResponse` before memory persistence.
- Persisted JSON contains no raw fixed-format PAN, Aadhaar, or bank-account value: `True`.
- Applicant names and income figures are deliberately out of scope for keyless MOCK_LLM masking.
- The transcript demonstrates both routes, persisted context, fresh-thread reset, PII masking, prompt-injection refusal, and the calibrated unsupported-policy fallback.
