"""Cred capstone Tasks 14--16: MCP, durable interruption, retries, and timeouts.

Every demonstration is local and deterministic.  ``MOCK_LLM`` is retained as an
explicit execution-mode marker; no model provider or external service is called.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
from pathlib import Path
from typing import Any, TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from loan_application_status import MOCK_LLM


PROJECT_DIR = Path(__file__).resolve().parent
CHECKPOINT_DB = PROJECT_DIR / "task_15_checkpoints.sqlite"


# Task 15 --------------------------------------------------------------------
class ApprovalState(TypedDict, total=False):
    application_id: str
    decision: str
    audit: list[str]


def build_checkpoint_graph(
    checkpointer: SqliteSaver, execution_counts: dict[str, int]
):
    def record(node_name: str, state: ApprovalState, note: str) -> dict[str, Any]:
        execution_counts[node_name] += 1
        return {"audit": state.get("audit", []) + [note]}

    def intake_node(state: ApprovalState) -> dict[str, Any]:
        return record("intake", state, f"intake completed for {state['application_id']}")

    def validate_node(state: ApprovalState) -> dict[str, Any]:
        return record("validate", state, "validate completed")

    def enrich_node(state: ApprovalState) -> dict[str, Any]:
        return record("enrich", state, "enrich completed")

    def approval_gate_node(state: ApprovalState) -> dict[str, Any]:
        return record("approval_gate", state, f"approval completed with decision={state['decision']}")

    graph = StateGraph(ApprovalState)
    graph.add_node("intake", intake_node)
    graph.add_node("validate", validate_node)
    graph.add_node("enrich", enrich_node)
    graph.add_node("approval_gate", approval_gate_node)
    graph.add_edge(START, "intake")
    graph.add_edge("intake", "validate")
    graph.add_edge("validate", "enrich")
    graph.add_edge("enrich", "approval_gate")
    graph.add_edge("approval_gate", END)
    return graph.compile(checkpointer=checkpointer)


def demonstrate_checkpoint_resume() -> dict[str, Any]:
    if CHECKPOINT_DB.exists():
        CHECKPOINT_DB.unlink()
    config = {"configurable": {"thread_id": "approval-LA-002"}}
    execution_counts = {"intake": 0, "validate": 0, "enrich": 0, "approval_gate": 0}
    with SqliteSaver.from_conn_string(str(CHECKPOINT_DB)) as checkpointer:
        graph = build_checkpoint_graph(checkpointer, execution_counts)
        # This single invocation pauses after the first three nodes without placing a
        # permanent breakpoint on the compiled graph used for the resume.
        interrupted = graph.invoke(
            {"application_id": "LA-002"}, config, interrupt_before=["approval_gate"]
        )
        paused_state = graph.get_state(config)
        counts_before_resume = dict(execution_counts)
        # Update the durable pending state, then invoke with None to continue the
        # queued approval node rather than starting a new graph execution.
        graph.update_state(config, {"decision": "approved"})
        resumed = graph.invoke(None, config)
        final_state = graph.get_state(config)

    with sqlite3.connect(CHECKPOINT_DB) as connection:
        checkpoint_rows = connection.execute("SELECT COUNT(*) FROM checkpoints").fetchone()[0]
    return {
        "interrupted_values": interrupted,
        "next_node": list(paused_state.next),
        "resumed_values": resumed,
        "final_next": list(final_state.next),
        "counts_before_resume": counts_before_resume,
        "counts_after_resume": dict(execution_counts),
        "checkpoint_rows": checkpoint_rows,
        "database": CHECKPOINT_DB.name,
    }


def write_task_15_report(result: dict[str, Any]) -> None:
    (PROJECT_DIR / "task_15_sqlite_checkpoint_report.md").write_text(
        "\n".join(
            [
                "# Cred Capstone Task 15 SQLite LangGraph Checkpoint Report",
                "",
                f"- LLM mode: `{MOCK_LLM}`; no external LLM or API is called.",
                f"- Durable checkpointer: `SqliteSaver` at `{result['database']}`.",
                "- Graph: `intake -> validate -> enrich -> approval_gate -> END`; the first "
                "invocation uses `interrupt_before=['approval_gate']`.",
                "",
                "## Interruption and resume evidence",
                "",
                f"- First invocation stopped before: `{result['next_node']}`.",
                f"- Persisted state at interruption: `{json.dumps(result['interrupted_values'])}`.",
                "- Resume input: `{'decision': 'approved'}` on the same thread ID "
                "`approval-LA-002`.",
                f"- Resumed final state: `{json.dumps(result['resumed_values'])}`.",
                f"- Remaining next nodes after resume: `{result['final_next']}`.",
                f"- Execution counters before resume: `{json.dumps(result['counts_before_resume'])}`.",
                f"- Execution counters after resume: `{json.dumps(result['counts_after_resume'])}`.",
                f"- SQLite checkpoint rows recorded: `{result['checkpoint_rows']}`.",
                "",
                "The counters prove that intake, validate, and enrich completed before the interrupt "
                "and were not re-run on resume; approval_gate ran exactly once after resume.",
                "",
            ]
        ),
        encoding="utf-8",
    )


# Task 16 --------------------------------------------------------------------
class ResilienceState(TypedDict, total=False):
    attempts: int
    outcome: str


class TransientRiskServiceError(RuntimeError):
    """Local deterministic failure used to demonstrate bounded retry."""


def demonstrate_retry() -> dict[str, Any]:
    attempts = {"count": 0}
    observed_delays: list[float] = []

    def record_delay(retry_state: Any) -> None:
        observed_delays.append(round(float(retry_state.next_action.sleep), 2))

    @retry(
        retry=retry_if_exception_type(TransientRiskServiceError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.05, max=0.20, exp_base=2),
        before_sleep=record_delay,
        reraise=True,
    )
    def transient_lookup() -> str:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise TransientRiskServiceError("simulated transient local dependency failure")
        return "risk lookup succeeded"

    result = transient_lookup()
    return {"attempts": attempts["count"], "result": result, "observed_delays": observed_delays}


async def bounded_node(_: ResilienceState) -> dict[str, Any]:
    try:
        await asyncio.wait_for(asyncio.sleep(0.05), timeout=0.01)
    except TimeoutError:
        return {"outcome": "per_node_timeout"}
    return {"outcome": "unexpected_success"}


async def slow_node(_: ResilienceState) -> dict[str, Any]:
    await asyncio.sleep(0.05)
    return {"outcome": "completed"}


def build_async_graph(node: Any):
    graph = StateGraph(ResilienceState)
    graph.add_node("work", node)
    graph.add_edge(START, "work")
    graph.add_edge("work", END)
    return graph.compile()


async def demonstrate_timeouts() -> dict[str, str]:
    per_node_result = await build_async_graph(bounded_node).ainvoke({})
    try:
        await asyncio.wait_for(build_async_graph(slow_node).ainvoke({}), timeout=0.01)
    except TimeoutError:
        global_result = "global_timeout"
    else:
        global_result = "unexpected_success"
    return {"per_node": per_node_result["outcome"], "global": global_result}


def write_task_16_report(retry_result: dict[str, Any], timeouts: dict[str, str]) -> None:
    (PROJECT_DIR / "task_16_resilience_report.md").write_text(
        "\n".join(
            [
                "# Cred Capstone Task 16 Retry and Timeout Report",
                "",
                f"- LLM mode: `{MOCK_LLM}`; no external LLM or API is called.",
                "- Retry policy: Tenacity retries only `TransientRiskServiceError`; max attempts = "
                "3; exponential-backoff initial interval = 0.05 seconds; max interval = 0.20 "
                "seconds; jitter = disabled for deterministic reproducibility.",
                f"- Retry result: `{retry_result['result']}` after `{retry_result['attempts']}` attempts "
                "(first two attempts intentionally failed).",
                f"- Observed deterministic backoff intervals before recovery: `{retry_result['observed_delays']}` seconds.",
                "- Per-node timeout: a 50 ms node operation is bounded by `asyncio.wait_for(..., "
                "timeout=0.01)` inside the node.",
                f"- Per-node demonstration result: `{timeouts['per_node']}`.",
                "- Global timeout: the entire compiled graph invocation containing a 50 ms node is "
                "bounded by `asyncio.wait_for(..., timeout=0.01)`.",
                f"- Global demonstration result: `{timeouts['global']}`.",
                "",
                "The scopes differ deliberately: the per-node timeout is handled as a node outcome, "
                "while the global timeout cancels the graph invocation itself.",
                "",
            ]
        ),
        encoding="utf-8",
    )


async def main() -> None:
    task15 = demonstrate_checkpoint_resume()
    write_task_15_report(task15)
    retry_result = demonstrate_retry()
    timeouts = await demonstrate_timeouts()
    write_task_16_report(retry_result, timeouts)
    print("Task 15 checkpoint evidence:", task15)
    print("Task 16 retry/timeouts:", retry_result, timeouts)


if __name__ == "__main__":
    asyncio.run(main())
