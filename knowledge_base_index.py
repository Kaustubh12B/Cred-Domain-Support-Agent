"""Build and query local ChromaDB indexes for the Cred capstone knowledge base."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Literal

import chromadb
from chromadb.errors import NotFoundError
from sentence_transformers import SentenceTransformer


Strategy = Literal["fixed_character", "sentence"]

MODEL_NAME = "all-MiniLM-L6-v2"
FIXED_CHARACTER_SIZE = 300
FIXED_CHARACTER_OVERLAP = 60
SENTENCE_CHUNK_MAX_CHARS = 350
COLLECTION_NAMES: dict[Strategy, str] = {
    "fixed_character": "cred_kb_fixed_character",
    "sentence": "cred_kb_sentence",
}
HEADING_PATTERN = re.compile(r"^#\s+(KB-\d{3}):\s+(.+?)\s*$", re.MULTILINE)
SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+")
ANSWER_STRATEGY: Strategy = "sentence"
FALLBACK_ANSWER = "I don't know based on the knowledge base."
CALIBRATION_IN_SCOPE_QUERIES = (
    "What affects eligibility for a home loan?",
    "How is my EMI calculated?",
    "Which KYC documents are required?",
)
CALIBRATION_OUT_OF_SCOPE_QUERIES = (
    "What is the weather in Mumbai today?",
    "Who won the latest cricket match?",
)
EVALUATION_QUERIES = (
    ("What affects eligibility for a home loan?", "KB-001"),
    ("How is my EMI calculated?", "KB-002"),
    ("Which KYC documents are required?", "KB-004"),
    ("What charge can apply when I prepay a loan early?", "KB-008"),
    ("How does joint-account authorization work?", "KB-011"),
)


@dataclass(frozen=True)
class KnowledgeBaseDocument:
    """A source Markdown policy document and its stable document identifier."""

    document_id: str
    title: str
    source_filename: str
    text: str


def read_knowledge_base(knowledge_base_dir: Path) -> list[KnowledgeBaseDocument]:
    """Read policy Markdown files whose headings declare a KB document ID."""
    documents: list[KnowledgeBaseDocument] = []
    for path in sorted(knowledge_base_dir.glob("*.md")):
        content = path.read_text(encoding="utf-8").strip()
        match = HEADING_PATTERN.search(content)
        if match is None:
            # README.md is an index, not a policy document, so it has no KB ID.
            continue
        document_id, title = match.groups()
        body = content[match.end() :].strip()
        if not body:
            raise ValueError(f"{path.name} has a KB heading but no policy content")
        documents.append(
            KnowledgeBaseDocument(document_id, title, path.name, body)
        )

    if not documents:
        raise ValueError(f"No KB policy documents found in {knowledge_base_dir}")
    ids = [document.document_id for document in documents]
    if len(ids) != len(set(ids)):
        raise ValueError("Knowledge-base document IDs must be unique")
    return documents


def fixed_character_chunks(
    text: str, size: int = FIXED_CHARACTER_SIZE, overlap: int = FIXED_CHARACTER_OVERLAP
) -> list[str]:
    """Split text into fixed-length character chunks with a character overlap."""
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("Chunk size must be positive and overlap must be smaller than size")
    return [
        text[start : start + size].strip()
        for start in range(0, len(text), size - overlap)
        if text[start : start + size].strip()
    ]


def sentence_chunks(text: str, max_chars: int = SENTENCE_CHUNK_MAX_CHARS) -> list[str]:
    """Group whole sentences without splitting a sentence across chunks."""
    if max_chars <= 0:
        raise ValueError("Sentence chunk maximum must be positive")
    sentences = [sentence.strip() for sentence in SENTENCE_PATTERN.split(text) if sentence.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_length = 0
    for sentence in sentences:
        proposed_length = current_length + len(sentence) + (1 if current else 0)
        if current and proposed_length > max_chars:
            chunks.append(" ".join(current))
            current = []
            current_length = 0
        current.append(sentence)
        current_length += len(sentence) + (1 if current_length else 0)
    if current:
        chunks.append(" ".join(current))
    return chunks


class KnowledgeBaseIndex:
    """Local embedding and retrieval interface for two persistent chunk indexes."""

    def __init__(self, knowledge_base_dir: Path, persist_dir: Path) -> None:
        self.knowledge_base_dir = knowledge_base_dir
        self.client = chromadb.PersistentClient(path=str(persist_dir))
        # The model runs locally. SentenceTransformers downloads it once if it is not cached.
        self.model = SentenceTransformer(MODEL_NAME)

    def _embed(self, texts: Iterable[str]) -> list[list[float]]:
        return self.model.encode(
            list(texts), normalize_embeddings=True, show_progress_bar=False
        ).tolist()

    def build(self) -> None:
        """Rebuild one cosine-space ChromaDB collection for each chunking strategy."""
        documents = read_knowledge_base(self.knowledge_base_dir)
        for strategy in COLLECTION_NAMES:
            collection_name = COLLECTION_NAMES[strategy]
            try:
                self.client.delete_collection(collection_name)
            except NotFoundError:
                pass
            collection = self.client.create_collection(
                name=collection_name, metadata={"hnsw:space": "cosine", "strategy": strategy},
            )

            texts: list[str] = []
            metadata: list[dict[str, Any]] = []
            chunk_ids: list[str] = []
            for document in documents:
                chunks = (
                    fixed_character_chunks(document.text)
                    if strategy == "fixed_character"
                    else sentence_chunks(document.text)
                )
                for chunk_index, chunk_text in enumerate(chunks):
                    texts.append(chunk_text)
                    chunk_ids.append(f"{document.document_id}:{strategy}:{chunk_index:03d}")
                    metadata.append(
                        {
                            "document_id": document.document_id,
                            "source_filename": document.source_filename,
                            "strategy": strategy,
                            "chunk_index": chunk_index,
                        }
                    )
            collection.add(ids=chunk_ids, documents=texts, metadatas=metadata, embeddings=self._embed(texts))
            print(f"Built {collection_name}: {len(texts)} chunks")

    def retrieve(self, query: str, strategy: Strategy, top_k: int = 3) -> list[dict[str, Any]]:
        """Return top chunks with cosine similarity, then print them for the CLI demo."""
        if strategy not in COLLECTION_NAMES:
            raise ValueError(f"Unknown strategy: {strategy}")
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        collection = self.client.get_collection(COLLECTION_NAMES[strategy])
        result = collection.query(
            query_embeddings=self._embed([query]),
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        retrieved: list[dict[str, Any]] = []
        for text, metadata, distance in zip(
            result["documents"][0], result["metadatas"][0], result["distances"][0]
        ):
            # With Chroma's cosine space and normalized vectors, distance is 1 - cosine similarity.
            retrieved.append(
                {
                    "text": text,
                    "document_id": metadata["document_id"],
                    "score": 1 - distance,
                    "metadata": metadata,
                }
            )
        return retrieved


def print_retrieval(query: str, strategy: Strategy, results: list[dict[str, Any]]) -> None:
    """Display retrieval output required for the direct-run demonstration."""
    print(f"\n{strategy} retrieval for: {query}")
    for rank, result in enumerate(results, start=1):
        print(f"{rank}. document_id={result['document_id']} score={result['score']:.4f}")
        print(f"   {result['text']}")


def calibrate_threshold(
    index: KnowledgeBaseIndex, strategy: Strategy
) -> tuple[float, dict[str, float], dict[str, float]]:
    """Choose a threshold strictly between measured in- and out-of-scope scores."""
    in_scope_scores = {
        query: index.retrieve(query, strategy, top_k=1)[0]["score"]
        for query in CALIBRATION_IN_SCOPE_QUERIES
    }
    out_of_scope_scores = {
        query: index.retrieve(query, strategy, top_k=1)[0]["score"]
        for query in CALIBRATION_OUT_OF_SCOPE_QUERIES
    }
    lowest_in_scope = min(in_scope_scores.values())
    highest_out_of_scope = max(out_of_scope_scores.values())
    if highest_out_of_scope >= lowest_in_scope:
        raise ValueError(
            "Cannot select a threshold strictly between the observed similarity clusters"
        )
    threshold = (lowest_in_scope + highest_out_of_scope) / 2
    return threshold, in_scope_scores, out_of_scope_scores


def mock_llm_grounded_answer(
    retrieved_chunks: list[dict[str, Any]], threshold: float
) -> str:
    """Return only retrieved source text, or the exact required no-answer fallback."""
    if not retrieved_chunks or retrieved_chunks[0]["score"] < threshold:
        return FALLBACK_ANSWER
    return retrieved_chunks[0]["text"]


def deduplicate_parent_document_ids(results: list[dict[str, Any]]) -> list[str]:
    """Keep parent IDs in rank order before document-level scoring."""
    return list(dict.fromkeys(result["document_id"] for result in results))


def top_distinct_parent_document_ids(
    index: KnowledgeBaseIndex, query: str, strategy: Strategy, limit: int = 3
) -> list[str]:
    """Retrieve enough chunks to form up to ``limit`` ranked distinct parent IDs."""
    collection = index.client.get_collection(COLLECTION_NAMES[strategy])
    all_ranked_chunks = index.retrieve(query, strategy, top_k=collection.count())
    return deduplicate_parent_document_ids(all_ranked_chunks)[:limit]


def evaluate_strategy(
    index: KnowledgeBaseIndex, strategy: Strategy
) -> tuple[list[dict[str, Any]], float, float]:
    """Evaluate five queries with one relevant parent document per query."""
    evaluations: list[dict[str, Any]] = []
    for query, expected_document_id in EVALUATION_QUERIES:
        parent_ids = top_distinct_parent_document_ids(index, query, strategy, limit=3)
        relevant_hits = int(expected_document_id in parent_ids)
        precision = relevant_hits / 3
        recall = relevant_hits / 1
        evaluations.append(
            {
                "query": query,
                "expected_document_id": expected_document_id,
                "parent_ids": parent_ids,
                "relevant_hits": relevant_hits,
                "precision": precision,
                "recall": recall,
            }
        )
    average_precision = sum(item["precision"] for item in evaluations) / len(evaluations)
    average_recall = sum(item["recall"] for item in evaluations) / len(evaluations)
    return evaluations, average_precision, average_recall


def print_calibration(
    threshold: float, in_scope_scores: dict[str, float], out_of_scope_scores: dict[str, float]
) -> None:
    """Print the measured threshold-calibration evidence."""
    print(f"\nTask 4 calibration ({ANSWER_STRATEGY} strategy):")
    print("In-scope top-1 cosine similarities:")
    for query, score in in_scope_scores.items():
        print(f"  {score:.4f} | {query}")
    print("Out-of-scope top-1 cosine similarities:")
    for query, score in out_of_scope_scores.items():
        print(f"  {score:.4f} | {query}")
    print(f"Selected threshold: {threshold:.4f}")


def print_answer_demo(index: KnowledgeBaseIndex, threshold: float) -> list[dict[str, Any]]:
    """Demonstrate five known-answer queries and one fallback query."""
    demo_queries = [query for query, _ in EVALUATION_QUERIES] + [
        "What is the weather in Mumbai today?"
    ]
    demonstrations: list[dict[str, Any]] = []
    print("\nTask 4 grounded-answer demonstration:")
    for query in demo_queries:
        retrieved = index.retrieve(query, ANSWER_STRATEGY, top_k=1)
        answer = mock_llm_grounded_answer(retrieved, threshold)
        demonstrations.append(
            {"query": query, "top_score": retrieved[0]["score"], "answer": answer}
        )
        print(f"Q: {query}")
        print(f"Top-1 score: {retrieved[0]['score']:.4f}")
        print(f"A: {answer}")
    return demonstrations


def print_evaluation(
    strategy: Strategy, evaluations: list[dict[str, Any]], average_precision: float, average_recall: float
) -> None:
    """Print visible document-level Precision@3 and Recall@3 arithmetic."""
    print(f"\nTask 5 evaluation ({strategy} strategy):")
    for item in evaluations:
        print(f"Q: {item['query']}")
        print(f"Expected parent document: {item['expected_document_id']}")
        print(f"Retrieved parent IDs after deduplication: {item['parent_ids']}")
        print(
            f"Precision@3 = {item['relevant_hits']}/3 = {item['precision']:.3f}; "
            f"Recall@3 = {item['relevant_hits']}/1 = {item['recall']:.3f}"
        )
    print(f"Average Precision@3 = {average_precision:.3f}")
    print(f"Average Recall@3 = {average_recall:.3f}")


def deployment_recommendation(
    metrics: dict[Strategy, tuple[float, float]]
) -> str:
    """Return a short deployment recommendation grounded in measured metrics."""
    fixed_precision, fixed_recall = metrics["fixed_character"]
    sentence_precision, sentence_recall = metrics["sentence"]
    if (fixed_precision, fixed_recall) == (sentence_precision, sentence_recall):
        return (
            "The fixed-character and sentence strategies tie on the measured metrics: "
            f"fixed-character Precision@3 {fixed_precision:.3f}, Recall@3 {fixed_recall:.3f}; "
            f"sentence Precision@3 {sentence_precision:.3f}, Recall@3 {sentence_recall:.3f}. "
            "Choose sentence-based chunking as a qualitative tie-breaker because it preserves "
            "whole sentences. Keep the calibrated fallback enabled and re-evaluate when the "
            "knowledge base changes."
        )
    recommended = max(COLLECTION_NAMES, key=lambda strategy: (metrics[strategy][1], metrics[strategy][0]))
    precision, recall = metrics[recommended]
    return (
        f"Recommend the {recommended} strategy because it achieved the strongest measured "
        f"document-level result (average Precision@3 {precision:.3f}, Recall@3 {recall:.3f}). "
        "Keep the calibrated fallback enabled so queries outside this small fictional policy "
        "set do not receive unsupported answers. Re-evaluate the threshold and metrics when "
        "the knowledge base changes."
    )


def write_report(
    report_path: Path,
    threshold: float,
    in_scope_scores: dict[str, float],
    out_of_scope_scores: dict[str, float],
    demonstrations: list[dict[str, Any]],
    evaluations_by_strategy: dict[Strategy, list[dict[str, Any]]],
    metrics: dict[Strategy, tuple[float, float]],
    recommendation: str,
) -> None:
    """Persist calibration measurements and Task 5 results for reproducibility."""
    lines = [
        "# Cred Capstone Tasks 4 and 5 Report",
        "",
        "## Reproducible configuration",
        "",
        f"- Embedding model: `{MODEL_NAME}` (local SentenceTransformer)",
        f"- Answer strategy: `{ANSWER_STRATEGY}`",
        "- Chroma distance space: `cosine`; displayed score: `1 - distance`",
        "- Evaluation retrieval depth: 3 chunks per strategy",
        "",
        "## Task 4 threshold calibration",
        "",
        "### In-scope top-1 scores",
        "",
    ]
    lines.extend(f"- `{query}`: {score:.4f}" for query, score in in_scope_scores.items())
    lines.extend(["", "### Out-of-scope top-1 scores", ""])
    lines.extend(f"- `{query}`: {score:.4f}" for query, score in out_of_scope_scores.items())
    lines.extend(["", f"Selected threshold: **{threshold:.4f}**", "", "## Grounded-answer demonstration", ""])
    for item in demonstrations:
        lines.extend(
            [
                f"### {item['query']}",
                "",
                f"Top-1 score: {item['top_score']:.4f}",
                "",
                f"Answer: {item['answer']}",
                "",
            ]
        )
    lines.extend(["## Task 5 document-level evaluation", ""])
    for strategy, evaluations in evaluations_by_strategy.items():
        average_precision, average_recall = metrics[strategy]
        lines.extend([f"### {strategy}", ""])
        for item in evaluations:
            lines.extend(
                [
                    f"- Query: {item['query']}",
                    f"  - Expected parent: `{item['expected_document_id']}`",
                    f"  - Deduplicated retrieved parents: {item['parent_ids']}",
                    f"  - Precision@3 = {item['relevant_hits']}/3 = {item['precision']:.3f}",
                    f"  - Recall@3 = {item['relevant_hits']}/1 = {item['recall']:.3f}",
                ]
            )
        lines.extend(
            [
                f"- Average Precision@3: {average_precision:.3f}",
                f"- Average Recall@3: {average_recall:.3f}",
                "",
            ]
        )
    lines.extend(["## Deployment recommendation", "", recommendation, ""])
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build, calibrate, and evaluate the Cred KB.")
    parser.add_argument(
        "--report-file",
        default="task_4_5_report.md",
        help="Path for the reproducible calibration and evaluation report.",
    )
    args = parser.parse_args()
    project_dir = Path(__file__).resolve().parent
    index = KnowledgeBaseIndex(project_dir / "knowledge_base", project_dir / "chroma_indexes")
    index.build()
    threshold, in_scope_scores, out_of_scope_scores = calibrate_threshold(index, ANSWER_STRATEGY)
    print_calibration(threshold, in_scope_scores, out_of_scope_scores)
    demonstrations = print_answer_demo(index, threshold)

    evaluations_by_strategy: dict[Strategy, list[dict[str, Any]]] = {}
    metrics: dict[Strategy, tuple[float, float]] = {}
    for strategy in COLLECTION_NAMES:
        evaluations, average_precision, average_recall = evaluate_strategy(index, strategy)
        evaluations_by_strategy[strategy] = evaluations
        metrics[strategy] = (average_precision, average_recall)
        print_evaluation(strategy, evaluations, average_precision, average_recall)

    recommendation = deployment_recommendation(metrics)
    print(f"\nDeployment recommendation: {recommendation}")
    report_path = project_dir / args.report_file
    write_report(
        report_path,
        threshold,
        in_scope_scores,
        out_of_scope_scores,
        demonstrations,
        evaluations_by_strategy,
        metrics,
        recommendation,
    )
    print(f"Report written to: {report_path}")


if __name__ == "__main__":
    main()
