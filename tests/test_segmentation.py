"""Testes de unidade e integração para ScoreAV, clusterização e personas (WS5)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from aura_core.paths import ROOT
from ml.segmentation.cluster import (
    prepare_clustering_features,
    run_clustering_pipeline,
)
from ml.segmentation.score_av import (
    analyze_pareto_concentration,
    compute_score_av,
)
from schemas.load import load_contract, validate_or_raise

ALLOWED_PERSONAS = {
    "executivo_recorrente",
    "lazer_premium",
    "maximizador_milhas",
    "regional_dependente",
    "eventual_ascendente",
    "eventual_promocional",
}


@pytest.fixture
def sample_features_and_predictions() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Cria DataFrames sintéticos pequenos e controlados para testes de unidade isolados."""
    n = 100
    cids = [f"C{i:04d}" for i in range(1, n + 1)]
    rng = np.random.RandomState(42)

    feat_df = pd.DataFrame(
        {
            "customer_id": cids,
            "recency_days": rng.randint(1, 300, size=n),
            "frequency_12m": rng.poisson(4, size=n),
            "monetary_12m": rng.uniform(200, 5000, size=n),
            "ticket_medio_12m": rng.uniform(100, 1000, size=n),
            "frequency_trend": rng.uniform(0, 2, size=n),
            "share_rotas_troncais": rng.uniform(0, 1, size=n),
            "share_resgate": rng.uniform(0, 1, size=n),
            "avg_advance_booking_days": rng.uniform(1, 60, size=n),
            "pontos_qualificaveis_12m": rng.randint(500, 20000, size=n),
            "saldo_pontos": rng.randint(1000, 100000, size=n),
            "meta_proximo_nivel_pct": rng.uniform(0, 1, size=n),
            "total_atritos_12m": rng.poisson(1, size=n),
            "tier": rng.choice(["azul", "topazio", "safira", "diamante"], size=n),
        }
    )

    clv_df = pd.DataFrame(
        {
            "customer_id": cids,
            "clv_predicted_12m": rng.uniform(500, 15000, size=n),
        }
    )

    return feat_df, clv_df


