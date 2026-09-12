"""Build and query local ChromaDB indexes for the Cred capstone knowledge base."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Literal

import chromadb
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
            except ValueError:
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and demo local Cred KB indexes.")
    parser.add_argument(
        "--query",
        default="What charge can apply when I prepay a loan early?",
        help="Query demonstrated against both chunking strategies.",
    )
    parser.add_argument("--top-k", type=int, default=3, help="Chunks to return per strategy.")
    args = parser.parse_args()

    project_dir = Path(__file__).resolve().parent
    index = KnowledgeBaseIndex(project_dir / "knowledge_base", project_dir / "chroma_indexes")
    index.build()
    for strategy in COLLECTION_NAMES:
        print_retrieval(args.query, strategy, index.retrieve(args.query, strategy, args.top_k))


if __name__ == "__main__":
    main()
