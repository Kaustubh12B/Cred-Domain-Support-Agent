"""Capstone Tasks 11-12: FastAPI surface and one-line-per-request safe logging."""

from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from capstone_agent import AgentResponse, CapstoneAgent, JsonThreadMemory, mask_pii
from knowledge_base_index import ANSWER_STRATEGY, KnowledgeBaseIndex, calibrate_threshold, read_knowledge_base


DOCUMENT_ID_PATTERN = re.compile(r"^KB-\d{3}$")


class AskRequest(BaseModel):
    thread_id: str = Field(min_length=1, max_length=100)
    query: str = Field(min_length=1, max_length=4000)


class AddDocumentRequest(BaseModel):
    document_id: str
    title: str = Field(min_length=1, max_length=160)
    policy_content: str = Field(min_length=1, max_length=4000)


class AddDocumentResponse(BaseModel):
    document_id: str
    filename: str
    message: str


class ApiRequestLogger:
    """Append exactly one sanitized JSONL event for each handled API request."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def write(
        self,
        endpoint: str,
        thread_id: str | None,
        request_text: str,
        started: float,
        outcome: str,
    ) -> None:
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "trace_id": str(uuid.uuid4()),
            "endpoint": endpoint,
            "thread_id": thread_id,
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            "outcome": outcome,
            "masked_request_text": mask_pii(request_text),
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")


def safe_document_filename(document_id: str) -> str:
    """Convert a validated stable ID into a traversal-safe Markdown filename."""
    if not DOCUMENT_ID_PATTERN.fullmatch(document_id):
        raise ValueError("document_id must match KB-###")
    return f"{document_id.lower()}-policy.md"


def create_app(
    project_dir: Path | None = None,
    knowledge_base_dir: Path | None = None,
    persist_dir: Path | None = None,
    memory_path: Path | None = None,
    log_path: Path | None = None,
) -> FastAPI:
    """Create a configurable local app; defaults point to this capstone workspace."""
    base = project_dir or Path(__file__).resolve().parent
    kb_dir = knowledge_base_dir or base / "knowledge_base"
    chroma_dir = persist_dir or base / "chroma_indexes"
    memories = memory_path or base / "api_thread_memory.json"
    logs = log_path or base / "api_request_logs.jsonl"
    index = KnowledgeBaseIndex(kb_dir, chroma_dir)
    threshold, _, _ = calibrate_threshold(index, ANSWER_STRATEGY)
    agent = CapstoneAgent(index, threshold, JsonThreadMemory(memories))
    request_logger = ApiRequestLogger(logs)

    app = FastAPI(title="Cred Capstone API", version="1.0")

    @app.middleware("http")
    async def log_api_request(request: Request, call_next):
        """Log once after every /ask or /add-document request, including validation errors."""
        if request.url.path not in {"/ask", "/add-document"}:
            return await call_next(request)
        started = time.perf_counter()
        body = await request.body()
        try:
            payload = json.loads(body or b"{}")
        except json.JSONDecodeError:
            payload = {}
        thread_id = payload.get("thread_id")
        request_text = payload.get("query") or " | ".join(
            str(payload.get(field, ""))
            for field in ("document_id", "title", "policy_content")
        )
        try:
            response = await call_next(request)
            outcome = "success" if response.status_code < 400 else "rejected"
            return response
        except Exception:
            request_logger.write(request.url.path, thread_id, request_text, started, "error")
            raise
        finally:
            # Exceptions return through the except branch above; ordinary requests arrive here once.
            if "response" in locals():
                request_logger.write(request.url.path, thread_id, request_text, started, outcome)

    @app.post("/ask", response_model=AgentResponse)
    def ask(request: AskRequest) -> AgentResponse:
        try:
            return agent.ask(request.thread_id, request.query)
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @app.post("/add-document", response_model=AddDocumentResponse)
    def add_document(request: AddDocumentRequest) -> AddDocumentResponse:
        try:
            filename = safe_document_filename(request.document_id)
            existing_ids = {document.document_id for document in read_knowledge_base(kb_dir)}
            if request.document_id in existing_ids:
                raise HTTPException(status_code=409, detail="document_id already exists")
            path = kb_dir / filename
            if path.exists():
                raise HTTPException(status_code=409, detail="document filename already exists")
            safe_title = request.title.replace("\n", " ").strip()
            safe_content = request.policy_content.strip()
            path.write_text(
                f"# {request.document_id}: {safe_title}\n\n{safe_content}\n", encoding="utf-8"
            )
            index.build()
            nonlocal threshold, agent
            threshold, _, _ = calibrate_threshold(index, ANSWER_STRATEGY)
            agent = CapstoneAgent(index, threshold, JsonThreadMemory(memories))
            return AddDocumentResponse(
                document_id=request.document_id,
                filename=filename,
                message="Document stored and local indexes rebuilt.",
            )
        except HTTPException:
            raise
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    return app


app = create_app()
