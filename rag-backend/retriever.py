import json
import os
from pathlib import Path
from typing import Any

import numpy as np
from openai import OpenAI

from github_loader import collect_project_documents

client = OpenAI()

EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
INDEX_PATH = Path(os.getenv("INDEX_PATH", "data/project_vector_index.json"))


def _embed_texts(texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]


def _cosine_similarity(query_vector: list[float], matrix: list[list[float]]) -> np.ndarray:
    q = np.array(query_vector, dtype=np.float32)
    m = np.array(matrix, dtype=np.float32)
    q_norm = np.linalg.norm(q)
    m_norm = np.linalg.norm(m, axis=1)
    denominator = np.maximum(q_norm * m_norm, 1e-8)
    return np.dot(m, q) / denominator


async def rebuild_index() -> dict[str, Any]:
    documents = await collect_project_documents()
    if not documents:
        raise RuntimeError("No project documents were collected. Check project_sources.json and repository paths.")

    texts = [doc["text"] for doc in documents]
    embeddings = _embed_texts(texts)

    index = {
        "embedding_model": EMBEDDING_MODEL,
        "document_count": len(documents),
        "documents": [
            {**doc, "embedding": embedding}
            for doc, embedding in zip(documents, embeddings)
        ],
    }

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with INDEX_PATH.open("w", encoding="utf-8") as file:
        json.dump(index, file, ensure_ascii=False)

    return {"status": "ok", "document_count": len(documents), "index_path": str(INDEX_PATH)}


def load_index() -> dict[str, Any]:
    if not INDEX_PATH.exists():
        raise FileNotFoundError(
            f"Vector index not found at {INDEX_PATH}. Run POST /api/reindex first."
        )

    with INDEX_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def retrieve(question: str, top_k: int = 5) -> list[dict[str, Any]]:
    index = load_index()
    documents = index["documents"]
    query_embedding = _embed_texts([question])[0]
    embeddings = [doc["embedding"] for doc in documents]
    scores = _cosine_similarity(query_embedding, embeddings)

    ranked_indices = np.argsort(scores)[::-1][:top_k]
    results: list[dict[str, Any]] = []

    for rank, doc_idx in enumerate(ranked_indices, start=1):
        doc = documents[int(doc_idx)]
        results.append(
            {
                "rank": rank,
                "score": float(scores[int(doc_idx)]),
                "project": doc.get("project"),
                "repo": doc.get("repo"),
                "url": doc.get("url"),
                "category": doc.get("category"),
                "status": doc.get("status"),
                "source_path": doc.get("source_path"),
                "text": doc.get("text"),
            }
        )

    return results


def format_context(results: list[dict[str, Any]]) -> str:
    blocks = []
    for item in results:
        blocks.append(
            "\n".join(
                [
                    f"[Source {item['rank']} | score={item['score']:.3f}]",
                    f"Project: {item.get('project')}",
                    f"Category: {item.get('category')}",
                    f"Status: {item.get('status')}",
                    f"Repo: {item.get('url')}",
                    f"Source file: {item.get('source_path')}",
                    item.get("text", "")[:2200],
                ]
            )
        )
    return "\n\n---\n\n".join(blocks)
