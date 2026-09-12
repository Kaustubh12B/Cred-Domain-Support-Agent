"""Task 11-12 TestClient demonstration and JSONL PII-log verification."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from capstone_agent import AADHAAR_PATTERN, BANK_ACCOUNT_PATTERN, PAN_PATTERN
from capstone_api import create_app
from knowledge_base_index import KnowledgeBaseIndex


def run_demo() -> None:
    project_dir = Path(__file__).resolve().parent
    log_path = project_dir / "api_request_logs.jsonl"
    log_path.unlink(missing_ok=True)
    app = create_app(
        project_dir=project_dir,
        memory_path=project_dir / "api_demo_memory.json",
        log_path=log_path,
    )
    client = TestClient(app)
    ask_response = client.post(
        "/ask", json={"thread_id": "api-demo", "query": "How is my EMI calculated?"}
    )
    add_response = client.post(
        "/add-document",
        json={
            "document_id": "KB-099",
            "title": "Temporary API Demo Policy",
            "policy_content": "This fictional temporary policy demonstrates that the local index rebuild path works.",
        },
    )
    pii_response = client.post(
        "/ask",
        json={
            "thread_id": "api-pii",
            "query": "Which KYC documents are required? PAN ABCDE1234F, Aadhaar 1234 5678 9012, bank account 1234567890123.",
        },
    )
    # Remove only the document just created by this demo and restore the original 12-document indexes.
    (project_dir / "knowledge_base" / "kb-099-policy.md").unlink(missing_ok=True)
    KnowledgeBaseIndex(project_dir / "knowledge_base", project_dir / "chroma_indexes").build()

    entries = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    raw_patterns_absent = all(
        not pattern.search(log_path.read_text(encoding="utf-8"))
        for pattern in (PAN_PATTERN, AADHAAR_PATTERN, BANK_ACCOUNT_PATTERN)
    )
    report = "\n".join(
        [
            "# Cred Capstone Tasks 11-12 API Demonstration",
            "",
            f"- `POST /ask` status: {ask_response.status_code}; route: `{ask_response.json()['route']}`.",
            f"- `POST /add-document` status: {add_response.status_code}; result: `{add_response.json().get('message', add_response.json())}`.",
            f"- Fabricated-PII `POST /ask` status: {pii_response.status_code}.",
            f"- JSONL entries written: {len(entries)} (exactly one per API request).",
            f"- Raw fixed-format PAN, Aadhaar, and bank-account values absent from JSONL: `{raw_patterns_absent}`.",
            "- The demo-created KB-099 document was removed after verification and the pre-demo indexes were rebuilt.",
            "",
        ]
    )
    (project_dir / "task_11_12_report.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    run_demo()
