# Cred (Banking & FinTech) Track

A local, deterministic Banking & FinTech support-agent capstone. The default
execution mode is `MOCK_LLM (no external API calls)`, so the demonstrations run
without an LLM key or external model provider.

## Dataset

- Seed: `20260912`; records: `50`.
- Categories: Personal, Home, Auto, Education, and Business loans are each seeded
  at least three times; the remaining 35 records use equal weights of `1/5` for
  each required category, then the combined list is deterministically shuffled.
- Statuses: Submitted, Under Review, Approved, Rejected, and Disbursed are each
  seeded once; the remaining 45 records use equal weights of `1/5` for each
  required status, then the list is deterministically shuffled.
- Loan amount range: **₹75,000–₹50,00,000**. This spans small unsecured borrowing
  through substantial secured lending while remaining suitable for a compact demo.
- Fraud-review probability: `18%`; the seeded output observes `14%` (`7/50`) fraud
  flags.

## Install and run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Core local demonstrations
python dataset.py
python loan_application_status.py
python knowledge_base_index.py
python capstone_agent.py
python api_demo.py
python rag_triad_evaluation.py

# Tasks 15–16 checkpoint, retry, and timeout demonstrations
python task_14_16_advanced.py

# Task 14: use two terminals for the separate HTTP MCP processes
python mcp_server.py
python mcp_client.py

# FastAPI service (optional interactive API)
uvicorn capstone_api:app --host 127.0.0.1 --port 8001
```

The FastAPI endpoints are `POST /ask` for the guarded LangGraph agent and
`POST /add-document` for validated local knowledge-base additions. The FastMCP
endpoint is `http://127.0.0.1:8000/mcp`; run `python mcp_server.py` before
`python mcp_client.py`.

## Retrieval and escalation results

The local Chroma index uses `all-MiniLM-L6-v2`. Calibration top-1 scores were
0.5042, 0.2175, and 0.3089 for in-scope queries, versus -0.0002 and 0.0577 for
out-of-scope queries. The calibrated threshold is **0.1376**. Fixed-character
and sentence chunking tied at Precision@3 `0.333` and Recall@3 `1.000`; sentence
chunking is recommended because it preserves complete sentences.

The transparent escalation formula is:

`0.70 * fraud_flag + 0.30 * (1 - days_since_created / 30)`

Its nearest-rank 80th-percentile escalation threshold is **0.2900**.

## Tasks 14–16

- Task 14 exposes `get_loan_status(record_id)` through the FastMCP HTTP server;
  the separate client records standardized MCP envelopes for `LA-001` and `LA-002`.
- Task 15 checkpoints `intake -> validate -> enrich -> approval_gate -> END` in
  SQLite, interrupts before approval, and resumes the same thread without rerunning
  the first three nodes.
- Task 16 demonstrates three-attempt deterministic exponential retry (initial 0.05s,
  maximum 0.20s, no jitter), plus per-node and whole-graph timeout scopes.

## Repository structure

```text
dataset.py                    deterministic loan data (Tasks 1–3)
loan_application_status.py    status lookup and escalation (Task 6)
knowledge_base_index.py       chunking, Chroma retrieval, calibration (Tasks 4–5)
capstone_agent.py             guarded LangGraph agent and memory (Tasks 7–10)
capstone_api.py / api_demo.py FastAPI surface and logging demo (Tasks 11–12)
rag_triad_evaluation.py       MOCK_LLM RAG-triad evaluation (Task 13)
mcp_server.py / mcp_client.py separate FastMCP HTTP server/client (Task 14)
task_14_16_advanced.py        SQLite checkpoint and resilience demos (Tasks 15–16)
knowledge_base/               fictional policy sources
```

## Evidence artifacts

- `task_4_5_report.md` — retrieval calibration and evaluation.
- `task_6_report.md` — escalation distribution and threshold.
- `task_7_10_transcript.md` and `task_7_10_report.md` — LangGraph, memory, schema,
  and guardrail evidence.
- `task_11_12_report.md` and `task_11_12_api_report.md` — API and safe JSONL logging.
- `task_13_rag_triad_report.md` — RAG-triad results.
- `task_14_fastmcp_report.md` and `task_14_mcp_responses.json` — HTTP MCP calls.
- `task_15_sqlite_checkpoint_report.md` and `task_15_checkpoints.sqlite` — durable
  interruption/resume evidence.
- `task_16_resilience_report.md` — retry and timeout evidence.
- `SUBMISSION_CHECKLIST.md` — task-by-task source and evidence map.
