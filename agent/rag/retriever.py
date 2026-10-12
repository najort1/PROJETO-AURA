"""Módulo de recuperação (retriever) da base de conhecimento com citações auditáveis.

Permite consulta por tópicos e por fact_id direto. Garante que toda citação
possua fact_id, verification_status, valid_from, snapshot_version e source_label.
Citações quebradas (fact_id inexistente ou status ausente) disparam exceção (fail-loud).
"""

from __future__ import annotations

import json
import pickle
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from agent.rag.indexer import INDEX_DIR, index_knowledge_base, verify_index_integrity
from agent.rag.knowledge import KnowledgeChunk
from aura_core.log import get_logger

logger = get_logger("agent.rag.retriever")


@dataclass(frozen=True)
class Citation:
    """Citação auditável vinculada a um fato formal da base de conhecimento."""

    fact_id: str
    text: str
    verification_status: str
    valid_from: str
    snapshot_version: str
    source_label: str
    score: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class KnowledgeRetriever:
    """Recuperador semântico baseado em TF-IDF com busca por relevância e por fact_id."""

    def __init__(self, index_dir: Path | None = None) -> None:
        self.index_dir = index_dir or INDEX_DIR
        self._chunks: list[KnowledgeChunk] = []
        self._chunks_by_fact: dict[str, list[KnowledgeChunk]] = {}
        self._vectorizer: Any = None
        self._tfidf_matrix: np.ndarray | None = None
        self._load_or_index()

    def _load_or_index(self) -> None:
        if not verify_index_integrity(self.index_dir):
            logger.info("Índice inexistente ou inválido. Gerando índice em %s...", self.index_dir)
            index_knowledge_base(self.index_dir)

        chunks_path = self.index_dir / "chunks.json"
        vectorizer_path = self.index_dir / "tfidf_vectorizer.pkl"
        matrix_path = self.index_dir / "tfidf_matrix.npy"

        with open(chunks_path, encoding="utf-8") as f:
            raw_chunks = json.load(f)

        self._chunks = [KnowledgeChunk(**c) for c in raw_chunks]
        self._chunks_by_fact = {}
        for c in self._chunks:
            self._chunks_by_fact.setdefault(c.fact_id, []).append(c)

        with open(vectorizer_path, "wb+" if not vectorizer_path.exists() else "rb") as f:
            self._vectorizer = pickle.load(f)

        self._tfidf_matrix = np.load(matrix_path)

    @property
    def chunks(self) -> list[KnowledgeChunk]:
        return self._chunks

    def get_chunks_by_fact_id(self, fact_id: str) -> list[KnowledgeChunk]:
        """Retorna todos os chunks associados a um fact_id."""
        if not fact_id or fact_id not in self._chunks_by_fact:
            raise KeyError(f"fact_id não encontrado na base de conhecimento: {fact_id!r}")
        return self._chunks_by_fact[fact_id]

    def get_citation_for_fact(
        self,
        fact_id: str,
        preferred_chunk_id: str | None = None,
        preferred_category: str | None = None,
    ) -> Citation:
        """Gera citação estrita para um fact_id. Falha alto se inexistente ou sem status."""
        if not fact_id or fact_id not in self._chunks_by_fact:
            raise ValueError(f"Citação quebrada: fact_id inexistente no regulamento ({fact_id!r})")

        chunks = self._chunks_by_fact[fact_id]
        if not chunks:
            raise ValueError(f"Citação quebrada: nenhum chunk associado a {fact_id!r}")

        primary_chunk = chunks[0]
        if preferred_chunk_id:
            for ch in chunks:
                if ch.chunk_id == preferred_chunk_id:
                    primary_chunk = ch
                    break
        elif preferred_category:
            for ch in chunks:
                if ch.category == preferred_category:
                    primary_chunk = ch
                    break
        status = primary_chunk.verification_status
        if not status or not str(status).strip():
            raise ValueError(f"Citação quebrada: verification_status ausente para {fact_id!r}")

        source_label = (
            primary_chunk.source_labels[0]
            if primary_chunk.source_labels
            else (
                primary_chunk.sources[0] if primary_chunk.sources else "Regulamento Azul Fidelidade"
            )
        )

        # Resumo representativo do texto
        summary = primary_chunk.title
        if "\n## " in primary_chunk.text:
            rules_part = primary_chunk.text.split("\n## ", 1)[-1]
            first_rule = rules_part.split("\n- ", 1)[-1].split("\n")[0].strip()
            if first_rule:
                summary = f"{primary_chunk.title}: {first_rule}"

        return Citation(
            fact_id=primary_chunk.fact_id,
            text=summary,
            verification_status=status,
            valid_from=primary_chunk.valid_from,
            snapshot_version=primary_chunk.snapshot_version,
            source_label=source_label,
            score=1.0,
        )

    def validate_citation(self, fact_id: str) -> Citation:
        """Validador público de citação; alias para get_citation_for_fact."""
        return self.get_citation_for_fact(fact_id)

    def get_canonical_source_labels(self) -> set[str]:
        """Retorna o conjunto de source_labels canônicos presentes no KB.

        Usado pelos guardrails para validar se uma citação tem source_label válido (NEW-18).
        """
        labels: set[str] = set()
        for chunk in self._chunks:
            if chunk.source_labels:
                labels.update(chunk.source_labels)
            elif chunk.sources:
                labels.update(chunk.sources)
        # Garantir fallback padrão
        labels.add("Regulamento Azul Fidelidade")
        return labels

    def search(self, query: str, top_k: int = 3, min_score: float = 0.05) -> list[Citation]:
        """Consulta semântica por query textual com similaridade de cosseno."""
        if not query or not query.strip():
            return []

        if self._vectorizer is None or self._tfidf_matrix is None:
            raise RuntimeError("Índice não carregado adequadamente.")

        q_vec = self._vectorizer.transform([query]).toarray().astype(np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return []

        # Cosine similarity: (A . B) / (|A| * |B|)
        # Como o tfidf_matrix já possui norma L2, a similaridade é o produto escalar
        scores = np.dot(self._tfidf_matrix, q_vec.T).flatten()

        top_indices = np.argsort(scores)[::-1][:top_k]

        citations: list[Citation] = []
        seen_facts: set[str] = set()

        for idx in top_indices:
            score = float(scores[idx])
            if score < min_score:
                continue

            chunk = self._chunks[idx]
            if chunk.fact_id in seen_facts:
                continue
            seen_facts.add(chunk.fact_id)

            if not chunk.verification_status:
                raise ValueError(
                    f"Citação quebrada no índice: fact_id={chunk.fact_id} sem verification_status"
                )

            src_label = (
                chunk.source_labels[0] if chunk.source_labels else "Regulamento Azul Fidelidade"
            )
            citations.append(
                Citation(
                    fact_id=chunk.fact_id,
                    text=f"{chunk.title}: {chunk.text.splitlines()[-1]}",
                    verification_status=chunk.verification_status,
                    valid_from=chunk.valid_from,
                    snapshot_version=chunk.snapshot_version,
                    source_label=src_label,
                    score=round(score, 4),
                )
            )

        return citations


_DEFAULT_RETRIEVER: KnowledgeRetriever | None = None


def get_retriever() -> KnowledgeRetriever:
    """Retorna a instância singleton do KnowledgeRetriever."""
    global _DEFAULT_RETRIEVER
    if _DEFAULT_RETRIEVER is None:
        _DEFAULT_RETRIEVER = KnowledgeRetriever()
    return _DEFAULT_RETRIEVER
