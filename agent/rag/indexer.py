"""Indexador de chunks da base de conhecimento do Azul Fidelidade.

Gera índice local TF-IDF com matrizes numpy persistidas em data/curated/rag_index/,
garantindo integridade criptográfica (sha256) de cada chunk e do índice completo.
Executável via: python -m agent.rag.indexer (ou python tasks.py rag)
"""

from __future__ import annotations

import datetime
import hashlib
import json
import pickle
from pathlib import Path

import numpy as np

from agent.rag.knowledge import KnowledgeChunk, build_knowledge_chunks, compute_chunk_hash
from aura_core.log import get_logger
from aura_core.paths import ensure_dir, path

logger = get_logger("agent.rag.indexer")

INDEX_DIR = path("data/curated/rag_index")


def _file_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while b := f.read(65536):
            h.update(b)
    return h.hexdigest()


def index_knowledge_base(output_dir: Path | None = None) -> dict[str, int | str]:
    """Constrói os chunks, vetoriza com TF-IDF e persiste o índice com manifest de integridade."""
    target_dir = output_dir or INDEX_DIR
    ensure_dir(target_dir)

    logger.info("Construindo chunks da base de conhecimento...")
    chunks: list[KnowledgeChunk] = build_knowledge_chunks()

    if not chunks:
        raise ValueError("Nenhum chunk de conhecimento foi gerado a partir das regras!")

    # Prepara textos combinando título ponderado, id, keywords e conteúdo (ACH-10)
    corpus: list[str] = []
    for c in chunks:
        kw_str = " ".join(c.metadata.get("keywords", []))
        # Ponderação do título (4x) e keywords maximiza especificidade semântica
        corpus.append(f"{c.fact_id} {c.title} {c.title} {c.title} {c.title} {kw_str} {c.text}")

    logger.info("Vetorizando %d chunks com TfidfVectorizer...", len(chunks))
    from sklearn.feature_extraction.text import TfidfVectorizer

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        sublinear_tf=True,
        norm="l2",
    )
    tfidf_matrix = vectorizer.fit_transform(corpus).toarray().astype(np.float32)

    # Serializa chunks em JSON
    chunks_data = [c.to_dict() for c in chunks]
    chunks_path = target_dir / "chunks.json"
    with open(chunks_path, "w", encoding="utf-8") as f:
        json.dump(chunks_data, f, ensure_ascii=False, indent=2)

    # Salva vectorizer e matriz TF-IDF
    vectorizer_path = target_dir / "tfidf_vectorizer.pkl"
    with open(vectorizer_path, "wb") as f:
        pickle.dump(vectorizer, f)

    matrix_path = target_dir / "tfidf_matrix.npy"
    np.save(matrix_path, tfidf_matrix)

    # Calcula hash global do índice para integridade
    all_hashes_concat = "".join(sorted(c.sha256 for c in chunks))
    overall_index_hash = hashlib.sha256(all_hashes_concat.encode("utf-8")).hexdigest()

    file_hashes = {
        "tfidf_vectorizer.pkl": _file_sha256(vectorizer_path),
        "tfidf_matrix.npy": _file_sha256(matrix_path),
    }

    manifest = {
        "snapshot_version": chunks[0].snapshot_version,
        "total_chunks": len(chunks),
        "vocab_size": len(vectorizer.vocabulary_),
        "matrix_shape": list(tfidf_matrix.shape),
        "overall_index_hash": overall_index_hash,
        "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "chunk_hashes": {c.chunk_id: c.sha256 for c in chunks},
        "file_hashes": file_hashes,
    }
    manifest_path = target_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    logger.info(
        "Índice RAG concluído com sucesso em %s (%d chunks, vocabulário=%d, hash=%s...)",
        target_dir,
        len(chunks),
        len(vectorizer.vocabulary_),
        overall_index_hash[:12],
    )

    return {
        "status": "success",
        "total_chunks": len(chunks),
        "vocab_size": len(vectorizer.vocabulary_),
        "index_hash": overall_index_hash,
        "output_dir": str(target_dir),
    }


