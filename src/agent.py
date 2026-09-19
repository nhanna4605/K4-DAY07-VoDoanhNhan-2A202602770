from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    EMPTY_CONTEXT_ANSWER = (
        "Khong tim thay thong tin lien quan trong co so tri thuc. "
        "Vui long bo sung tai lieu hoac dat lai cau hoi."
    )

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def _build_context(self, results: list[dict]) -> str:
        """
        Danh so tung chunk [1] [2] [3] kem nguon.

        Nho danh so nay, cau tra loi co the trich dan "[2]" va nguoi doc truy nguoc
        ve dung chunk / dung file -> tieu chi Source Traceability trong
        docs/EVALUATION.md. Voi corpus quy dinh dai hoc thi day khong phai tinh
        nang phu: tra loi sai quy dinh ma khong truy duoc nguon la vo dung.
        """
        blocks = []
        for order, result in enumerate(results, start=1):
            metadata = result.get("metadata") or {}
            source = (
                metadata.get("source_url")
                or metadata.get("source")
                or metadata.get("doc_id")
                or result.get("id")
                or "khong ro nguon"
            )
            header = f"[{order}] nguon: {source}"
            audience = metadata.get("audience")
            if audience:
                header += f" | audience: {audience}"
            blocks.append(f"{header}\n{result.get('content', '')}")
        return "\n\n".join(blocks)

    def answer(self, question: str, top_k: int = 3) -> str:
        # 1. Truy xuat top-k chunk lien quan.
        results = self.store.search(question, top_k=top_k)

        # Store rong / khong co ket qua: tra thong bao, khong crash va khong goi
        # LLM vo ich.
        if not results:
            return self.EMPTY_CONTEXT_ANSWER

        # 2. Dung prompt co ngu canh + rang buoc chong bia.
        context = self._build_context(results)
        prompt = (
            "Ban la tro ly tra loi cau hoi ve dich vu va quy dinh dai hoc.\n"
            "Chi su dung NGU CANH duoi day de tra loi. Tuyet doi khong suy doan "
            "hay bo sung thong tin ngoai ngu canh.\n"
            "Neu ngu canh khong du de tra loi, hay noi ro la khong tim thay thong tin.\n"
            "Khi tra loi, trich dan so hieu doan da dung, vi du [1] hoac [2].\n\n"
            f"NGU CANH:\n{context}\n\n"
            f"CAU HOI: {question}\n\n"
            "TRA LOI (kem trich dan):"
        )

        # 3. Goi LLM.
        return self.llm_fn(prompt)
