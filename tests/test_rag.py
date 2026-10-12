"""Testes da base de conhecimento e do motor RAG (agent/rag).

Cobre:
- Chunks citados existem e possuem integridade de hash sha256
- Status de verificação presente e válido em todas as citações
- Falha estrita (fail-loud) ao consultar fact_id inexistente ou quebrado
- Busca semântica por tópicos do regulamento ('qualificação safira', 'resgate especial'...)
- Verificação de integridade do manifesto do índice em data/curated/rag_index/
"""

import pytest

from agent.rag.indexer import verify_index_integrity
from agent.rag.knowledge import build_knowledge_chunks
from agent.rag.retriever import Citation, KnowledgeRetriever, get_retriever
from aura_core.paths import path


@pytest.fixture(scope="module")
def retriever() -> KnowledgeRetriever:
    return get_retriever()


def test_chunks_gerados_com_sucesso():
    """Verifica que os chunks são construídos com campos obrigatórios e hashes válidos."""
    chunks = build_knowledge_chunks()
    assert len(chunks) >= 30, "Esperado no mínimo 30 chunks cobrindo tiers, regras e ações"

    for c in chunks:
        assert c.chunk_id, "chunk_id não pode ser vazio"
        assert c.fact_id, "fact_id não pode ser vazio"
        assert c.title, "title não pode ser vazio"
        assert c.text, "text não pode ser vazio"
        assert c.verification_status, f"verification_status ausente no chunk {c.chunk_id}"
        assert c.valid_from, f"valid_from ausente no chunk {c.chunk_id}"
        assert c.snapshot_version == "research-2026-10-12"
        assert len(c.sha256) == 64, "Hash SHA-256 deve ter 64 caracteres hexadecimais"


def test_chunk_citado_existe(retriever: KnowledgeRetriever):
    """Verifica existência e recuperação de fatos essenciais do regulamento."""
    # Qualificação Safira
    cit_safira = retriever.get_citation_for_fact("AF-TIER-SAFIRA")
    assert isinstance(cit_safira, Citation)
    assert cit_safira.fact_id == "AF-TIER-SAFIRA"
    assert cit_safira.verification_status == "official_historical"
    assert cit_safira.valid_from == "2024-04-01"

    # Resgate Especial
    cit_resgate = retriever.get_citation_for_fact("AF-RESGATE-ESPECIAL-2025")
    assert cit_resgate.fact_id == "AF-RESGATE-ESPECIAL-2025"
    assert cit_resgate.verification_status == "official_current_partial"
    assert cit_resgate.valid_from == "2025-02"

    # Pontos Qualificáveis
    cit_pontos = retriever.get_citation_for_fact("AF-QUALIFYING-POINTS")
    assert cit_pontos.fact_id == "AF-QUALIFYING-POINTS"
    assert cit_pontos.verification_status == "official_historical"

    # Diamante Unique
    cit_du = retriever.get_citation_for_fact("AF-TIER-DIAMANTE-UNIQUE")
    assert cit_du.fact_id == "AF-TIER-DIAMANTE-UNIQUE"
    assert cit_du.verification_status == "official_current_partial"
    assert cit_du.valid_from == "2026"


def test_fact_id_inexistente_dispara_erro(retriever: KnowledgeRetriever):
    """Consulta por fact_id inexistente deve levantar exceção imediatamente (fail-loud)."""
    with pytest.raises(ValueError, match="Citação quebrada: fact_id inexistente"):
        retriever.get_citation_for_fact("AF-REGRA-INEXISTENTE-12345")

    with pytest.raises(KeyError):
        retriever.get_chunks_by_fact_id("AF-REGRA-INEXISTENTE-12345")


def test_busca_semantica_topicos_chave(retriever: KnowledgeRetriever):
    """Busca tópicos do regulamento e valida relevância e citações completas."""
    # 1. 'qualificação safira'
    res_safira = retriever.search("qualificação safira", top_k=2)
    assert len(res_safira) > 0
    assert any(c.fact_id == "AF-TIER-SAFIRA" for c in res_safira)
    assert all(c.verification_status for c in res_safira)

    # 2. 'resgate especial'
    res_resgate = retriever.search("resgate especial cotas anuais", top_k=2)
    assert len(res_resgate) > 0
    assert any("RESGATE" in c.fact_id for c in res_resgate)

    # 3. 'benefícios diamante unique'
    res_du = retriever.search("benefícios diamante unique", top_k=2)
    assert len(res_du) > 0
    assert any(c.fact_id == "AF-TIER-DIAMANTE-UNIQUE" for c in res_du)


def test_integridade_manifesto_indice():
    """Valida se o índice persistido em disco passa no teste de integridade criptográfica."""
    assert verify_index_integrity() is True


def test_busca_validade_dos_pontos_rank1(retriever: KnowledgeRetriever):
    """Verifica que a query 'validade dos pontos' ranqueia AF-VALIDITY-TRANSITION em 1º lugar (ACH-10)."""
    results = retriever.search("validade dos pontos", top_k=3)
    assert len(results) > 0
    top_hit = results[0]
    assert top_hit.fact_id == "AF-VALIDITY-TRANSITION", (
        f"Esperado AF-VALIDITY-TRANSITION em 1º lugar, recebido {top_hit.fact_id}"
    )


def test_preferencia_chunk_beneficios(retriever: KnowledgeRetriever):
    """Verifica que preferred_chunk_id direciona para o chunk de benefícios do tier (ACH-03)."""
    cit = retriever.get_citation_for_fact(
        "AF-TIER-TOPAZIO", preferred_chunk_id="AF-TIER-TOPAZIO:beneficios"
    )
    assert "Benefícios" in cit.text or "Espaço Azul" in cit.text


def test_tamper_detection_em_indice_adulterado(tmp_path):
    """Verifica detecção estrita de violação de integridade criptográfica (ACH-04)."""
    import json
    import shutil

    source_dir = path("data/curated/rag_index")
    # Copia índice para diretório temporário
    shutil.copytree(source_dir, tmp_path / "rag_index")
    test_index_dir = tmp_path / "rag_index"

    # 1. Modifica o texto de um chunk sem alterar o hash declarado
    chunks_path = test_index_dir / "chunks.json"
    with open(chunks_path, encoding="utf-8") as f:
        chunks_data = json.load(f)

    chunks_data[0]["text"] += " [TEXTO ADULTERADO MALICIOSAMENTE]"
    with open(chunks_path, "w", encoding="utf-8") as f:
        json.dump(chunks_data, f, indent=2, ensure_ascii=False)

    with pytest.raises(RuntimeError, match="adulteração detectada"):
        verify_index_integrity(test_index_dir, raise_on_failure=True)

    # 2. Modifica arquivo binário (tfidf_matrix.npy)
    shutil.rmtree(test_index_dir)
    shutil.copytree(source_dir, test_index_dir)
    matrix_path = test_index_dir / "tfidf_matrix.npy"
    with open(matrix_path, "ab") as f:
        f.write(b"\x00\xff\x00\xff")

    with pytest.raises(RuntimeError, match="arquivo binário adulterado"):
        verify_index_integrity(test_index_dir, raise_on_failure=True)
