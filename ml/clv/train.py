"""Treinamento e avaliação de modelos de CLV (WS4 - Projeto Aura 2.0).

Pipeline:
1. Validação temporal estrita: treino na coorte de validação (2025-02-28), teste na coorte principal (2025-08-31).
2. Baseline estatístico: BG/NBD + Gamma-Gamma monetizado 12m.
3. Modelo final: LightGBM Regressor com restrições determinísticas.
4. Métricas auditáveis com Bootstrap IC95: WAPE, MAE, Spearman, Gini de captura, Lift@Decil 1.
5. TreeSHAP nativo (global + local top-3 por cliente).
6. Persistência e validação contra contrato schemas/clv_predictions.yaml.
"""

from __future__ import annotations

import json
from typing import Any

import lightgbm as lgb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from aura_core.config import child_seed, settings
from aura_core.log import get_logger
from aura_core.paths import ensure_dir, path
from ml.clv.bgnbd_gamma import BGNBDGammaGammaPipeline
from ml.common.metrics import (
    bootstrap_metric_difference,
    gini_revenue_capture,
    lift_by_decile,
    mae,
    spearman_rank_corr,
    wape,
)
from ml.common.registry import save_model_bundle
from ml.common.shap_utils import (
    compute_shap_contributions,
    global_feature_importance,
    local_top_k,
    plot_global_summary,
    plot_waterfall,
)
from schemas.load import load_contract, validate_or_raise

log = get_logger("ml.clv.train")

FEATURE_COLUMNS = [
    "recency_days",
    "frequency_3m",
    "frequency_6m",
    "frequency_12m",
    "monetary_12m",
    "ticket_medio_12m",
    "frequency_trend",
    "frequency_volatility",
    "share_rotas_troncais",
    "share_resgate",
    "avg_advance_booking_days",
    "pontos_qualificaveis_12m",
    "saldo_pontos",
    "pontos_expirando_30d",
    "meta_proximo_nivel_pct",
    "days_since_last_interaction",
    "atritos_atraso_12m",
    "atritos_bagagem_12m",
    "atritos_app_checkin_12m",
    "atritos_resgate_milhas_12m",
    "atritos_atendimento_12m",
    "atritos_preco_12m",
    "total_atritos_12m",
    "tier_encoded",
]


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """Prepara matriz de features numéricas e codificadas sem vazamento."""
    X = df.copy()

    tier_map = {"azul": 1, "topazio": 2, "safira": 3, "diamante": 4, "diamante_unique": 5}
    X["tier_encoded"] = X["tier"].map(tier_map).fillna(1).astype(int)

    for col in FEATURE_COLUMNS:
        if col not in X.columns:
            X[col] = 0.0

    return X[FEATURE_COLUMNS].astype(float)


