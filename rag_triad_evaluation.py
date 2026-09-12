"""Capstone Task 13: deterministic 15-query RAG triad evaluation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from knowledge_base_index import (
    ANSWER_STRATEGY,
    FALLBACK_ANSWER,
    KnowledgeBaseIndex,
    calibrate_threshold,
    mock_llm_grounded_answer,
)


MOCK_LLM_JUDGE_PROMPT = """You are MOCK_LLM, a deterministic local RAG judge.
Score context relevance, groundedness, and answer relevance from 1 (poor) to 5 (strong).
Use only the supplied query, expected source ID, retrieved context, and answer.
Query: {query}
Expected source ID: {expected_source_id}
Retrieved source IDs: {source_ids}
Retrieved context: {context}
Answer: {answer}
"""

# Exactly 15 queries: one for every required topic, one extra in-scope check, and two edge cases.
EVALUATION_QUERIES = (
    ("What affects eligibility for a home loan?", "KB-001"),
    ("How is my EMI calculated?", "KB-002"),
    ("What fees can a credit card charge?", "KB-003"),
    ("Which KYC documents are required?", "KB-004"),
    ("How is an unrecognized transaction dispute handled?", "KB-005"),
    ("How do I close an account?", "KB-006"),
    ("How are interest-rate slabs assigned?", "KB-007"),
    ("What charge can apply when I prepay a loan early?", "KB-008"),
    ("What is the minimum-balance rule?", "KB-009"),
    ("Which factors affect a credit score?", "KB-010"),
    ("How does joint-account authorization work?", "KB-011"),
    ("Who can apply for an NRI account?", "KB-012"),
    ("What affects eligibility for a business loan?", "KB-001"),
    ("What is the weather in Mumbai today?", None),
    ("Who won the latest cricket match?", None),
)


def mock_llm_judge(
    query: str,
    expected_source_id: str | None,
    source_ids: list[str],
    context: str,
    answer: str,
) -> dict[str, Any]:
    """Use the visible prompt template and deterministic rules; no external judge is called."""
    prompt = MOCK_LLM_JUDGE_PROMPT.format(
        query=query,
        expected_source_id=expected_source_id or "None (out of scope)",
        source_ids=source_ids,
        context=context,
        answer=answer,
    )
    if expected_source_id is None:
        correct = answer == FALLBACK_ANSWER
        scores = {"context_relevance": 5 if correct else 1, "groundedness": 5 if correct else 1, "answer_relevance": 5 if correct else 1}
        reasoning = "Out-of-scope query correctly used the calibrated fallback." if correct else "Out-of-scope query should have used the fallback."
    else:
        source_match = expected_source_id in source_ids
        grounded = answer != FALLBACK_ANSWER and answer == context
        scores = {
            "context_relevance": 5 if source_match else 1,
            "groundedness": 5 if grounded else 1,
            "answer_relevance": 5 if source_match and grounded else 1,
        }
        reasoning = (
            "Expected parent source was retrieved and the answer is exactly the retrieved context."
            if source_match and grounded
            else "The expected source was missing or the answer was not grounded in retrieved context."
        )
    return {"prompt": prompt, "scores": scores, "reasoning": reasoning}


def main() -> None:
    if len(EVALUATION_QUERIES) != 15:
        raise ValueError("Task 13 requires exactly 15 evaluation queries")
    project_dir = Path(__file__).resolve().parent
    index = KnowledgeBaseIndex(project_dir / "knowledge_base", project_dir / "chroma_indexes")
    threshold, _, _ = calibrate_threshold(index, ANSWER_STRATEGY)
    results: list[dict[str, Any]] = []
    for query, expected_source_id in EVALUATION_QUERIES:
        retrieved = index.retrieve(query, ANSWER_STRATEGY, top_k=1)
        context = retrieved[0]["text"]
        answer = mock_llm_grounded_answer(retrieved, threshold)
        source_ids = [] if answer == FALLBACK_ANSWER else [retrieved[0]["document_id"]]
        judge = mock_llm_judge(query, expected_source_id, source_ids, context, answer)
        results.append(
            {
                "query": query,
                "expected_source_id": expected_source_id,
                "source_ids": source_ids,
                "context": context,
                "answer": answer,
                "judge": judge,
            }
        )
    averages = {
        metric: sum(result["judge"]["scores"][metric] for result in results) / len(results)
        for metric in ("context_relevance", "groundedness", "answer_relevance")
    }
    lines = [
        "# Cred Capstone Task 13 RAG Triad Report",
        "",
        f"- Judge: `MOCK_LLM` with the deterministic prompt template below; no external API is called.",
        f"- Fixed RAG collection: `{ANSWER_STRATEGY}`; calibrated threshold: `{threshold:.4f}`.",
        f"- Query count: `{len(results)}`.",
        "",
        "## MOCK_LLM judge prompt template",
        "",
        "```text",
        MOCK_LLM_JUDGE_PROMPT.strip(),
        "```",
        "",
    ]
    for number, result in enumerate(results, start=1):
        scores = result["judge"]["scores"]
        lines.extend(
            [
                f"## {number}. {result['query']}",
                "",
                f"- Expected source: `{result['expected_source_id']}`",
                f"- Retrieved source IDs: `{result['source_ids']}`",
                f"- Retrieved context: {result['context']}",
                f"- Answer: {result['answer']}",
                f"- Context relevance: {scores['context_relevance']}/5",
                f"- Groundedness: {scores['groundedness']}/5",
                f"- Answer relevance: {scores['answer_relevance']}/5",
                f"- Judge reasoning: {result['judge']['reasoning']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Averages across 15 queries",
            "",
            f"- Average context relevance: {averages['context_relevance']:.2f}/5",
            f"- Average groundedness: {averages['groundedness']:.2f}/5",
            f"- Average answer relevance: {averages['answer_relevance']:.2f}/5",
            "",
        ]
    )
    report_path = project_dir / "task_13_rag_triad_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"15-query report written to: {report_path}")
    print("Averages:", averages)


if __name__ == "__main__":
    main()