def test_score_av_determinism(
    sample_features_and_predictions: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    """Verifica se o cálculo do ScoreAV é 100% determinístico e idempotente."""
    feat_df, clv_df = sample_features_and_predictions

    res1 = compute_score_av(feat_df, clv_df, check_sensitive=True)
    res2 = compute_score_av(feat_df, clv_df, check_sensitive=True)

    pd.testing.assert_frame_equal(res1, res2)
    assert (res1["score_av"] >= 0.0).all() and (res1["score_av"] <= 1.0).all()
    assert res1["alto_valor"].sum() == 10  # 10% de 100 clientes


def test_score_av_sensitive_leakage_assertion_fails(
    sample_features_and_predictions: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    """Garante que a presença de atributos sensíveis (LGPD) levanta AssertionError imediato."""
    feat_df, clv_df = sample_features_and_predictions

    # Injeta atributo sensível proibido
    leaked_feat = feat_df.copy()
    leaked_feat["faixa_etaria"] = "30-49"

    with pytest.raises(AssertionError, match="VIOLAÇÃO DE ÉTICA/LGPD"):
        compute_score_av(leaked_feat, clv_df, check_sensitive=True)

    leaked_clv = clv_df.copy()
    leaked_clv["genero"] = "Feminino"

    with pytest.raises(AssertionError, match="VIOLAÇÃO DE ÉTICA/LGPD"):
        compute_score_av(feat_df, leaked_clv, check_sensitive=True)


def test_clustering_sensitive_leakage_assertion_fails(
    sample_features_and_predictions: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    """Garante que a matriz de clustering recusa qualquer atributo demográfico protegido."""
    feat_df, _ = sample_features_and_predictions
    leaked_feat = feat_df.copy()
    leaked_feat["regiao"] = "Sudeste"

    with pytest.raises(AssertionError, match="VIOLAÇÃO DE ÉTICA/LGPD"):
        prepare_clustering_features(leaked_feat, check_sensitive=True)


def test_pareto_concentration_calculation(
    sample_features_and_predictions: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    """Testa a lógica da curva de Pareto e monotonicidade da receita acumulada."""
    feat_df, clv_df = sample_features_and_predictions
    score_df = compute_score_av(feat_df, clv_df, check_sensitive=False)

    results = analyze_pareto_concentration(feat_df, clv_df, score_df, cutoffs=(0.05, 0.10, 0.20))
    assert len(results) == 3
    # Monotonicidade estrita de receita capturada
    assert (
        results[0]["clv_captured_pct"]
        < results[1]["clv_captured_pct"]
        < results[2]["clv_captured_pct"]
    )


def test_real_artifacts_contracts_validation() -> None:
    """Valida se todos os artefatos de dados gerados passam sem violações nos contratos YAML."""
    data_dir = ROOT / "data" / "analytics"

    contract_files = [
        ("score_av", data_dir / "score_av.parquet"),
        ("segments", data_dir / "segments.parquet"),
        ("personas_summary", data_dir / "personas_summary.parquet"),
        ("customers_scores", data_dir / "customers_scores.parquet"),
        ("customer_timeline", data_dir / "customer_timeline.parquet"),
        ("agent_input", data_dir / "agent_input.parquet"),
    ]

    for c_name, file_path in contract_files:
        assert file_path.exists(), f"Artefato esperado não encontrado: {file_path}"
        contract = load_contract(c_name)
        validate_or_raise(contract, file_path)


def test_personas_reconcile_with_actions_catalog() -> None:
    """Garante que todas as personas geradas casam com os allowed_values do agente e actions.yaml."""
    data_dir = ROOT / "data" / "analytics"
    p_summary = pd.read_parquet(data_dir / "personas_summary.parquet")
    p_names = set(p_summary["persona"].unique())

    assert p_names == ALLOWED_PERSONAS, (
        f"Discrepância nas personas geradas: {p_names} vs {ALLOWED_PERSONAS}"
    )

    agent_input = pd.read_parquet(data_dir / "agent_input.parquet")
    ai_personas = set(agent_input["persona"].unique())
    assert ai_personas.issubset(ALLOWED_PERSONAS)


def test_ari_vs_ground_truth_metric_computed() -> None:
    """Testa se o pipeline de clusterização calcula e reporta o ARI real contra o ground truth."""
    _, metrics = run_clustering_pipeline()
    ari_gt = metrics.get("ari_vs_ground_truth")

    assert ari_gt is not None
    assert isinstance(ari_gt, float)
    # Valor real documentado em torno de 0.16 (honesto e não maquiado)
    assert -0.10 <= ari_gt <= 1.0
    assert metrics["ari_kmeans_vs_gmm"] >= 0.70


def test_timeline_exclui_voos_com_partida_pos_cutoff() -> None:
    """Revisor WS5-B, achado B4-01: voos pré-comprados com PARTIDA após o cutoff
    não podem entrar na timeline (vazariam resultado operacional futuro, ex. atraso).
    Voo comprado ANTES do cutoff e partindo DEPOIS → excluído; partida no próprio
    cutoff → incluído; a guarda fail-loud nega qualquer evento pós-cutoff."""
    from ml.segmentation.timeline import build_customer_timeline

    cutoff = "2025-08-31 23:59:59"
    tx = pd.DataFrame(
        {
            "customer_id": ["C1", "C1", "C2"],
            "transaction_date": ["2025-06-01", "2025-06-01", "2025-08-01"],
            "flight_id": ["F1", "F2", "F3"],
            "pontos_azul_resgatados": [0, 0, 0],
        }
    )
    fl = pd.DataFrame(
        {
            "flight_id": ["F1", "F2", "F3"],
            "origin_airport": ["VCP", "VCP", "CGH"],
            "destination_airport": ["REC", "SDU", "GYN"],
            "departure_date": ["2025-08-31", "2025-09-15", "2025-08-20"],
            "delay_minutes": [30, 90, 0],
            "has_delay": [1, 1, 0],
        }
    )
    inter = pd.DataFrame(
        {"customer_id": [], "interaction_date": [], "has_friction": [], "aspect": [], "channel": []}
    ).astype(object)
    lo = pd.DataFrame(
        {
            "customer_id": [],
            "event_date": [],
            "new_tier": [],
            "previous_tier": [],
            "trigger_reason": [],
        }
    ).astype(object)

    tl = build_customer_timeline(tx, fl, inter, lo, cutoff_date=cutoff)

    voos = tl[tl["tipo"] == "voo"]
    # F1 (partida no cutoff) e F3 (partida antes) permanecem; F2 (partida 15/09) sai.
    assert sorted(voos["titulo"].tolist()) == ["Voo CGH-GYN", "Voo VCP-REC"]
    assert (pd.to_datetime(tl["data"]) <= pd.Timestamp("2025-08-31")).all()
    # O atraso do voo futuro (F2) não pode vazar como evento:
    assert not tl["detalhe"].str.contains("SDU").any()