def verify_index_integrity(
    index_dir: Path | None = None,
    raise_on_failure: bool = False,
) -> bool:
    """Verifica se os arquivos do índice existem e se os hashes dos chunks batem com o manifest."""
    target_dir = index_dir or INDEX_DIR
    manifest_path = target_dir / "manifest.json"
    chunks_path = target_dir / "chunks.json"
    vectorizer_path = target_dir / "tfidf_vectorizer.pkl"
    matrix_path = target_dir / "tfidf_matrix.npy"

    if (
        not manifest_path.exists()
        or not chunks_path.exists()
        or not vectorizer_path.exists()
        or not matrix_path.exists()
    ):
        msg = "Arquivo essencial ausente no diretório do índice RAG"
        logger.warning(msg)
        if raise_on_failure:
            raise RuntimeError(msg)
        return False

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    with open(chunks_path, encoding="utf-8") as f:
        chunks_data = json.load(f)

    chunk_hashes = manifest.get("chunk_hashes", {})
    if len(chunks_data) != manifest.get("total_chunks"):
        msg = "Quantidade de chunks no índice diverge do manifest"
        logger.error(msg)
        if raise_on_failure:
            raise RuntimeError(msg)
        return False

    recalculated_hashes: list[str] = []
    for c in chunks_data:
        cid = c.get("chunk_id")
        text = c.get("text", "")
        fact_id = c.get("fact_id", "")
        status = c.get("verification_status", "")
        valid_from = c.get("valid_from", "")

        # Recálculo criptográfico real do hash a partir do texto e metadados canônicos (ACH-04)
        computed_hash = compute_chunk_hash(text, fact_id, status, valid_from)

        # Checagem contra o atributo sha256 do chunk
        if computed_hash != c.get("sha256"):
            msg = f"Hash recalculado do chunk {cid} diverge de c['sha256'] (adulteração detectada)"
            logger.error(msg)
            if raise_on_failure:
                raise RuntimeError(msg)
            return False

        # Checagem contra o manifesto
        expected_hash = chunk_hashes.get(cid)
        if not expected_hash or expected_hash != computed_hash:
            msg = f"Hash recalculado do chunk {cid} diverge do manifest (adulteração detectada)"
            logger.error(msg)
            if raise_on_failure:
                raise RuntimeError(msg)
            return False

        recalculated_hashes.append(computed_hash)

    # Verificação do overall_index_hash
    recomputed_overall = hashlib.sha256(
        "".join(sorted(recalculated_hashes)).encode("utf-8")
    ).hexdigest()
    if recomputed_overall != manifest.get("overall_index_hash"):
        msg = "overall_index_hash recalculado diverge do manifest (adulteração detectada)"
        logger.error(msg)
        if raise_on_failure:
            raise RuntimeError(msg)
        return False

    # Verificação dos hashes de arquivos binários (.pkl e .npy)
    file_hashes = manifest.get("file_hashes", {})
    if (
        "tfidf_vectorizer.pkl" in file_hashes
        and _file_sha256(vectorizer_path) != file_hashes["tfidf_vectorizer.pkl"]
    ):
        msg = "Hash de tfidf_vectorizer.pkl diverge do manifest (arquivo binário adulterado)"
        logger.error(msg)
        if raise_on_failure:
            raise RuntimeError(msg)
        return False
    if (
        "tfidf_matrix.npy" in file_hashes
        and _file_sha256(matrix_path) != file_hashes["tfidf_matrix.npy"]
    ):
        msg = "Hash de tfidf_matrix.npy diverge do manifest (arquivo binário adulterado)"
        logger.error(msg)
        if raise_on_failure:
            raise RuntimeError(msg)
        return False

    return True


def main() -> None:
    res = index_knowledge_base()
    print("=" * 60)
    print("AURA 2.0 :: RAG INDEXER CONCLUÍDO COM SUCESSO")
    print(f"Total de Chunks:   {res['total_chunks']}")
    print(f"Tamanho Vocábulo:  {res['vocab_size']}")
    print(f"Hash do Índice:    {res['index_hash']}")
    print(f"Diretório Salvo:   {res['output_dir']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
