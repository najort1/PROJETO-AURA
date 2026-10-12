"""Testes de unidade e auditoria de equidade algorítmica (Fairness / Four-Fifths) (WS5)."""

from __future__ import annotations

import pandas as pd
import pytest

from aura_core.paths import ROOT
from ml.fairness.audit import compute_fairness_metrics
from schemas.load import load_contract, validate_or_raise


def test_four_fifths_exact_calculation_on_controlled_fixture() -> None:
    """Valida a precisão matemática da regra 4/5 em fixture sintética com taxas controladas.

    Cenário:
    - Grupo A: 100 clientes, 100 selecionados (taxa = 1,00) -> Grupo Máximo (Referência).
    - Grupo B: 100 clientes, 70 selecionados (taxa = 0,70) -> Razão = 0,70 / 1,00 = 0,70 (< 0,80 -> Falso).
    - Grupo C: 100 clientes, 85 selecionados (taxa = 0,85) -> Razão = 0,85 / 1,00 = 0,85 (>= 0,80 -> Verdadeiro).
    """
    rows = []
    # Grupo A
    for i in range(100):
        rows.append({"customer_id": f"A{i}", "alto_valor": True, "churn_prob": 0.30, "faixa_etaria": "A", "genero": "M", "regiao": "Sudeste"})
    # Grupo B
    for i in range(100):
        sel = i < 70
        rows.append({"customer_id": f"B{i}", "alto_valor": sel, "churn_prob": 0.40, "faixa_etaria": "B", "genero": "M", "regiao": "Sudeste"})
    # Grupo C
    for i in range(100):
        sel = i < 85
        rows.append({"customer_id": f"C{i}", "alto_valor": sel, "churn_prob": 0.35, "faixa_etaria": "C", "genero": "M", "regiao": "Sudeste"})

    df_test = pd.DataFrame(rows)
    metrics_df = compute_fairness_metrics(df_test, threshold_ratio=0.80)

    age_metrics = metrics_df[metrics_df["sensitive_attribute"] == "faixa_etaria"].set_index("group_value")

    # Grupo A (máximo)
    assert age_metrics.loc["A", "selection_rate"] == 1.00
    assert age_metrics.loc["A", "selection_ratio_vs_max"] == 1.00
    assert bool(age_metrics.loc["A", "four_fifths_compliant"]) is True

    # Grupo B (razão 0,70)
    assert age_metrics.loc["B", "selection_rate"] == 0.70
    assert pytest.approx(age_metrics.loc["B", "selection_ratio_vs_max"], abs=1e-4) == 0.70
    assert bool(age_metrics.loc["B", "four_fifths_compliant"]) is False

    # Grupo C (razão 0,85)
    assert age_metrics.loc["C", "selection_rate"] == 0.85
    assert pytest.approx(age_metrics.loc["C", "selection_ratio_vs_max"], abs=1e-4) == 0.85
    assert bool(age_metrics.loc["C", "four_fifths_compliant"]) is True


def test_fairness_metrics_parquet_contract() -> None:
    """Valida o parquet gerado pelo pipeline contra o contrato schemas/fairness_metrics.yaml."""
    parquet_path = ROOT / "data" / "analytics" / "fairness_metrics.parquet"
    assert parquet_path.exists(), f"Artefato ausente: {parquet_path}"

    contract = load_contract("fairness_metrics")
    validate_or_raise(contract, parquet_path)


def test_fairness_audit_identifies_disparities_honestly() -> None:
    """Verifica que a auditoria reporta fielmente as disparidades reais sem mascaramento."""
    parquet_path = ROOT / "data" / "analytics" / "fairness_metrics.parquet"
    df = pd.read_parquet(parquet_path)

    # Todas as 3 dimensões protegidas devem estar presentes
    dims = set(df["sensitive_attribute"].unique())
    assert dims == {"faixa_etaria", "genero", "regiao"}

    # Grupos que comprovadamente falham a regra dos quatro quintos
    failing = df[~df["four_fifths_compliant"]]
    assert not failing.empty, "A auditoria não pode mascarar disparidades reais."

    # Jovens (18-24) e Região Sul estão entre os grupos identificados com razão < 0,80
    failing_pairs = set(zip(failing["sensitive_attribute"], failing["group_value"], strict=False))
    assert ("faixa_etaria", "18-24") in failing_pairs
    assert ("regiao", "Sul") in failing_pairs
