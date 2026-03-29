from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import SectionChunk


@dataclass
class SearchResult:
    chunk: SectionChunk
    score: float


class LocalRetriever:
    def __init__(self, mode: str | None = None):
        self.mode = (mode or os.getenv("RETRIEVER_MODE", "tfidf")).lower()
        self.vectorizer: TfidfVectorizer | None = None
        self.matrix = None
        self.encoder = None
        self.embeddings = None
        self.chunks: list[SectionChunk] = []

    def fit(self, chunks: list[SectionChunk]) -> None:
        self.chunks = chunks
        texts = [f"{chunk.heading}\n{chunk.text}" for chunk in chunks]
        if self.mode == "embeddings":
            try:
                from sentence_transformers import SentenceTransformer
            except Exception:
                self.mode = "tfidf"
            else:  # pragma: no cover - optional dependency path
                model_name = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")
                self.encoder = SentenceTransformer(model_name)
                self.embeddings = self.encoder.encode(texts, normalize_embeddings=True)
                return
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.matrix = self.vectorizer.fit_transform(texts)

    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        if not self.chunks:
            return []
        if self.mode == "embeddings" and self.encoder is not None and self.embeddings is not None:  # pragma: no cover
            query_embedding = self.encoder.encode([query], normalize_embeddings=True)
            scores = np.dot(self.embeddings, query_embedding[0])
        else:
            assert self.vectorizer is not None and self.matrix is not None
            query_vector = self.vectorizer.transform([query])
            scores = cosine_similarity(query_vector, self.matrix)[0]
        ranked_indices = np.argsort(scores)[::-1][:top_k]
        return [SearchResult(chunk=self.chunks[idx], score=float(scores[idx])) for idx in ranked_indices if scores[idx] > 0]
