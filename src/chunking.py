from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    # Cat sau dau cau nho lookbehind, nho vay dau "." "!" "?" duoc giu lai
    # trong cau thay vi bi nuot mat nhu khi dung r"[.!?]\s+".
    _SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        sentences = [part.strip() for part in self._SENTENCE_BOUNDARY.split(text)]
        sentences = [sentence for sentence in sentences if sentence]
        if not sentences:
            return []

        size = self.max_sentences_per_chunk
        chunks: list[str] = []
        for start in range(0, len(sentences), size):
            chunk = " ".join(sentences[start : start + size]).strip()
            if chunk:
                chunks.append(chunk)
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = max(1, chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        return self._split(text, list(self.separators))

    def _hard_split(self, current_text: str) -> list[str]:
        """Base case cuoi cung: khong con separator nao thi cat cung theo chunk_size."""
        pieces = [
            current_text[start : start + self.chunk_size].strip()
            for start in range(0, len(current_text), self.chunk_size)
        ]
        return [piece for piece in pieces if piece]

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        # Base case 1 - khong con gi de cat.
        if not current_text or not current_text.strip():
            return []

        # Base case 2 - manh da du nho, dung dung lai.
        if len(current_text) <= self.chunk_size:
            return [current_text.strip()]

        # Base case 3 - het separator (ke ca khi nguoi dung truyen separators=[]).
        if not remaining_separators:
            return self._hard_split(current_text)

        separator = remaining_separators[0]
        rest = remaining_separators[1:]

        # Separator rong la quy uoc "cat cung", str.split("") se nem ValueError.
        if separator == "":
            return self._hard_split(current_text)

        raw_pieces = current_text.split(separator)
        if len(raw_pieces) == 1:
            # Separator nay khong xuat hien -> ha xuong separator nho hon.
            return self._split(current_text, rest)

        # Gan lai separator vao cuoi moi manh (tru manh cuoi) de khong mat dau cham.
        pieces = [piece + separator for piece in raw_pieces[:-1]] + [raw_pieces[-1]]

        chunks: list[str] = []
        buffer = ""
        for piece in pieces:
            if not piece:
                continue

            # Chieu 1 - de quy xuong: manh van qua dai thi cat tiep bang separator nho hon.
            if len(piece) > self.chunk_size:
                if buffer.strip():
                    chunks.append(buffer.strip())
                buffer = ""
                chunks.extend(self._split(piece, rest))
                continue

            # Chieu 2 - gom len: noi cac manh nho lien ke toi sat chunk_size,
            # neu khong mot file nhieu dong ngan se sinh ra hang tram chunk vun.
            if not buffer:
                buffer = piece
            elif len(buffer) + len(piece) <= self.chunk_size:
                buffer += piece
            else:
                chunks.append(buffer.strip())
                buffer = piece

        if buffer.strip():
            chunks.append(buffer.strip())

        return [chunk for chunk in chunks if chunk]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))

    # Chan chia cho 0: vector do dai 0 khong co huong nen khong dinh nghia duoc goc.
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return _dot(vec_a, vec_b) / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=chunk_size // 10),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        comparison: dict = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            count = len(chunks)
            total_length = sum(len(chunk) for chunk in chunks)
            # Chan chia cho 0 khi text rong -> count == 0.
            avg_length = total_length / count if count else 0.0
            comparison[name] = {
                "count": count,
                "avg_length": avg_length,
                "chunks": chunks,
            }
        return comparison
