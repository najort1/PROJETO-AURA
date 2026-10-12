"""Auditoria de equidade algorítmica e conformidade com a regra Four-Fifths (WS5).

Objetivos:
1. Avaliar impacto desproporcional (Disparate Impact) na seleção de clientes de Alto Valor.
2. Dimensões protegidas: faixa_etaria, genero, regiao.
3. Regra dos Quatro Quintos (Four-Fifths Rule / limiar 0,80):
   selection_ratio_vs_max = selection_rate_grupo / selection_rate_maximo >= 0.80.
4. Análise honesta sem manipulação artificial do score — reporte explícito de disparidades.
5. Persistência de data/analytics/fairness_metrics.parquet conforme contrato e loader do app.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from aura_core.paths import ROOT
from schemas.load import load_contract, validate_or_raise

SENSITIVE_DIMENSIONS = ["faixa_etaria", "genero", "regiao"]

# Rótulo de dado não informado (LGPD): clientes sem atributo demográfico declarado.
# Não é um grupo demográfico — fica fora do denominador da regra 4/5 e das
# contagens de conformidade (mantido na tabela apenas por transparência).
NA_LABEL = "não informado"


def compute_fairness_metrics(
    customers_scores_df: pd.DataFrame,
    threshold_ratio: float = 0.80,
) -> pd.DataFrame:
    """Calcula as métricas de disparidade e conformidade Four-Fifths por dimensão sensível.

    Parâmetros:
        customers_scores_df: DataFrame contendo [customer_id, alto_valor, churn_prob, faixa_etaria, genero, regiao].
        threshold_ratio: Limiar regulatório da regra 4/5 (padrão 0.80).

    Retorna:
        DataFrame com colunas:
        ['sensitive_attribute', 'group_value', 'group_size', 'alto_valor_count',
         'selection_rate', 'avg_predicted_churn', 'selection_ratio_vs_max', 'four_fifths_compliant'].
    """
    rows: list[dict[str, Any]] = []

    for dim in SENSITIVE_DIMENSIONS:
        assert dim in customers_scores_df.columns, f"Dimensão demográfica '{dim}' ausente em customers_scores."

        informed = customers_scores_df[customers_scores_df[dim] != NA_LABEL]
        group_rates = informed.groupby(dim)["alto_valor"].mean()
        # Baseline da regra 4/5: taxa máxima entre grupos INFORMADOS (o grupo
        # "não informado" é artefato de completude, não grupo demográfico).
        max_rate = float(group_rates.max()) if not group_rates.empty else 0.0

        for g_val in sorted(customers_scores_df[dim].dropna().unique()):
            sub_g = customers_scores_df[customers_scores_df[dim] == g_val]
            cnt = len(sub_g)
            av_cnt = int(sub_g["alto_valor"].sum())
            sel_rate = float(av_cnt / cnt) if cnt > 0 else 0.0
            avg_churn = float(sub_g["churn_prob"].mean()) if cnt > 0 else 0.0
            ratio = float(sel_rate / max_rate) if max_rate > 0 else 1.0
            # Grupo "não informado": linha mantida por transparência, mas fora do
            # julgamento demográfico da regra 4/5 (compliant=True; sem grupo de
            # comparação legítimo) e fora das contagens de conformidade do summary.
            compliant = bool(ratio >= threshold_ratio) if g_val != NA_LABEL else True

            rows.append(
                {
                    "sensitive_attribute": dim,
                    "group_value": str(g_val),
                    "group_size": int(cnt),
                    "alto_valor_count": int(av_cnt),
                    "selection_rate": round(sel_rate, 4),
                    "avg_predicted_churn": round(avg_churn, 4),
                    "selection_ratio_vs_max": round(ratio, 4),
                    "four_fifths_compliant": compliant,
                }
            )

    return pd.DataFrame(rows)


def run_fairness_audit(
    output_dir: Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Executa a auditoria completa de fairness e persiste fairness_metrics.parquet."""
    data_dir = ROOT / "data" / "analytics"
    out_dir = output_dir or data_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    cs_path = data_dir / "customers_scores.parquet"
    if not cs_path.exists():
        raise FileNotFoundError(
            f"Arquivo {cs_path} ausente. Execute python -m ml.segmentation.score_av antes da auditoria."
        )

    cs_df = pd.read_parquet(cs_path)
    metrics_df = compute_fairness_metrics(cs_df)

    out_file = out_dir / "fairness_metrics.parquet"
    metrics_df.to_parquet(out_file, index=False)
    validate_or_raise(load_contract("fairness_metrics"), out_file)

    informed_df = metrics_df[metrics_df["group_value"] != NA_LABEL]
    total_groups = len(informed_df)
    compliant_groups = int(informed_df["four_fifths_compliant"].sum())
    failing_groups = informed_df[~informed_df["four_fifths_compliant"]]
    na_rows = metrics_df[metrics_df["group_value"] == NA_LABEL]

    summary: dict[str, Any] = {
        "total_groups_audited": total_groups,
        "compliant_count": compliant_groups,
        "non_compliant_count": total_groups - compliant_groups,
        "compliance_rate": round(compliant_groups / max(1, total_groups), 4),
        "na_group_rows": len(na_rows),
        "na_note": (
            f"Grupos '{NA_LABEL}' (dado não declarado, LGPD) reportados por transparência "
            "e excluídos do denominador e das contagens da regra 4/5."
        ),
        "failing_groups": failing_groups[
            ["sensitive_attribute", "group_value", "selection_rate", "selection_ratio_vs_max"]
        ].to_dict(orient="records"),
    }

    print(f"Auditoria de Fairness concluída: {compliant_groups}/{total_groups} grupos conformes (4/5).")
    print(f"Artefato gravado em: {out_file}")
    if not failing_groups.empty:
        print("Grupos abaixo do limiar 0,80 (Four-Fifths):")
        for _, r in failing_groups.iterrows():
            print(f"  - [{r['sensitive_attribute']}] {r['group_value']}: razão {r['selection_ratio_vs_max']:.4f} (taxa: {r['selection_rate']:.4f})")

    return metrics_df, summary


if __name__ == "__main__":
    run_fairness_audit()
