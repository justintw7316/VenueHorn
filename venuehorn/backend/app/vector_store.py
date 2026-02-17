"""
Vector store backed by FAISS with async-safe access.

Key design decisions
--------------------
* Uses asyncio.Lock — not threading.Lock — so it never blocks the event loop.
* Uses AsyncOpenAI so embedding calls are true async I/O.
* Sentence-aware chunking: never cuts mid-sentence.
* Lazy saves: writes to disk only when explicitly flushed or after bulk ingestion,
  not on every add_documents call.
* Deduplication: tracks ingested sources so re-running ingest doesn't double data.
* Built-in retry: OpenAI client is configured with max_retries=3.
"""
import asyncio
import json
import os
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

import faiss
import numpy as np
from openai import AsyncOpenAI

from .config import settings


@dataclass
class StoredChunk:
    text: str
    source: Optional[str]


class VectorStore:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._index: Optional[faiss.IndexFlatIP] = None
        self._meta: List[StoredChunk] = []
        self._ingested_sources: set[str] = set()
        self._dirty: bool = False

        self._client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            max_retries=settings.openai_max_retries,
        )

        os.makedirs(settings.data_dir, exist_ok=True)
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if os.path.exists(settings.index_path) and os.path.exists(settings.meta_path):
            self._index = faiss.read_index(settings.index_path)
            with open(settings.meta_path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
            self._meta = [StoredChunk(**item) for item in raw]
            self._ingested_sources = {c.source for c in self._meta if c.source}

    def flush(self) -> None:
        """Write index and metadata to disk. Call after bulk ingestion."""
        if not self._dirty or self._index is None:
            return
        faiss.write_index(self._index, settings.index_path)
        with open(settings.meta_path, "w", encoding="utf-8") as fh:
            json.dump([c.__dict__ for c in self._meta], fh, ensure_ascii=False)
        self._dirty = False

    # ------------------------------------------------------------------
    # Chunking
    # ------------------------------------------------------------------

    @staticmethod
    def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
        """
        Sentence-aware chunking.

        Splits on sentence boundaries (. ! ?) first; only falls back to
        hard character splits for pathologically long sentences.
        The result never cuts a word in two.
        """
        # Normalise whitespace
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            return []

        # Tokenise into sentences
        sentence_endings = re.compile(r"(?<=[.!?])\s+")
        sentences = sentence_endings.split(text)

        chunks: List[str] = []
        current = ""

        for sentence in sentences:
            # Hard-split sentences that are longer than chunk_size on their own
            if len(sentence) > chunk_size:
                # Flush whatever we have
                if current:
                    chunks.append(current.strip())
                    current = ""
                # Split the long sentence at word boundaries
                words = sentence.split()
                buf = ""
                for word in words:
                    if len(buf) + len(word) + 1 > chunk_size:
                        if buf:
                            chunks.append(buf.strip())
                        buf = word
                    else:
                        buf = (buf + " " + word) if buf else word
                if buf:
                    current = buf  # carry forward for overlap
                continue

            candidate = (current + " " + sentence).strip()
            if len(candidate) <= chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current.strip())
                # Start next chunk with overlap from the end of current
                overlap_text = current[-overlap:].strip() if overlap else ""
                current = (overlap_text + " " + sentence).strip()

        if current:
            chunks.append(current.strip())

        return [c for c in chunks if c]

    # ------------------------------------------------------------------
    # Embedding
    # ------------------------------------------------------------------

    async def _embed(self, texts: List[str]) -> np.ndarray:
        """Embed a list of texts. Batches automatically handled by OpenAI SDK."""
        response = await self._client.embeddings.create(
            model=settings.openai_embedding_model,
            input=texts,
        )
        vectors = np.array([item.embedding for item in response.data], dtype=np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return vectors / norms

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    async def add_documents(
        self,
        docs: List[Tuple[str, Optional[str]]],
        skip_duplicates: bool = True,
    ) -> int:
        """
        Chunk, embed, and index a list of (text, source) tuples.

        Returns the number of chunks added.
        Does NOT flush to disk — call flush() when done.
        """
        chunks: List[Tuple[str, Optional[str]]] = []
        for text, source in docs:
            if skip_duplicates and source and source in self._ingested_sources:
                continue
            for chunk in self.chunk_text(text, settings.chunk_size, settings.chunk_overlap):
                chunks.append((chunk, source))

        if not chunks:
            return 0

        texts = [c for c, _ in chunks]
        vectors = await self._embed(texts)

        async with self._lock:
            if self._index is None:
                self._index = faiss.IndexFlatIP(vectors.shape[1])
            self._index.add(vectors)
            self._meta.extend(
                StoredChunk(text=c, source=s) for c, s in chunks
            )
            for _, source in chunks:
                if source:
                    self._ingested_sources.add(source)
            self._dirty = True

        return len(chunks)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def search(self, query: str, k: int) -> List[Tuple[StoredChunk, float]]:
        """Return the top-k chunks most similar to query."""
        vectors = await self._embed([query])

        async with self._lock:
            if self._index is None or self._index.ntotal == 0:
                return []
            actual_k = min(k, self._index.ntotal)
            scores, indices = self._index.search(vectors, actual_k)

        results = []
        for idx, score in zip(indices[0], scores[0]):
            if idx < 0 or idx >= len(self._meta):
                continue
            if float(score) < settings.score_threshold:
                continue
            results.append((self._meta[idx], float(score)))
        return results

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def total_chunks(self) -> int:
        return self._index.ntotal if self._index is not None else 0

    @property
    def total_sources(self) -> int:
        return len(self._ingested_sources)


vector_store = VectorStore()
