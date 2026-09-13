# Cred Capstone Task 15 SQLite LangGraph Checkpoint Report

- LLM mode: `MOCK_LLM (no external API calls)`; no external LLM or API is called.
- Durable checkpointer: `SqliteSaver` at `task_15_checkpoints.sqlite`.
- Graph: `intake -> validate -> enrich -> approval_gate -> END`; the first invocation uses `interrupt_before=['approval_gate']`.

## Interruption and resume evidence

- First invocation stopped before: `['approval_gate']`.
- Persisted state at interruption: `{"application_id": "LA-002", "audit": ["intake completed for LA-002", "validate completed", "enrich completed"]}`.
- Resume input: `{'decision': 'approved'}` on the same thread ID `approval-LA-002`.
- Resumed final state: `{"application_id": "LA-002", "decision": "approved", "audit": ["intake completed for LA-002", "validate completed", "enrich completed", "approval completed with decision=approved"]}`.
- Remaining next nodes after resume: `[]`.
- Execution counters before resume: `{"intake": 1, "validate": 1, "enrich": 1, "approval_gate": 0}`.
- Execution counters after resume: `{"intake": 1, "validate": 1, "enrich": 1, "approval_gate": 1}`.
- SQLite checkpoint rows recorded: `7`.

The counters prove that intake, validate, and enrich completed before the interrupt and were not re-run on resume; approval_gate ran exactly once after resume.
