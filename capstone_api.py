"""Capstone Tasks 11-12: local FastAPI interface and structured JSONL logging."""

from __future__ import annotations

import json
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from capstone_agent import AgentResponse, CapstoneAgent, JsonThreadMemory, mask_pii
from knowledge_base_index import ANSWER_STRATEGY, KnowledgeBaseIndex, calibrate_threshold, read_knowledge_base


DOCUMENT_ID_PATTERN = re.compile(r"^KB-\d{3}$")


class AskRequest(BaseModel):
    thread_id: str = Field(min_length=1, max_length=100)
    query: str = Field(min_length=1, max_length=4_000)


class AddDocumentRequest(BaseModel):
    document_id: str
    title: str = Field(min_length=1, max_length=160)
    policy_content: str = Field(min_length=20, max_length=8_000)

    @field_validator("document_id")
    @classmethod
    def validate_document_id(cls, value: str) -> str:
        normalized = value.upper()
        if not DOCUMENT_ID_PATTERN.fullmatch(normalized):
            raise ValueError("document_id must use the stable format KB-###")
        return normalized

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        if "\n" in value or "\r" in value:
            raise ValueError("title must be a single line")
        return value.strip()


def safe_filename(document_id: str, title: str) -> str:
    """Create a safe, readable Markdown filename from validated input."""
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "policy"
    return f"{document_id.lower()}-{slug[:60]}.md"


def request_log_text(payload: dict[str, Any]) -> str:
    """Choose request text for logging and apply the shared guardrail masker."""
    if "query" in payload:
        return mask_pii(str(payload["query"]))
    return mask_pii(
        " ".join(str(payload.get(key, "")) for key in ("document_id", "title", "policy_content"))
    )


def create_app(project_dir: Path | None = None) -> FastAPI:
    """Create the local-only API app and its reusable agent runtime."""
    root = project_dir or Path(__file__).resolve().parent
    app = FastAPI(title="Cred Capstone Local API")
    app.state.project_dir = root
    app.state.log_path = root / "api_requests.jsonl"
    app.state.memory_path = root / "api_thread_memory.json"

    def refresh_agent() -> None:
        index = KnowledgeBaseIndex(root / "knowledge_base", root / "chroma_indexes")
        threshold, _, _ = calibrate_threshold(index, ANSWER_STRATEGY)
        app.state.index = index
        app.state.threshold = threshold
        app.state.agent = CapstoneAgent(index, threshold, JsonThreadMemory(app.state.memory_path))

    refresh_agent()

    @app.middleware("http")
    async def log_request(request: Request, call_next):
        """Write exactly one masked structured record for every API request."""
        started = time.perf_counter()
        body = await request.body()
        try:
            payload = json.loads(body) if body else {}
        except json.JSONDecodeError:
            payload = {}
        thread_id = payload.get("thread_id")
        outcome = "success"
        try:
            response = await call_next(request)
            if response.status_code >= 400:
                outcome = "error"
            return response
        except Exception:
            outcome = "error"
            raise
        finally:
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "trace_id": str(uuid.uuid4()),
                "endpoint": request.url.path,
                "thread_id": thread_id,
                "duration_ms": round((time.perf_counter() - started) * 1_000, 3),
                "outcome": outcome,
                "masked_request_text": request_log_text(payload),
            }
            with app.state.log_path.open("a", encoding="utf-8") as log_file:
                log_file.write(json.dumps(entry) + "\n")

    @app.post("/ask", response_model=AgentResponse)
    def ask(request_body: AskRequest) -> AgentResponse:
        return app.state.agent.ask(request_body.thread_id, request_body.query)

    @app.post("/add-document")
    def add_document(request_body: AddDocumentRequest) -> dict[str, str]:
        documents = read_knowledge_base(root / "knowledge_base")
        if request_body.document_id in {document.document_id for document in documents}:
            raise HTTPException(status_code=409, detail="document_id already exists")
        filename = safe_filename(request_body.document_id, request_body.title)
        target = root / "knowledge_base" / filename
        if target.exists():
            raise HTTPException(status_code=409, detail="target filename already exists")
        content = request_body.policy_content.strip()
        target.write_text(
            f"# {request_body.document_id}: {request_body.title}\n\n{content}\n",
            encoding="utf-8",
        )
        app.state.index.build()
        _, _, _ = calibrate_threshold(app.state.index, ANSWER_STRATEGY)
        return {"document_id": request_body.document_id, "filename": filename, "status": "indexed"}

    return app


app = create_app()
