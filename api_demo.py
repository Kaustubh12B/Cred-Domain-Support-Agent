"""Capstone Tasks 11-12 API demonstration and masked-log verification."""

from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

from capstone_agent import AADHAAR_PATTERN, BANK_ACCOUNT_PATTERN, PAN_PATTERN
from capstone_api import create_app
from knowledge_base_index import read_knowledge_base


def next_demo_document_id(project_dir: Path) -> str:
    existing = {document.document_id for document in read_knowledge_base(project_dir / "knowledge_base")}
    for number in range(13, 1_000):
        candidate = f"KB-{number:03d}"
        if candidate not in existing:
            return candidate
    raise RuntimeError("No free KB document ID is available for the API demonstration")


def verify_log(log_path: Path) -> tuple[bool, int, list[dict[str, object]]]:
    entries = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line]
    raw_log = log_path.read_text(encoding="utf-8")
    pii_absent = not any(pattern.search(raw_log) for pattern in (PAN_PATTERN, AADHAAR_PATTERN, BANK_ACCOUNT_PATTERN))
    required_keys = {"timestamp", "trace_id", "endpoint", "thread_id", "duration_ms", "outcome", "masked_request_text"}
    if not all(required_keys <= entry.keys() for entry in entries):
        raise AssertionError("A structured log entry is missing a required field")
    return pii_absent, len(entries), entries


def main() -> None:
    project_dir = Path(__file__).resolve().parent
    log_path = project_dir / "api_requests.jsonl"
    log_path.write_text("", encoding="utf-8")
    app = create_app(project_dir)
    client = TestClient(app)

    status_response = client.post(
        "/ask", json={"thread_id": "api-status", "query": "Please check LA-002 status."}
    )
    status_response.raise_for_status()
    document_id = next_demo_document_id(project_dir)
    add_response = client.post(
        "/add-document",
        json={
            "document_id": document_id,
            "title": "API Demonstration Policy",
            "policy_content": "This is fictional Cred capstone policy content for an API demonstration. It has no real customer data and does not describe an actual Cred policy.",
        },
    )
    add_response.raise_for_status()
    pii_response = client.post(
        "/ask",
        json={
            "thread_id": "api-pii",
            "query": "Which KYC documents are required? PAN ABCDE1234F, Aadhaar 1234 5678 9012, bank account 1234567890123.",
        },
    )
    pii_response.raise_for_status()
    pii_absent, entry_count, entries = verify_log(log_path)
    if entry_count != 3:
        raise AssertionError(f"Expected exactly 3 JSONL entries, found {entry_count}")

    report = "\n".join(
        [
            "# Capstone Tasks 11-12 API Demonstration",
            "",
            f"- `/ask` status response route: `{status_response.json()['route']}`",
            f"- `/add-document` response: `{add_response.json()}`",
            f"- Fabricated-PII `/ask` masked input: `{pii_response.json()['masked_input']}`",
            f"- JSONL entries written: `{entry_count}` (exactly one per API request)",
            f"- Required structured logging keys present: `True`",
            f"- Raw fixed-format PAN, Aadhaar, and bank-account values absent from logs: `{pii_absent}`",
            "",
        ]
    )
    (project_dir / "task_11_12_api_report.md").write_text(report, encoding="utf-8")
    print(report)
    print("Masked log entries:")
    for entry in entries:
        print(json.dumps(entry))


if __name__ == "__main__":
    main()
