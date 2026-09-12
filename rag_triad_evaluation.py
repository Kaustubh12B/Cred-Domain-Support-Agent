"""Capstone Task 13: deterministic 15-query RAG triad evaluation with MOCK_LLM judge."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from capstone_agent import CapstoneAgent, JsonThreadMemory
from knowledge_base_index import ANSWER_STRATEGY, FALLBACK_ANSWER, KnowledgeBaseIndex, calibrate_threshold
from loan_application_status import MOCK_LLM


JUDGE_PROMPT_TEMPLATE = """You are MOCK_LLM judging a local RAG result. Score each criterion as 0 or 1.
Context relevance: does retrieved context support the expected topic or a correct out-of-scope fallback?
Groundedness: is the answer exactly retrieved context or the required fallback?
Answer relevance: does the answer satisfy the query without inventing policy?
Query: {query}
Expected source: {expected_source}
Retrieved context: {context}
Answer: {answer}
Return scores and concise deterministic reasoning."""

# Exactly 15: one per each of the 12 required topics, then three deliberate edge cases.
EVALUATION_QUERIES = (
    ("What affects eligibility for a home loan?", "KB-001"),
    ("How is my EMI calculated?", "KB-002"),
    ("Which card fees may apply?", "KB-003"),
    ("Which KYC documents are required?", "KB-004"),
    ("How can I report an unrecognized transaction?", "KB-005"),
    ("How do I close an account?", "KB-006"),
    ("How are interest-rate slabs assigned?", "KB-007"),
    ("What charge can apply when I prepay a loan early?", "KB-008"),
    ("What is the minimum balance requirement?", "KB-009"),
    ("Which factors affect a credit score?", "KB-010"),
    ("How does joint-account authorization work?", "KB-011"),
    ("Who can apply for an NRI account?", "KB-012"),
    ("What is the weather in Mumbai today?", None),
    ("Who won the latest cricket match?", None),
    ("How many moons does Neptune have?", None),
)


def mock_llm_judge(
    query: str, expected_source: str | None, context: str, answer: str, sources: list[str]
) -> dict[str, Any]:
    """Apply the visible template deterministically, without any external API or LLM."""
    if expected_source is None:
        correct = answer == FALLBACK_ANSWER and not sources
        reasoning = "Out-of-scope query correctly used the required fallback." if correct else "Out-of-scope query did not use the required fallback."
        return {"context_relevance": int(correct), "groundedness": int(correct), "answer_relevance": int(correct), "reasoning": reasoning}
    relevant = expected_source in sources
    grounded = answer == context and bool(context)
    answer_relevant = relevant and grounded and answer != FALLBACK_ANSWER
    reasoning = (
        f"Expected {expected_source}; retrieved sources {sources}. "
        f"Answer {'matches' if grounded else 'does not match'} retrieved context."
    )
    return {"context_relevance": int(relevant), "groundedness": int(grounded), "answer_relevance": int(answer_relevant), "reasoning": reasoning}


def run_evaluation() -> None:
    project_dir = Path(__file__).resolve().parent
    index = KnowledgeBaseIndex(project_dir / "knowledge_base", project_dir / "chroma_indexes")
    threshold, _, _ = calibrate_threshold(index, ANSWER_STRATEGY)
    memory_path = project_dir / "task_13_memory.json"
    memory_path.write_text("{}", encoding="utf-8")
    agent = CapstoneAgent(index, threshold, JsonThreadMemory(memory_path))
    results: list[dict[str, Any]] = []
    for number, (query, expected_source) in enumerate(EVALUATION_QUERIES, start=1):
        retrieved = index.retrieve(query, ANSWER_STRATEGY, top_k=1)[0]
        response = agent.ask(f"task13-{number}", query)
        judge = mock_llm_judge(query, expected_source, retrieved["text"], response.answer, response.sources)
        results.append({"number": number, "query": query, "expected_source": expected_source, "context": retrieved["text"], "answer": response.answer, "sources": response.sources, "judge": judge})

    averages = {
        key: sum(item["judge"][key] for item in results) / len(results)
        for key in ("context_relevance", "groundedness", "answer_relevance")
    }
    lines = [
        "# Cred Capstone Task 13 RAG Triad Report",
        "",
        f"- LLM mode: `{MOCK_LLM}`; no external API calls.",
        f"- Fixed input collection: `{ANSWER_STRATEGY}`; calibrated threshold: `{threshold:.4f}`.",
        "- Judge prompt template:",
        "",
        "```text",
        JUDGE_PROMPT_TEMPLATE,
        "```",
        "",
    ]
    for item in results:
        judge = item["judge"]
        lines.extend([
            f"## {item['number']}. {item['query']}", "",
            f"- Expected source: `{item['expected_source']}`",
            f"- Source IDs: {item['sources']}",
            f"- Retrieved context: {item['context']}",
            f"- Answer: {item['answer']}",
            f"- Context relevance: {judge['context_relevance']}",
            f"- Groundedness: {judge['groundedness']}",
            f"- Answer relevance: {judge['answer_relevance']}",
            f"- Judge reasoning: {judge['reasoning']}", "",
        ])
    lines.extend([
        "## Averages", "",
        f"- Average context relevance: {averages['context_relevance']:.3f}",
        f"- Average groundedness: {averages['groundedness']:.3f}",
        f"- Average answer relevance: {averages['answer_relevance']:.3f}", "",
    ])
    (project_dir / "task_13_rag_triad_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Evaluated exactly {len(results)} queries.")
    print(f"Averages: {averages}")


if __name__ == "__main__":
    run_evaluation()
