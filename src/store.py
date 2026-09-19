from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Backend: in-memory list of records.

    Nhanh ChromaDB da duoc bo han. Khong test nao can no, requirements.txt khong
    cai no, va code khoi tao goc gan self._use_chroma = True TRUOC khi client
    duoc tao -> neu may cham bai tinh co co chromadb thi moi method se re vao
    nhanh chua cai dat va 14 test store deu sap.

    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Chuan hoa mot Document thanh record luu trong store."""
        # Copy metadata thay vi dung truc tiep dict cua caller: neu khong, sua
        # metadata cua record se sua luon object ben ngoai store.
        metadata = dict(doc.metadata or {})

        # delete_document() xoa theo metadata['doc_id'] nen record luon phai co
        # khoa nay. O tang benchmark, mot file sinh nhieu Document id kieu
        # "file#0", "file#1" nhung doc_id van tro ve TEN FILE GOC de xoa ca cum.
        metadata.setdefault("doc_id", doc.id)

        record = {
            "id": doc.id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": self._embedding_fn(doc.content),
            "index": self._next_index,
        }
        self._next_index += 1
        return record

    def _search_records(
        self, query: str, records: list[dict[str, Any]], top_k: int
    ) -> list[dict[str, Any]]:
        """
        Similarity search tren mot tap record bat ky.

        Tach rieng vi search() va search_with_filter() chi khac nhau o TAP UNG VIEN
        dau vao; cho ca hai di chung mot duong code thi ket qua khong the lech nhau.
        """
        if not records or top_k <= 0:
            return []

        query_embedding = self._embedding_fn(query)

        scored: list[dict[str, Any]] = []
        for record in records:
            # Embedding da duoc chuan hoa (||v|| = 1) nen dot product = cosine.
            score = _dot(query_embedding, record["embedding"])
            scored.append(
                {
                    "id": record["id"],
                    "content": record["content"],
                    # Bo khoa "embedding": vector hang tram chieu lam ban terminal.
                    "metadata": dict(record["metadata"]),
                    "score": score,
                }
            )

        scored.sort(key=lambda result: result["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        Luu y: KHONG tu chunk o day. 1 Document = 1 record. Viec chunking xay ra
        o tang ngoai (bench.py), moi chunk tro thanh mot Document rieng.
        """
        for doc in docs or []:
            self._store.append(self._make_record(doc))

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        Compute dot product of query embedding vs all stored embeddings.
        """
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(
        self, query: str, top_k: int = 3, metadata_filter: dict = None
    ) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        LOC TRUOC roi moi search. Neu lam nguoc lai (lay top-k roi bo cai khong
        khop) thi co the con 0 ket qua du store van con tai lieu hop le, vi k slot
        da bi chiem het boi tai lieu sai doi tuong.
        """
        if not metadata_filter:
            candidates = self._store
        else:
            candidates = [
                record
                for record in self._store
                if all(
                    record["metadata"].get(key) == value
                    for key, value in metadata_filter.items()
                )
            ]

        return self._search_records(query, candidates, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        kept = [
            record
            for record in self._store
            if record["metadata"].get("doc_id") != doc_id
        ]

        if len(kept) == len(self._store):
            return False

        self._store = kept
        return True
