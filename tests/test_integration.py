"""Testes de INTEGRAÇÃO cross-artefato (Projeto Aura 2.0).

Estes testes verificam a CONSISTÊNCIA entre os artefatos analíticos reais gerados
pelo pipeline completo — o contratório que uma suíte unitária não cobre. Eles
leem data/analytics/*.parquet e data/curated/* e falham se qualquer frente
produzir artefatos incoerentes entre si (WS2↔WS3/4↔WS5↔WS6↔WS7).

Contexto de honestidade: a base é SINTÉTICA (v3, determinística). Estes testes
validam a COERÊNCIA DO PIPELINE, não desempenho no mundo real.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from aura_core.paths import ROOT

ANALYTICS = ROOT / "data" / "analytics"
CURATED_SYNTH = ROOT / "data" / "curated" / "synthetic"
CURATED = ROOT / "data" / "curated"


def _read(name: str, base: Path = ANALYTICS) -> pd.DataFrame:
    path = base / f"{name}.parquet"
    if not path.exists():
        pytest.fail(
            f"Artefato ausente: {path} — rode `python tasks.py all` antes dos testes de integração."
        )
    return pd.read_parquet(path)


@pytest.fixture(scope="module")
def customers_scores() -> pd.DataFrame:
    return _read("customers_scores")


@pytest.fixture(scope="module")
def score_av() -> pd.DataFrame:
    return _read("score_av")


@pytest.fixture(scope="module")
def segments() -> pd.DataFrame:
    return _read("segments")


@pytest.fixture(scope="module")
def agent_input() -> pd.DataFrame:
    return _read("agent_input")


# ---------------------------------------------------------------------------
# 1. Chaves e cobertura: a carteira é UMA em todos os artefatos de cliente
# ---------------------------------------------------------------------------


def test_ids_de_cliente_identicos_em_todos_os_artefatos(
    customers_scores: pd.DataFrame,
    score_av: pd.DataFrame,
    segments: pd.DataFrame,
    agent_input: pd.DataFrame,
) -> None:
    """customers_scores, score_av, segments e agent_input cobrem EXATAMENTE a mesma carteira."""
    for df, name in [(score_av, "score_av"), (segments, "segments"), (agent_input, "agent_input")]:
        assert set(df["customer_id"]) == set(customers_scores["customer_id"]), (
            f"customer_id divergente entre customers_scores e {name}"
        )
        assert len(df) == len(customers_scores) == 50_000
        assert df["customer_id"].is_unique


def test_base_sintetica_cobre_a_carteira(customers_scores: pd.DataFrame) -> None:
    cs_ids = set(customers_scores["customer_id"])
    customers = pd.read_parquet(CURATED_SYNTH / "customers.parquet", columns=["customer_id"])
    assert set(customers["customer_id"]) == cs_ids


# ---------------------------------------------------------------------------
# 2. Scores: valores propagam sem divergência entre frentes
# ---------------------------------------------------------------------------


def test_score_av_e_alto_valor_coerentes(
    customers_scores: pd.DataFrame, score_av: pd.DataFrame
) -> None:
    merged = customers_scores.merge(score_av, on="customer_id", suffixes=("_cs", "_sa"))
    assert (merged["score_av_cs"] - merged["score_av_sa"]).abs().max() < 1e-9
    assert (merged["alto_valor_cs"] == merged["alto_valor_sa"]).all()
    # Corte top-10% com empates documentados (5.005 = 5.000 + 5 empates no limiar 0,8840)
    share = customers_scores["alto_valor"].mean()
    assert 0.099 <= share <= 0.101, f"share alto_valor={share:.4f} fora do esperado (~10,01%)"


def test_previsoes_clv_churn_propagam_para_customers_scores(customers_scores: pd.DataFrame) -> None:
    clv = _read("clv_predictions")
    merged = customers_scores.merge(clv, on="customer_id")
    assert len(merged) == 50_000
    m_clv = (merged["clv_12m_previsto"] - merged["clv_predicted_12m"]).abs().max()
    assert m_clv < 1e-6, f"CLV divergiu entre customers_scores e clv_predictions: {m_clv}"


def test_valor_em_risco_formula_canonica(customers_scores: pd.DataFrame) -> None:
    """valor_em_risco = clv_12m_previsto × churn_prob (a fórmula exibida na tela 01)."""
    esperado = customers_scores["clv_12m_previsto"] * customers_scores["churn_prob"]
    assert (customers_scores["valor_em_risco"] - esperado).abs().max() < 0.01


# ---------------------------------------------------------------------------
# 3. Personas e segmentos: reconciliação com o playbook
# ---------------------------------------------------------------------------


def test_personas_cobrem_toda_a_base_e_batem_com_playbook(customers_scores: pd.DataFrame) -> None:
    personas_summary = _read("personas_summary")
    actions = (ROOT / "config" / "actions.yaml").read_text(encoding="utf-8")
    counts = customers_scores["persona"].value_counts()
    for name in counts.index:
        assert name in personas_summary["persona"].values
        assert name in actions, f"persona {name} ausente do playbook config/actions.yaml"
    assert counts.sum() == 50_000
    assert abs(personas_summary["share_pct"].sum() - 1.0) < 0.005


def test_clusters_alinhados_com_segments(segments: pd.DataFrame) -> None:
    assert {"cluster_kmeans", "cluster_gmm", "segment_name"} <= set(segments.columns)
    assert segments["segment_id"].nunique() == 6


# ---------------------------------------------------------------------------
# 4. Anti-vazamento global: nada em analytics pode ter data pós-cutoff
# ---------------------------------------------------------------------------


def test_timeline_sem_eventos_pos_cutoff() -> None:
    timeline = _read("customer_timeline")
    max_data = pd.to_datetime(timeline["data"]).max()
    assert max_data <= pd.Timestamp("2025-08-31"), (
        f"vazamento temporal: max(data)={max_data.date()}"
    )


def test_atributos_sensiveis_ausentes_das_features() -> None:
    features = _read("features_customer")
    banned = {
        "faixa_etaria",
        "genero",
        "regiao",
        "arquetipo",
        "clv_real_12m",
        "hazard_latente",
        "churn_latente",
    }
    vazou = banned & {c.lower() for c in features.columns}
    assert not vazou, f"atributos proibidos nas features: {vazou}"


# ---------------------------------------------------------------------------
# 5. Fairness: números da auditoria são reproduzíveis
# ---------------------------------------------------------------------------


def test_fairness_reproduzivel(customers_scores: pd.DataFrame) -> None:
    fm = _read("fairness_metrics")
    informed = fm[fm["group_value"] != "não informado"]
    assert len(fm) == 16 and len(informed) == 14
    for dim in ("faixa_etaria", "genero", "regiao"):
        rates = (
            customers_scores[customers_scores[dim] != "não informado"]
            .groupby(dim)["alto_valor"]
            .mean()
        )
        base = rates.max()
        for g_val, rate in rates.items():
            row = informed[
                (informed["sensitive_attribute"] == dim) & (informed["group_value"] == g_val)
            ]
            assert len(row) == 1
            assert abs(row["selection_rate"].iloc[0] - round(rate, 4)) < 1e-6
            assert abs(row["selection_ratio_vs_max"].iloc[0] - round(rate / base, 4)) < 1e-4


# ---------------------------------------------------------------------------
# 6. Mapa de atritos (WS6): consistência com os pesos curados
# ---------------------------------------------------------------------------


def test_friction_map_e_peso_total() -> None:
    fm = _read("friction_map")
    weights_path = CURATED / "friction_weights.json"
    assert weights_path.exists(), "data/curated/friction_weights.json ausente"
    payload = json.loads(weights_path.read_text(encoding="utf-8"))
    weights = payload["weights"] if isinstance(payload, dict) and "weights" in payload else payload
    if isinstance(weights, dict):
        total = sum(weights.values())
        assert abs(total - 1.0) < 0.01, f"pesos de atrito somam {total:.4f} (esperado 1,0)"
    aspects = set(fm["aspect"].str.lower()) if "aspect" in fm.columns else set()
    assert {"atraso", "resgate_milhas"} <= aspects


# ---------------------------------------------------------------------------
# 7. Recomendações do agente (WS7b/WS8b): contrato e fail-safes sobre a base real
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def recommendations() -> pd.DataFrame:
    return _read("agent_recommendations")


def test_recomendacoes_cobrem_a_carteira_com_ids_validos(
    customers_scores: pd.DataFrame, recommendations: pd.DataFrame
) -> None:
    assert len(recommendations) == 50_000
    assert recommendations["customer_id"].is_unique
    assert set(recommendations["customer_id"]) == set(customers_scores["customer_id"])


def test_recomendacoes_somente_do_inventario_e_offline(recommendations: pd.DataFrame) -> None:
    import yaml

    data = yaml.safe_load((ROOT / "config" / "actions.yaml").read_text(encoding="utf-8"))
    actions = data.get("actions", data) if isinstance(data, dict) else data
    if isinstance(actions, dict):
        inventory = {v["id"] for v in actions.values() if isinstance(v, dict) and "id" in v}
    else:
        inventory = {a["id"] for a in actions}
    inventory |= {"ACT-NO-ACTION"}
    fora = set(recommendations["action_id"]) - inventory
    assert not fora, f"recomendações fora do inventário (regra de ouro violada): {fora}"
    assert (recommendations["mode"] == "offline").all()
    assert (recommendations["snapshot_version"] == "research-2026-10-12").all()


def test_recomendacoes_fail_safe_no_action_exige_revisao_humana(
    recommendations: pd.DataFrame,
) -> None:
    """ACH-01: todo silêncio responsável (ACT-NO-ACTION) aciona revisão humana."""
    no_action = recommendations[recommendations["action_id"] == "ACT-NO-ACTION"]
    assert no_action["human_review"].all(), (
        "existe ACT-NO-ACTION sem revisão humana (fail-safe violado)"
    )
    com_cit = recommendations[recommendations["citations_json"].astype(str).str.len() > 4]
    for row in com_cit.head(200).itertuples():
        cit = json.loads(row.citations_json)
        assert isinstance(cit, list) and cit, (
            "citations_json deve ser lista não vazia quando presente"
        )


def test_scores_consomem_exatamente_as_predicoes_publicadas(customers_scores: pd.DataFrame) -> None:
    """Guarda de corrida de processos: customers_scores deve refletir EXATAMENTE
    as predições publicadas em clv_predictions/churn_predictions.

    Detectou (e agora previne) a mistura de saídas de dois treinos concorrentes
    — ver docs/limitations.md §7b, Achado 3.
    """
    clv = _read("clv_predictions")[["customer_id", "clv_predicted_12m"]]
    churn = _read("churn_predictions")[["customer_id", "churn_prob_model"]]
    m = (
        customers_scores[["customer_id", "clv_12m_previsto", "churn_prob"]]
        .merge(clv, on="customer_id")
        .merge(churn, on="customer_id")
    )
    assert len(m) == 50_000, "joins 1:1 quebrados — bases divergem em cardinalidade"
    diff_clv = (m["clv_12m_previsto"] - m["clv_predicted_12m"]).abs()
    diff_churn = (m["churn_prob"] - m["churn_prob_model"].round(4)).abs()
    assert float(diff_clv.max()) <= 0.005, f"CLV publicado difere do previsto em {diff_clv.max()}"
    assert float(diff_churn.max()) <= 0.00005, (
        f"churn publicado difere do modelo em {diff_churn.max()} (treino concorrente/estagnado?)"
    )
