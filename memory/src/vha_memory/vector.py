from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import chromadb
except ImportError:  # pragma: no cover
    chromadb = None


class VectorMemoryStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self._fallback: dict[str, tuple[str, dict[str, Any]]] = {}
        self._collection = None

        if chromadb is not None:
            client = chromadb.PersistentClient(path=str(self.path))
            self._collection = client.get_or_create_collection("tukkie_memories")

    def upsert(self, record_id: str, document: str, metadata: dict[str, Any] | None = None) -> None:
        metadata = metadata or {}
        if self._collection is not None:
            self._collection.upsert(ids=[record_id], documents=[document], metadatas=[metadata])
            return
        self._fallback[record_id] = (document, metadata)

    def query(self, text: str, limit: int = 5) -> list[dict[str, Any]]:
        if self._collection is not None:
            result = self._collection.query(query_texts=[text], n_results=limit)
            ids = result.get("ids", [[]])[0]
            documents = result.get("documents", [[]])[0]
            metadatas = result.get("metadatas", [[]])[0]
            return [
                {"id": identifier, "document": document, "metadata": metadata}
                for identifier, document, metadata in zip(ids, documents, metadatas)
            ]

        terms = {term.lower() for term in text.split() if term.strip()}
        scored: list[tuple[int, str, dict[str, Any], str]] = []
        for identifier, (document, metadata) in self._fallback.items():
            doc_terms = {term.lower() for term in document.split() if term.strip()}
            score = len(terms & doc_terms)
            if score:
                scored.append((score, identifier, metadata, document))
        scored.sort(reverse=True)
        return [
            {"id": identifier, "document": document, "metadata": metadata}
            for _, identifier, metadata, document in scored[:limit]
        ]
