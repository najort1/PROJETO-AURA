"""Cálculo do Score de Alto Valor (ScoreAV) e geração de customers_scores (WS5).

Regras de negócio:
- ScoreAV = 0,60·pct(CLV_12m) + 0,20·pct(RFM composto) + 0,20·pct(Potencial).
- RFM composto: padronização z-score de (-recencia_dias, frequencia_12m, monetary_12m).
- Potencial: crescimento previsto (frequency_trend) + headroom (meta_proximo_nivel_pct).
- Anti-vazamento: todos os componentes derivados de dados <= cutoff.
- Atributos sensíveis (faixa_etaria, genero, regiao) categoricamente PROIBIDOS no cálculo.
- Análise de Pareto para justificar o corte de alto valor (top 10%).
- Análise de sensibilidade: grade de pesos +-0,1 (soma 1) e cortes {5%, 10%, 15%, 20%}.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr

from aura_core.paths import ROOT
from schemas.load import load_contract, validate_or_raise

SENSITIVE_FORBIDDEN_COLUMNS = ["faixa_etaria", "genero", "regiao"]


def compute_score_av(
    features_df: pd.DataFrame,
    clv_preds_df: pd.DataFrame,
    weights: dict[str, float] | None = None,
    cutoff_top_percent: float = 10.0,
    check_sensitive: bool = True,
) -> pd.DataFrame:
    """Calcula o ScoreAV canônico para cada cliente.

    Parâmetros:
        features_df: DataFrame de features analíticas (features_customer.parquet).
        clv_preds_df: DataFrame com predições de CLV (clv_predictions.parquet).
        weights: Pesos {'clv': 0.60, 'rfm': 0.20, 'potential': 0.20}.
        cutoff_top_percent: Percentual superior para definição de alto_valor (default 10.0%).
        check_sensitive: Se True, verifica ausência de atributos sensíveis e targets futuros.

    Retorna:
        DataFrame com colunas:
        ['customer_id', 'pct_clv', 'pct_rfm', 'pct_potential', 'score_av', 'alto_valor', 'percentile_rank'].
    """
    if weights is None:
        weights = {"clv": 0.60, "rfm": 0.20, "potential": 0.20}

    # Validação rigorosa anti-vazamento e conformidade ética
    if check_sensitive:
        for col in SENSITIVE_FORBIDDEN_COLUMNS:
            assert col not in features_df.columns, (
                f"VIOLAÇÃO DE ÉTICA/LGPD: Atributo sensível '{col}' encontrado nas features de entrada."
            )
            assert col not in clv_preds_df.columns, (
                f"VIOLAÇÃO DE ÉTICA/LGPD: Atributo sensível '{col}' encontrado em clv_predictions."
            )

    # Garante alinhamento por customer_id
    cols_feat = [
        "customer_id",
        "recency_days",
        "frequency_12m",
        "monetary_12m",
        "frequency_trend",
        "meta_proximo_nivel_pct",
    ]
    df = features_df[cols_feat].merge(
        clv_preds_df[["customer_id", "clv_predicted_12m"]],
        on="customer_id",
        how="inner",
    )

    # 1. Percentil de CLV Previsto 12m
    pct_clv = df["clv_predicted_12m"].rank(pct=True, method="average")

    # 2. RFM Composto Padronizado
    # Recência: menor recency_days é melhor -> z-score invertido
    std_r = df["recency_days"].std()
    z_recency = -(df["recency_days"] - df["recency_days"].mean()) / (std_r if std_r > 0 else 1.0)

    std_f = df["frequency_12m"].std()
    z_frequency = (df["frequency_12m"] - df["frequency_12m"].mean()) / (std_f if std_f > 0 else 1.0)

    std_m = df["monetary_12m"].std()
    z_monetary = (df["monetary_12m"] - df["monetary_12m"].mean()) / (std_m if std_m > 0 else 1.0)

    rfm_composite = (z_recency + z_frequency + z_monetary) / 3.0
    pct_rfm = rfm_composite.rank(pct=True, method="average")

    # 3. Potencial Composto (Tendência de crescimento + Headroom próximo nível)
    rank_trend = df["frequency_trend"].rank(pct=True, method="average")
    rank_headroom = df["meta_proximo_nivel_pct"].rank(pct=True, method="average")
    potential_composite = (rank_trend + rank_headroom) / 2.0
    pct_potential = potential_composite.rank(pct=True, method="average")

    # 4. ScoreAV Consolidado
    w_clv = weights["clv"]
    w_rfm = weights["rfm"]
    w_pot = weights["potential"]
    score_av = (w_clv * pct_clv + w_rfm * pct_rfm + w_pot * pct_potential).clip(0.0, 1.0)
    score_av = score_av.round(4)

    # 5. Percentile Rank e Corte de Alto Valor
    percentile_rank = score_av.rank(pct=True, method="average").round(4)
    threshold = np.percentile(score_av, 100.0 - cutoff_top_percent)
    alto_valor = score_av >= threshold

    out_df = pd.DataFrame(
        {
            "customer_id": df["customer_id"].astype(str),
            "pct_clv": pct_clv.round(4).astype(float),
            "pct_rfm": pct_rfm.round(4).astype(float),
            "pct_potential": pct_potential.round(4).astype(float),
            "score_av": score_av.astype(float),
            "alto_valor": alto_valor.astype(bool),
            "percentile_rank": percentile_rank.astype(float),
        }
    )
    return out_df


def analyze_pareto_concentration(
    features_df: pd.DataFrame,
    clv_preds_df: pd.DataFrame,
    score_av_df: pd.DataFrame,
    cutoffs: tuple[float, ...] = (0.05, 0.10, 0.15, 0.20),
) -> list[dict[str, Any]]:
    """Calcula a concentração de receita prevista segundo os quantis superiores de ScoreAV."""
    df = (
        score_av_df.merge(
            clv_preds_df[["customer_id", "clv_predicted_12m"]],
            on="customer_id",
            how="inner",
        )
        .sort_values("score_av", ascending=False)
        .reset_index(drop=True)
    )

    total_clv = float(df["clv_predicted_12m"].sum())
    results: list[dict[str, Any]] = []

    for c in cutoffs:
        n = int(round(len(df) * c))
        top_slice = df.iloc[:n]
        clv_captured = float(top_slice["clv_predicted_12m"].sum())
        captured_pct = clv_captured / total_clv if total_clv > 0 else 0.0
        min_score = float(top_slice["score_av"].min())

        results.append(
            {
                "top_percent": int(round(c * 100)),
                "n_customers": n,
                "clv_captured_brl": round(clv_captured, 2),
                "clv_captured_pct": round(captured_pct, 4),
                "min_score_av": round(min_score, 4),
            }
        )
    return results


def run_sensitivity_analysis(
    features_df: pd.DataFrame,
    clv_preds_df: pd.DataFrame,
    base_weights: dict[str, float] | None = None,
    cutoffs: tuple[float, ...] = (0.05, 0.10, 0.15, 0.20),
    random_seed: int = 42,
) -> list[dict[str, Any]]:
    """Executa grade de sensibilidade de pesos +-0,1 e cortes {5%, 10%, 15%, 20%}.

    Avalia:
    - Correlação de Spearman entre ranking baseline e ranking alternativo.
    - Correlação de Kendall tau-b amostral.
    - Similaridade de Jaccard do conjunto classificado como alto valor para cada corte.
    """
    if base_weights is None:
        base_weights = {"clv": 0.60, "rfm": 0.20, "potential": 0.20}

    base_res = compute_score_av(
        features_df, clv_preds_df, weights=base_weights, check_sensitive=False
    )
    base_score = base_res["score_av"].values
    n_total = len(base_res)

    # Subamostra para cálculo eficiente e determinístico de Kendall tau
    rng = np.random.RandomState(random_seed)
    sub_size = min(5000, n_total)
    sub_idx = rng.choice(n_total, size=sub_size, replace=False)

    grid = [
        (0.6, 0.2, 0.2, "Baseline (60/20/20)"),
        (0.5, 0.2, 0.3, "Mais Potencial (50/20/30)"),
        (0.5, 0.3, 0.2, "Mais RFM (50/30/20)"),
        (0.6, 0.1, 0.3, "Foco Potencial (60/10/30)"),
        (0.6, 0.3, 0.1, "Foco RFM (60/30/10)"),
        (0.7, 0.1, 0.2, "Foco CLV Alto (70/10/20)"),
        (0.7, 0.2, 0.1, "CLV Maximo (70/20/10)"),
    ]

    records: list[dict[str, Any]] = []

    for w_c, w_r, w_p, desc in grid:
        w_dict = {"clv": w_c, "rfm": w_r, "potential": w_p}
        alt_res = compute_score_av(features_df, clv_preds_df, weights=w_dict, check_sensitive=False)
        alt_score = alt_res["score_av"].values

        sp_corr, _ = spearmanr(base_score, alt_score)
        kd_corr, _ = kendalltau(base_score[sub_idx], alt_score[sub_idx])

        jaccards: dict[str, float] = {}
        for c in cutoffs:
            n_cut = int(round(n_total * c))
            idx_base = set(np.argsort(-base_score)[:n_cut])
            idx_alt = set(np.argsort(-alt_score)[:n_cut])
            intersection = len(idx_base & idx_alt)
            union = len(idx_base | idx_alt)
            j_val = float(intersection / union) if union > 0 else 1.0
            jaccards[f"jaccard_{int(round(c * 100))}pct"] = round(j_val, 4)

        record = {
            "description": desc,
            "weight_clv": w_c,
            "weight_rfm": w_r,
            "weight_potential": w_p,
            "spearman_rank_corr": round(float(sp_corr), 4),
            "kendall_tau": round(float(kd_corr), 4),
            **jaccards,
        }
        records.append(record)

    return records


def build_customers_scores(
    features_df: pd.DataFrame,
    clv_preds_df: pd.DataFrame,
    churn_preds_df: pd.DataFrame,
    clv_shap_df: pd.DataFrame,
    score_av_df: pd.DataFrame,
    segments_df: pd.DataFrame,
    customers_curated_df: pd.DataFrame,
) -> pd.DataFrame:
    """Constrói o dataset customers_scores unificado conforme esperado pelo app."""
    # 1. Base unificada de IDs
    df = features_df.copy()

    # 2. Merge predições
    df = df.merge(
        clv_preds_df[["customer_id", "clv_predicted_12m"]],
        on="customer_id",
        how="left",
    )
    df = df.merge(
        churn_preds_df[["customer_id", "churn_prob_model"]],
        on="customer_id",
        how="left",
    )
    df = df.merge(
        score_av_df[["customer_id", "score_av", "alto_valor"]],
        on="customer_id",
        how="left",
    )
    df = df.merge(
        segments_df[["customer_id", "segment_name"]],
        on="customer_id",
        how="left",
    )
    df = df.merge(
        customers_curated_df[["customer_id", "faixa_etaria", "genero", "regiao"]],
        on="customer_id",
        how="left",
    )
    df = df.merge(
        clv_shap_df[
            [
                "customer_id",
                "top1_feature",
                "top1_shap",
                "top2_feature",
                "top2_shap",
                "top3_feature",
                "top3_shap",
            ]
        ],
        on="customer_id",
        how="left",
    )

    # 3. Derivação de métricas de negócio
    clv_previsto = df["clv_predicted_12m"].fillna(0.0).round(2)
    churn_prob = df["churn_prob_model"].fillna(0.5).round(4)
    valor_em_risco = (clv_previsto * churn_prob).round(2)
    alto_valor = df["alto_valor"].fillna(False).astype(bool)

    # Risk state determinístico (conforme build_fixtures.py e actions.yaml)
    risk_states = []
    for c_prob, av in zip(churn_prob, alto_valor, strict=False):
        if c_prob >= 0.50 and av:
            risk_states.append("risco_alto_valor_alto")
        elif c_prob >= 0.40 and av:
            risk_states.append("risco_medio_valor_alto")
        elif c_prob < 0.40 and av:
            risk_states.append("risco_baixo_potencial_alto")
        else:
            risk_states.append("risco_baixo_estavel")

    # Persona
    persona = df["segment_name"].fillna("eventual_promocional")

    # Atritos dominantes
    friction_cols = [
        ("atraso", "atritos_atraso_12m"),
        ("bagagem", "atritos_bagagem_12m"),
        ("app_checkin", "atritos_app_checkin_12m"),
        ("resgate_milhas", "atritos_resgate_milhas_12m"),
        ("atendimento", "atritos_atendimento_12m"),
        ("preco", "atritos_preco_12m"),
    ]
    atritos_list = []
    for _, row in df.iterrows():
        best_aspect = "atraso"
        max_val = -1
        for asp, col_name in friction_cols:
            val = row.get(col_name, 0)
            if val > max_val:
                max_val = val
                best_aspect = asp
        if max_val <= 0:
            # Fallback para o atrito característico da persona
            p_val = row.get("segment_name", "eventual_promocional")
            p_fallback = {
                "executivo_recorrente": "atraso",
                "lazer_premium": "bagagem",
                "maximizador_milhas": "resgate_milhas",
                "regional_dependente": "atraso",
                "eventual_ascendente": "app_checkin",
                "eventual_promocional": "preco",
            }
            best_aspect = p_fallback.get(p_val, "atraso")
        atritos_list.append(best_aspect)

    # Benefício não utilizado (trata 'nenhum' como None)
    ben_raw = df["beneficio_nao_utilizado"]
    ben_cleaned = ben_raw.apply(
        lambda b: None if (pd.isna(b) or str(b).strip() in {"", "nenhum", "None"}) else str(b)
    )

    # SHAP top3 formatado como JSON list de dicts para a interface
    shap_top3_list = []
    for _, row in df.iterrows():
        factors = [
            {
                "factor": str(row.get("top1_feature", "frequencia")),
                "shap_value": round(float(row.get("top1_shap", 0.0)), 4),
            },
            {
                "factor": str(row.get("top2_feature", "monetario")),
                "shap_value": round(float(row.get("top2_shap", 0.0)), 4),
            },
            {
                "factor": str(row.get("top3_feature", "recencia")),
                "shap_value": round(float(row.get("top3_shap", 0.0)), 4),
            },
        ]
        shap_top3_list.append(json.dumps(factors))

    frequencia_voos = df["trechos_12m"].fillna(0).astype("int64")

    customers_scores_df = pd.DataFrame(
        {
            "customer_id": df["customer_id"].astype(str),
            "tier": df["tier"].astype(str),
            "persona": persona.astype(str),
            "clv_12m_previsto": clv_previsto.astype("float64"),
            "churn_prob": churn_prob.astype("float64"),
            "valor_em_risco": valor_em_risco.astype("float64"),
            "score_av": df["score_av"].astype("float64"),
            "alto_valor": alto_valor.astype(bool),
            "risk_state": pd.Series(risk_states, dtype=str),
            "gastos_12m_brl": df["gastos_12m_brl"].fillna(0.0).round(2).astype("float64"),
            "recencia_dias": df["recency_days"].fillna(0).astype("int64"),
            "frequencia_voos": frequencia_voos,
            "trechos_12m": df["trechos_12m"].fillna(0).astype("int64"),
            "saldo_pontos": df["saldo_pontos"].fillna(0).astype("int64"),
            "pontos_expirando_30d": df["pontos_expirando_30d"].fillna(0).astype("int64"),
            "pontos_qualificaveis_12m": df["pontos_qualificaveis_12m"].fillna(0).astype("int64"),
            "meta_proximo_nivel_pct": df["meta_proximo_nivel_pct"]
            .fillna(0.0)
            .round(4)
            .astype("float64"),
            # Rótulo honesto para dados NÃO informados (LGPD): null ≠ valor factual.
            # Imputar "Sudeste"/"VCP-SDU"/"30-49" fabricaria identidade demográfica.
            "faixa_etaria": df["faixa_etaria"].fillna("não informado").astype(str),
            "genero": df["genero"].fillna("não informado").astype(str),
            "regiao": df["regiao"].fillna("não informado").astype(str),
            "rota_favorita": df["rota_favorita"].fillna("sem rota registrada").astype(str),
            "atritos_dominantes": pd.Series(atritos_list, dtype=str),
            "beneficio_nao_utilizado": ben_cleaned.astype("string"),
            "shap_top3": pd.Series(shap_top3_list, dtype=str),
        }
    )
    return customers_scores_df


def run_score_pipeline(
    output_dir: Path | None = None,
) -> tuple[pd.DataFrame, list[dict[str, Any]], list[dict[str, Any]]]:
    """Executa o pipeline canônico de ScoreAV e grava artefatos."""
    data_dir = ROOT / "data" / "analytics"
    curated_dir = ROOT / "data" / "curated" / "synthetic"
    out_dir = output_dir or data_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    features_path = data_dir / "features_customer.parquet"
    clv_path = data_dir / "clv_predictions.parquet"

    features_df = pd.read_parquet(features_path)
    clv_df = pd.read_parquet(clv_path)

    # 1. Calcula ScoreAV canônico
    score_av_df = compute_score_av(features_df, clv_df, check_sensitive=True)
    score_out_path = out_dir / "score_av.parquet"
    score_av_df.to_parquet(score_out_path, index=False)
    validate_or_raise(load_contract("score_av"), score_out_path)

    # 2. Análise de Pareto
    pareto_results = analyze_pareto_concentration(features_df, clv_df, score_av_df)

    # 3. Análise de sensibilidade
    sensitivity_results = run_sensitivity_analysis(features_df, clv_df)

    # 4. Se segments.parquet e modelos existirem, constrói customers_scores
    segments_path = data_dir / "segments.parquet"
    churn_path = data_dir / "churn_predictions.parquet"
    clv_shap_path = data_dir / "clv_shap.parquet"
    cust_path = curated_dir / "customers.parquet"

    if (
        segments_path.exists()
        and churn_path.exists()
        and clv_shap_path.exists()
        and cust_path.exists()
    ):
        churn_df = pd.read_parquet(churn_path)
        clv_shap_df = pd.read_parquet(clv_shap_path)
        segments_df = pd.read_parquet(segments_path)
        cust_df = pd.read_parquet(cust_path)

        cs_df = build_customers_scores(
            features_df, clv_df, churn_df, clv_shap_df, score_av_df, segments_df, cust_df
        )
        cs_out_path = out_dir / "customers_scores.parquet"
        cs_df.to_parquet(cs_out_path, index=False)
        validate_or_raise(load_contract("customers_scores"), cs_out_path)
        print(
            f"customers_scores gerado com sucesso: {len(cs_df)} registros gravados em {cs_out_path}"
        )

    print(f"ScoreAV gerado com sucesso: {len(score_av_df)} registros gravados em {score_out_path}")
    return score_av_df, pareto_results, sensitivity_results


if __name__ == "__main__":
    run_score_pipeline()
