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
