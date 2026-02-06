import json
import os
from dataclasses import dataclass
from threading import Lock
from typing import List, Optional, Tuple

import faiss
import numpy as np
from openai import OpenAI

from .config import settings


@dataclass
class StoredChunk:
    text: str
    source: Optional[str]


class VectorStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._index = None
        self._meta: List[StoredChunk] = []
        self._client = OpenAI(api_key=settings.openai_api_key)

        os.makedirs(settings.data_dir, exist_ok=True)
        self._load()

    def _load(self) -> None:
        if os.path.exists(settings.index_path) and os.path.exists(settings.meta_path):
            self._index = faiss.read_index(settings.index_path)
            with open(settings.meta_path, "r", encoding="utf-8") as handle:
                raw = json.load(handle)
            self._meta = [StoredChunk(**item) for item in raw]

    def _save(self) -> None:
        if self._index is None:
            return
        faiss.write_index(self._index, settings.index_path)
        with open(settings.meta_path, "w", encoding="utf-8") as handle:
            json.dump([chunk.__dict__ for chunk in self._meta], handle, ensure_ascii=False, indent=2)

    def _ensure_index(self, dim: int) -> None:
        if self._index is None:
            self._index = faiss.IndexFlatIP(dim)

    @staticmethod
    def _normalize(vectors: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return vectors / norms

    @staticmethod
    def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        chunks = []
        start = 0
        length = len(text)
        while start < length:
            end = min(start + chunk_size, length)
            chunks.append(text[start:end])
            if end == length:
                break
            start = max(end - chunk_overlap, 0)
        return [chunk.strip() for chunk in chunks if chunk.strip()]

    def _embed(self, texts: List[str]) -> np.ndarray:
        response = self._client.embeddings.create(
            model=settings.openai_embedding_model,
            input=texts,
        )
        vectors = np.array([item.embedding for item in response.data], dtype=np.float32)
        return self._normalize(vectors)

    def add_documents(self, docs: List[Tuple[str, Optional[str]]]) -> int:
        chunks: List[Tuple[str, Optional[str]]] = []
        for text, source in docs:
            for chunk in self.chunk_text(text, settings.chunk_size, settings.chunk_overlap):
                chunks.append((chunk, source))

        if not chunks:
            return 0

        texts = [chunk for chunk, _ in chunks]
        vectors = self._embed(texts)

        with self._lock:
            self._ensure_index(vectors.shape[1])
            self._index.add(vectors)
            self._meta.extend([StoredChunk(text=chunk, source=source) for chunk, source in chunks])
            self._save()

        return len(chunks)

    def search(self, query: str, k: int) -> List[Tuple[StoredChunk, float]]:
        vectors = self._embed([query])
        with self._lock:
            if self._index is None or self._index.ntotal == 0:
                return []
            scores, indices = self._index.search(vectors, k)

        results = []
        for idx, score in zip(indices[0], scores[0]):
            if idx < 0 or idx >= len(self._meta):
                continue
            if score < settings.score_threshold:
                continue
            results.append((self._meta[idx], float(score)))
        return results


vector_store = VectorStore()