def train_clv_models(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    seed: int | None = None,
) -> dict[str, Any]:
    """Executa o pipeline completo de treinamento e avaliação de CLV."""
    if seed is None:
        base_s = settings().get("seed", 42)
        seed = child_seed(base_s, "clv_model")

    log.info("Iniciando treino de CLV com validação temporal (seed=%d)...", seed)

    y_train = train_df["target_clv_12m"].values.astype(float)
    y_test = test_df["target_clv_12m"].values.astype(float)

    X_train = prepare_features(train_df)
    X_test = prepare_features(test_df)

    # ---------------------------------------------------------
    # 1. Baseline: BG/NBD + Gamma-Gamma
    # ---------------------------------------------------------
    log.info("Ajustando baseline estatístico BG/NBD + Gamma-Gamma...")
    train_freq = train_df["frequency_12m"].values.astype(float)
    train_rec = np.maximum(0.0, 365.0 - train_df["recency_days"].values.astype(float))
    train_tenure = np.full_like(train_freq, 365.0)
    train_mon = train_df["ticket_medio_12m"].values.astype(float)

    bgnbd_pipeline = BGNBDGammaGammaPipeline(penalizer_coef=0.01)
    bgnbd_pipeline.fit(train_freq, train_rec, train_tenure, train_mon)

    test_freq = test_df["frequency_12m"].values.astype(float)
    test_rec = np.maximum(0.0, 365.0 - test_df["recency_days"].values.astype(float))
    test_tenure = np.full_like(test_freq, 365.0)
    test_mon = test_df["ticket_medio_12m"].values.astype(float)

    preds_base = bgnbd_pipeline.predict_clv_12m(
        test_freq, test_rec, test_tenure, test_mon, horizon_days=365.0
    )
    preds_base = np.maximum(0.0, np.nan_to_num(preds_base, nan=0.0))

    # ---------------------------------------------------------
    # 2. Modelo Final: LightGBM Regressor
    # ---------------------------------------------------------
    log.info("Ajustando modelo final LightGBM Regressor...")
    model_lgb = lgb.LGBMRegressor(
        objective="regression",
        n_estimators=180,
        learning_rate=0.04,
        num_leaves=31,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=seed,
        n_jobs=-1,
        importance_type="gain",
        verbosity=-1,
        deterministic=True,
        force_col_wise=True,
    )
    model_lgb.fit(X_train, y_train)

    preds_model = model_lgb.predict(X_test)
    preds_model = np.maximum(0.0, np.nan_to_num(preds_model, nan=0.0))

    # ---------------------------------------------------------
    # 3. Métricas de Avaliação e Bootstrap IC95
    # ---------------------------------------------------------
    log.info("Calculando métricas analíticas e bootstrap...")
    wape_b = wape(y_test, preds_base)
    wape_m = wape(y_test, preds_model)
    mae_b = mae(y_test, preds_base)
    mae_m = mae(y_test, preds_model)
    spear_b = spearman_rank_corr(y_test, preds_base)
    spear_m = spearman_rank_corr(y_test, preds_model)

    gini_b, lorenz_b = gini_revenue_capture(y_test, preds_base)
    gini_m, lorenz_m = gini_revenue_capture(y_test, preds_model)

    lift_df = lift_by_decile(y_test, preds_model, n_deciles=10)
    lift_decil_1_m = float(lift_df.loc[0, "lift"])

    lift_base_df = lift_by_decile(y_test, preds_base, n_deciles=10)
    lift_decil_1_b = float(lift_base_df.loc[0, "lift"])

    # Testes bootstrap de diferença (Modelo - Baseline)
    boot_wape = bootstrap_metric_difference(
        wape, y_test, preds_model, preds_base, n_bootstraps=500, seed=seed, higher_is_better=False
    )
    boot_mae = bootstrap_metric_difference(
        mae, y_test, preds_model, preds_base, n_bootstraps=500, seed=seed, higher_is_better=False
    )
    boot_spear = bootstrap_metric_difference(
        spearman_rank_corr,
        y_test,
        preds_model,
        preds_base,
        n_bootstraps=500,
        seed=seed,
        higher_is_better=True,
    )

    metrics = {
        "baseline": {
            "model_type": "BG/NBD + Gamma-Gamma",
            "wape": float(round(wape_b, 4)),
            "mae": float(round(mae_b, 2)),
            "spearman": float(round(spear_b, 4)),
            "gini_capture": float(round(gini_b, 4)),
            "lift_decil_1": float(round(lift_decil_1_b, 2)),
        },
        "lightgbm": {
            "model_type": "LightGBM Regressor",
            "wape": float(round(wape_m, 4)),
            "mae": float(round(mae_m, 2)),
            "spearman": float(round(spear_m, 4)),
            "gini_capture": float(round(gini_m, 4)),
            "lift_decil_1": float(round(lift_decil_1_m, 2)),
        },
        "bootstrap_comparison": {
            "wape_diff": boot_wape,
            "mae_diff": boot_mae,
            "spearman_diff": boot_spear,
        },
    }

    # ---------------------------------------------------------
    # 4. TreeSHAP (Nativo) e Explicabilidade
    # ---------------------------------------------------------
    log.info("Calculando TreeSHAP nativo...")
    contrib_df, base_val = compute_shap_contributions(model_lgb, X_test, FEATURE_COLUMNS)
    global_imp = global_feature_importance(contrib_df)
    local_top3 = local_top_k(test_df["customer_id"].values, contrib_df, X_test, k=3)

    # ---------------------------------------------------------
    # 5. Visualizações em docs/model_cards/figuras/
    # ---------------------------------------------------------
    fig_dir = ensure_dir("docs/model_cards/figuras")
    plot_global_summary(
        global_imp,
        "Importância Global de Atributos — CLV 12m (TreeSHAP)",
        fig_dir / "clv_shap_global.png",
    )

    # Waterfall para o primeiro cliente
    c0_id = str(test_df["customer_id"].iloc[0])
    c0_shap = contrib_df.iloc[0].values
    plot_waterfall(
        FEATURE_COLUMNS,
        c0_shap,
        base_val,
        float(preds_model[0]),
        f"Explicabilidade Local SHAP — CLV Cliente {c0_id}",
        fig_dir / "clv_waterfall_example.png",
    )

    # Gráfico da curva de Lorenz de captura
    fig_lorenz, ax_lorenz = plt.subplots(figsize=(7, 6))
    ax_lorenz.plot(
        lorenz_m["population_fraction"],
        lorenz_m["revenue_capture_fraction"],
        label=f"LightGBM (Gini={gini_m:.3f})",
        color="#00529B",
        lw=2,
    )
    ax_lorenz.plot(
        lorenz_b["population_fraction"],
        lorenz_b["revenue_capture_fraction"],
        label=f"Baseline BG/NBD (Gini={gini_b:.3f})",
        color="#E65100",
        linestyle="--",
        lw=1.5,
    )
    ax_lorenz.plot([0, 1], [0, 1], label="Aleatório (Gini=0.00)", color="gray", linestyle=":", lw=1)
    ax_lorenz.set_title("Curva de Lorenz de Captura de Receita — CLV 12m", fontweight="bold")
    ax_lorenz.set_xlabel("Fração Acumulada da População (ordenada por predição)")
    ax_lorenz.set_ylabel("Fração Acumulada de Receita Real Capturada")
    ax_lorenz.legend(loc="lower right")
    ax_lorenz.grid(True, linestyle=":", alpha=0.6)
    fig_lorenz.tight_layout()
    fig_lorenz.savefig(fig_dir / "clv_lorenz_curve.png", dpi=150)
    plt.close(fig_lorenz)

    # ---------------------------------------------------------
    # 6. Salvar predições, SHAP e modelos
    # ---------------------------------------------------------
    n_samples = len(test_df)
    order = np.argsort(-preds_model, kind="stable")
    ranks = np.empty_like(order)
    ranks[order] = np.arange(n_samples)
    decile_ranks = np.minimum((ranks * 10) // n_samples + 1, 10)

    df_preds = pd.DataFrame(
        {
            "customer_id": test_df["customer_id"].astype(str),
            "clv_baseline_12m": np.round(preds_base, 2),
            "clv_predicted_12m": np.round(preds_model, 2),
            "target_clv_12m": np.round(y_test, 2),
            "error_baseline": np.round(np.abs(y_test - preds_base), 2),
            "error_model": np.round(np.abs(y_test - preds_model), 2),
            "decile_model": decile_ranks.astype(int),
        }
    )

    analytics_dir = ensure_dir("data/analytics")
    preds_path = analytics_dir / "clv_predictions.parquet"
    df_preds.to_parquet(preds_path, index=False)
    log.info("Predições salvas em %s (%d clientes)", preds_path, len(df_preds))

    # Validação rigorosa do contrato
    validate_or_raise(load_contract("clv_predictions"), preds_path)

    shap_path = analytics_dir / "clv_shap.parquet"
    local_top3.to_parquet(shap_path, index=False)
    log.info("SHAP local salvo em %s", shap_path)

    metrics_dir = ensure_dir("data/analytics/metrics")
    with open(metrics_dir / "clv_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    save_model_bundle(
        "clv_lightgbm",
        model_lgb,
        FEATURE_COLUMNS,
        metrics["lightgbm"],
        cutoff="2025-08-31",
        seed=seed,
    )

    # Gerar Model Card atualizado
    _write_clv_model_card(metrics, global_imp)

    return {
        "metrics": metrics,
        "predictions_path": str(preds_path),
        "shap_path": str(shap_path),
        "global_importance": global_imp,
    }


def _write_clv_model_card(metrics: dict[str, Any], importance_df: pd.DataFrame) -> None:
    """Gera o model card auditável em docs/model_cards/clv.md."""
    m_base = metrics["baseline"]
    m_lgb = metrics["lightgbm"]
    b_comp = metrics.get("bootstrap_comparison", {})

    top_feats = "\n".join(
        f"| {row['importance_rank']} | `{row['feature']}` | {row['mean_abs_shap']:.4f} |"
        for _, row in importance_df.head(8).iterrows()
    )

    card_content = f"""# Model Card — Customer Lifetime Value (CLV 12m)

## 1. Visão Geral e Uso Pretendido
- **Finalidade:** Previsão da receita total (BRL) que cada membro do Azul Fidelidade gerará nos próximos 12 meses.
- **Horizonte de Avaliação:** 12 meses futuros (`2025-09-01` a `2026-08-31`).
- **Validação Temporal:** Origem móvel estrita (treino com corte em `2025-02-28`, teste com corte em `2025-08-31`). Zero particionamento aleatório.
- **Uso no Sistema:** Componente de 60% do Score de Alto Valor (`ScoreAV`), cálculo do Valor em Risco (`CLV × P(churn)`) e priorização de ações do Agente.

## 2. Comparativo de Desempenho (Baseline vs Modelo Final)
A avaliação compara o modelo probabilístico não-contratual clássico (**BG/NBD + Gamma-Gamma**) contra o modelo de Gradient Boosting (**LightGBM**).

| Métrica | Baseline (BG/NBD + GG) | Modelo Final (LightGBM) | Ganho / Diferença | IC 95% Bootstrap | Significativo? |
|---|---|---|---|---|---|
| **WAPE** | {m_base["wape"]:.4f} | {m_lgb["wape"]:.4f} | {m_lgb["wape"] - m_base["wape"]:+.4f} | [{b_comp.get("wape_diff", {}).get("ci_lower", 0.0):.4f}, {b_comp.get("wape_diff", {}).get("ci_upper", 0.0):.4f}] | {"Sim" if b_comp.get("wape_diff", {}).get("significant") else "Não"} |
| **MAE (BRL)** | R$ {m_base["mae"]:.2f} | R$ {m_lgb["mae"]:.2f} | R$ {m_lgb["mae"] - m_base["mae"]:+.2f} | [{b_comp.get("mae_diff", {}).get("ci_lower", 0.0):.2f}, {b_comp.get("mae_diff", {}).get("ci_upper", 0.0):.2f}] | {"Sim" if b_comp.get("mae_diff", {}).get("significant") else "Não"} |
| **Spearman** | {m_base["spearman"]:.4f} | {m_lgb["spearman"]:.4f} | {m_lgb["spearman"] - m_base["spearman"]:+.4f} | [{b_comp.get("spearman_diff", {}).get("ci_lower", 0.0):.4f}, {b_comp.get("spearman_diff", {}).get("ci_upper", 0.0):.4f}] | {"Sim" if b_comp.get("spearman_diff", {}).get("significant") else "Não"} |
| **Gini de Captura** | {m_base["gini_capture"]:.4f} | {m_lgb["gini_capture"]:.4f} | {m_lgb["gini_capture"] - m_base["gini_capture"]:+.4f} | — | — |
| **Lift Decil 1** | {m_base["lift_decil_1"]:.2f}x | {m_lgb["lift_decil_1"]:.2f}x | {m_lgb["lift_decil_1"] - m_base["lift_decil_1"]:+.2f}x | — | — |

## 3. Explicabilidade (TreeSHAP)
Principais fatores que orientam a previsão de valor no LightGBM:

| Posto | Atributo | Média |SHAP| |
|---|---|---|
{top_feats}

### Figuras Auditáveis
- Importância Global: ![SHAP Global](figuras/clv_shap_global.png)
- Exemplo Local Waterfall: ![Waterfall Exemplo](figuras/clv_waterfall_example.png)
- Curva de Lorenz / Concentração: ![Curva Lorenz](figuras/clv_lorenz_curve.png)

## 4. Governança e LGPD
- **Atributos Sensíveis Proibidos:** Conforme a Política de IA Responsável do Projeto Aura 2.0 e a LGPD, variáveis como `faixa_etaria`, `genero` e `regiao` são **estritamente excluídas** de todas as etapas de treino e inferência.
- **Anti-Vazamento Temporal:** O pipeline aplica corte rígido (`<= 2025-08-31`). Nenhuma informação de voo ou gasto do período de avaliação entra no vetor de features.

## 5. Limitações Metodológicas
1. **Base Sintética Calibrada:** O modelo foi ajustado sobre base sintética calibrada em agregados ANAC e Azul RI. Os resultados comprovam a sanidade matemática e arquitetural do pipeline, mas não constituem comprovação empírica de acurácia no tráfego comercial real.
2. **Horizonte de 12 Meses:** O modelo é otimizado para o ciclo anual de fidelidade; previsões para horizontes plurianuais requerem recalibração com desconto de fluxo de caixa (DCF).
"""
    cards_dir = ensure_dir("docs/model_cards")
    with open(cards_dir / "clv.md", "w", encoding="utf-8") as f:
        f.write(card_content)
    log.info("Model Card de CLV gerado em %s", cards_dir / "clv.md")


def main() -> int:
    train_file = path("data/analytics/features_customer_val.parquet")
    test_file = path("data/analytics/features_customer.parquet")

    if not train_file.exists() or not test_file.exists():
        log.error(
            "Arquivos de entrada ausentes (%s e %s). Execute 'python tasks.py features' primeiro.",
            train_file,
            test_file,
        )
        return 1

    train_df = pd.read_parquet(train_file)
    test_df = pd.read_parquet(test_file)

    train_clv_models(train_df, test_df)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
