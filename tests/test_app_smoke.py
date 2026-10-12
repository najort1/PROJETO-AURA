"""Testes de fumaça (smoke tests) para a aplicação Streamlit Aura 2.0 (WS8).

Valida:
- Formatadores pt-BR (moeda BRL, percentuais, inteiros, datas)
- Tokens visuais e badges de categoria
- Loader com fallback de fixtures e fail loud em ausência de arquivos
- Persistência e integridade de decisões em decisions.jsonl
- Consistência lógica dos cálculos de simulação
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import pytest

from app.components import tier_badge
from app.loader import (
    DatasetLoadError,
    get_recorded_decisions,
    load_customers_data,
    load_dataset,
    load_fairness_data,
    load_friction_data,
    load_personas_data,
    load_recommendations_data,
    load_timeline_data,
    record_decision,
)
from app.theme import (
    AZUL_ACTION,
    AZUL_NAVY,
    MAGENTA_CTA,
    TIER_TOKENS,
    format_currency_brl,
    format_date_br,
    format_int_br,
    format_percent,
    get_global_css,
)


# =============================================================================
# 1. TESTES DOS FORMATADORES PT-BR
# =============================================================================
def test_format_currency_brl() -> None:
    assert format_currency_brl(1234.56) == "R$ 1.234,56"
    assert format_currency_brl(0) == "R$ 0,00"
    assert format_currency_brl(1000000.0) == "R$ 1.000.000,00"
    assert format_currency_brl(-50.25) == "-R$ 50,25"
    assert format_currency_brl(None) == "R$ 0,00"
    assert format_currency_brl(float("nan")) == "R$ 0,00"


def test_format_percent() -> None:
    assert format_percent(0.123) == "12,3%"
    assert format_percent(0.854) == "85,4%"
    assert format_percent(15.5) == "15,5%"
    assert format_percent(0.0) == "0,0%"
    assert format_percent(None) == "0,0%"
    assert format_percent(float("nan")) == "0,0%"


def test_format_int_br() -> None:
    assert format_int_br(12345) == "12.345"
    assert format_int_br(1000000) == "1.000.000"
    assert format_int_br(0) == "0"
    assert format_int_br(None) == "0"


def test_format_date_br() -> None:
    assert format_date_br("2026-08-31") == "31/08/2026"
    assert format_date_br(dt.date(2025, 4, 15)) == "15/04/2025"
    assert format_date_br(None) == "-"
    assert format_date_br("invalid") == "invalid"


# =============================================================================
# 2. TESTES DE TOKENS E TIERS
# =============================================================================
def test_tier_tokens_and_badges() -> None:
    for tier_key in ["azul", "topazio", "safira", "diamante", "diamante_unique"]:
        assert tier_key in TIER_TOKENS
        token = TIER_TOKENS[tier_key]
        assert "bg" in token
        assert "text" in token
        badge_html = tier_badge(tier_key, show_level=True)
        assert token["bg"] in badge_html
        assert token["label"] in badge_html

    # Diamante Unique deve conter a tag "Novo" em magenta
    badge_unique = tier_badge("diamante_unique")
    assert "Novo" in badge_unique
    assert MAGENTA_CTA in badge_unique


def test_global_css_generation() -> None:
    css = get_global_css()
    assert AZUL_NAVY in css
    assert AZUL_ACTION in css
    assert MAGENTA_CTA in css
    assert ".section-mark" in css or ".aura-section-mark" in css


# =============================================================================
# 3. TESTES DO LOADER COM FALLBACK TRANSPARENTE
# =============================================================================
def test_load_customers_data() -> None:
    df, is_fixture = load_customers_data()
    assert not df.empty
    assert len(df) >= 100
    expected_cols = {
        "customer_id",
        "tier",
        "persona",
        "clv_12m_previsto",
        "churn_prob",
        "valor_em_risco",
        "score_av",
        "alto_valor",
    }
    assert expected_cols.issubset(df.columns)
    assert isinstance(is_fixture, bool)


def test_load_personas_data() -> None:
    df, _ = load_personas_data()
    assert not df.empty
    assert len(df) >= 4
    assert "nome_display" in df.columns
    assert "clv_medio" in df.columns
    assert "churn_medio" in df.columns
    assert "acao_recomendada" in df.columns


def test_load_timeline_data() -> None:
    df_all, _ = load_timeline_data()
    assert not df_all.empty
    sample_cid = df_all["customer_id"].iloc[0]
    df_cid, _ = load_timeline_data(customer_id=sample_cid)
    assert not df_cid.empty
    assert (df_cid["customer_id"] == sample_cid).all()


def test_load_recommendations_data() -> None:
    df, _ = load_recommendations_data()
    assert not df.empty
    assert "action_id" in df.columns
    assert "message" in df.columns
    assert "justification_json" in df.columns
    assert "citations_json" in df.columns
    assert "human_review" in df.columns


def test_load_friction_data() -> None:
    df, _ = load_friction_data()
    assert not df.empty
    assert "aspect" in df.columns
    assert "semester" in df.columns
    assert "negative_rate" in df.columns


def test_load_fairness_data() -> None:
    df, _ = load_fairness_data()
    assert not df.empty
    assert "sensitive_attribute" in df.columns
    assert "group_value" in df.columns
    assert "selection_ratio_vs_max" in df.columns
    assert "four_fifths_compliant" in df.columns


def test_fail_loud_on_missing_dataset() -> None:
    with pytest.raises(DatasetLoadError) as exc_info:
        load_dataset("tabela_inexistente_xyz_123")
    err_msg = str(exc_info.value)
    assert "ausente" in err_msg
    assert "python tasks.py all" in err_msg


# =============================================================================
# 4. TESTES DE PERSISTÊNCIA DE DECISÕES DO OPERADOR
# =============================================================================
def test_record_decision(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    test_decisions_file = tmp_path / "decisions.jsonl"
    monkeypatch.setattr("app.loader.DECISIONS_FILE", test_decisions_file)
    monkeypatch.setattr("app.loader.ANALYTICS_DIR", tmp_path)

    dec = record_decision(
        customer_id="C999999",
        action_id="ACT-TEST",
        action_name="acao_teste",
        status="approved",
        original_message="Mensagem original de teste.",
        final_message="Mensagem original de teste.",
        operator="auditor_teste",
        notes="Teste unitário",
    )

    assert dec["customer_id"] == "C999999"
    assert dec["status"] == "approved"
    assert dec["edited"] is False
    assert test_decisions_file.exists()

    # Lê arquivo diretamente
    history = get_recorded_decisions()
    assert len(history) >= 1
    last_rec = history[-1]
    assert last_rec["customer_id"] == "C999999"
    assert last_rec["action_id"] == "ACT-TEST"


# =============================================================================
# 5. TESTES DA LÓGICA DE SIMULAÇÃO DE IMPACTO
# =============================================================================
def test_simulation_math_consistency() -> None:
    df_customers, _ = load_customers_data()
    assert not df_customers.empty

    orcamento = 50000.0
    custo_acao = 50.0
    taxa_resp = 0.20
    efeito_acao = 0.30
    margem = 0.20

    n_alvo = min(len(df_customers), int(orcamento // custo_acao))
    df_target = df_customers.sort_values("valor_em_risco", ascending=False).iloc[:n_alvo].copy()

    p_evitada = df_target["churn_prob"] * efeito_acao * taxa_resp
    receita_salva = (p_evitada * df_target["clv_12m_previsto"] * margem).sum()
    custos = n_alvo * custo_acao
    delta_receita = receita_salva - custos

    assert n_alvo == 1000 or n_alvo == len(df_customers)
    assert custos <= orcamento
    assert isinstance(delta_receita, float)
    assert not np.isnan(delta_receita)


# =============================================================================
# 6. TESTES DE INTEGRIDADE ANALÍTICA REAL (WS8b - 50k CLIENTES)
# =============================================================================
def test_real_analytics_dataset_metrics() -> None:
    df_customers, is_fixture = load_customers_data()
    assert is_fixture is False
    assert len(df_customers) == 50000

    # Cruzamento 01: Carteira
    clv_total = float(df_customers["clv_12m_previsto"].sum())
    assert abs(clv_total - 39554463.12) < 0.05

    var_total = float((df_customers["clv_12m_previsto"] * df_customers["churn_prob"]).sum())
    assert abs(var_total - 8305496.50) < 0.05

    av_count = int(df_customers["alto_valor"].sum())
    assert av_count == 5005
    assert abs(df_customers["alto_valor"].mean() - 0.1001) < 0.0001

    # Cruzamento 02: Personas
    df_personas, _ = load_personas_data()
    assert len(df_personas) == 6
    shares = df_personas.set_index("persona")["share_pct"].to_dict()
    assert abs(shares["eventual_promocional"] - 0.4842) < 0.0001
    assert abs(shares["regional_dependente"] - 0.1953) < 0.0001
    assert abs(shares["eventual_ascendente"] - 0.1024) < 0.0001
    assert abs(shares["maximizador_milhas"] - 0.0990) < 0.0001
    assert abs(shares["lazer_premium"] - 0.0929) < 0.0001
    assert abs(shares["executivo_recorrente"] - 0.0262) < 0.0001

    # Cruzamento 03: Linha do tempo sem eventos pós-cutoff
    df_timeline, _ = load_timeline_data()
    assert not df_timeline.empty
    assert (df_timeline["data"].astype(str) <= "2025-08-31").all()

    # Cruzamento 04: Agente de Retenção (50.000 recomendações)
    df_recs, is_r_fixture = load_recommendations_data()
    assert is_r_fixture is False
    assert len(df_recs) == 50000
    assert "ACT-NO-ACTION" in df_recs["action_id"].values
    assert "ACT-AVISO-ANTENCIPADO" in df_recs["action_id"].values
    assert "ACT-ANTECIPACAO-NIVEL" in df_recs["action_id"].values
    c038454_rec = df_recs[df_recs["customer_id"] == "C038454"]
    assert not c038454_rec.empty
    assert c038454_rec.iloc[0]["action_id"] == "ACT-ATRATRIBUI-ATRASO"

    # Cruzamento 05: Friction Map (49 linhas e pesos)
    df_friction, _ = load_friction_data()
    assert len(df_friction) == 49
    weights = df_friction.groupby("aspect")["aspect_weight"].first().to_dict()
    assert abs(weights["atraso"] - 0.1965) < 0.0001
    assert abs(weights["conforto"] - 0.0502) < 0.0001
    assert abs(sum(weights.values()) - 1.0) < 0.001

    # Cruzamento 07: IA Responsável (14 informados, 9 conformes, 5 não conformes)
    df_fairness, _ = load_fairness_data()
    assert len(df_fairness) == 16
    is_nao_inf = df_fairness["group_value"].str.lower().str.contains("informado", na=False) & ~df_fairness["group_value"].str.lower().str.contains("prefiro", na=False)
    assert is_nao_inf.sum() == 2
    df_inf = df_fairness[~is_nao_inf]
    assert len(df_inf) == 14
    assert df_inf["four_fifths_compliant"].sum() == 9
    assert (~df_inf["four_fifths_compliant"]).sum() == 5
