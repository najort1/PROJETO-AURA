"""Treinamento e avaliação de modelos de Churn / Risco de Evasão (WS4 - Projeto Aura 2.0).

Pipeline:
1. Validação temporal estrita: coorte de validação (2025-02-28) vs coorte principal (2025-08-31).
2. Definição operacional de evasão (settings.modeling): inatividade > 2x o intervalo individual, mínimo 180 dias.
3. Baseline: Regressão Logística com padronização de features.
4. Modelo final: LightGBM Classifier determinístico.
5. Métricas com Bootstrap IC95: ROC-AUC, PR-AUC, Brier score, Curva de Calibração, Lift@10%.
6. TreeSHAP nativo (global + local top-3 por cliente).
7. Persistência e validação contra contrato schemas/churn_predictions.yaml.
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
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from aura_core.config import child_seed, settings
from aura_core.log import get_logger
from aura_core.paths import ensure_dir, path
from ml.common.metrics import (
    bootstrap_metric_difference,
    brier_score,
    calibration_curve,
    lift_by_decile,
    pr_auc_score,
    roc_auc_score,
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

log = get_logger("ml.churn.train")

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


def train_churn_models(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    seed: int | None = None,
) -> dict[str, Any]:
    """Executa o pipeline completo de treinamento e avaliação de Churn."""
    if seed is None:
        base_s = settings().get("seed", 42)
        seed = child_seed(base_s, "churn_model")

    log.info("Iniciando treino de Churn com validação temporal (seed=%d)...", seed)

    y_train = train_df["target_churn_12m"].values.astype(int)
    y_test = test_df["target_churn_12m"].values.astype(int)

    X_train = prepare_features(train_df)
    X_test = prepare_features(test_df)

    # ---------------------------------------------------------
    # 1. Baseline: Regressão Logística
    # ---------------------------------------------------------
    log.info("Ajustando baseline de Regressão Logística...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    baseline_lr = LogisticRegression(
        max_iter=1000,
        random_state=seed,
        class_weight="balanced",
    )
    baseline_lr.fit(X_train_scaled, y_train)
    probs_base = baseline_lr.predict_proba(X_test_scaled)[:, 1]

    # ---------------------------------------------------------
    # 2. Modelo Final: LightGBM Classifier
    # ---------------------------------------------------------
    log.info("Ajustando modelo final LightGBM Classifier...")
    model_lgb = lgb.LGBMClassifier(
        objective="binary",
        n_estimators=180,
        learning_rate=0.035,
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
    probs_model = model_lgb.predict_proba(X_test)[:, 1]

    # ---------------------------------------------------------
    # 3. Métricas de Avaliação e Bootstrap IC95
    # ---------------------------------------------------------
    log.info("Calculando métricas analíticas e bootstrap...")
    auc_b = roc_auc_score(y_test, probs_base)
    auc_m = roc_auc_score(y_test, probs_model)

    pr_b = pr_auc_score(y_test, probs_base)
    pr_m = pr_auc_score(y_test, probs_model)

    brier_b = brier_score(y_test, probs_base)
    brier_m = brier_score(y_test, probs_model)

    lift_base_df = lift_by_decile(y_test, probs_base, n_deciles=10)
    lift_10_b = float(lift_base_df.loc[0, "lift"])

    lift_model_df = lift_by_decile(y_test, probs_model, n_deciles=10)
    lift_10_m = float(lift_model_df.loc[0, "lift"])

    cal_base = calibration_curve(y_test, probs_base, n_bins=10, strategy="uniform")
    cal_model = calibration_curve(y_test, probs_model, n_bins=10, strategy="uniform")

    # Bootstrap de diferença (Modelo - Baseline)
    boot_auc = bootstrap_metric_difference(
        roc_auc_score,
        y_test,
        probs_model,
        probs_base,
        n_bootstraps=500,
        seed=seed,
        higher_is_better=True,
    )
    boot_pr = bootstrap_metric_difference(
        pr_auc_score,
        y_test,
        probs_model,
        probs_base,
        n_bootstraps=500,
        seed=seed,
        higher_is_better=True,
    )
    boot_brier = bootstrap_metric_difference(
        brier_score,
        y_test,
        probs_model,
        probs_base,
        n_bootstraps=500,
        seed=seed,
        higher_is_better=False,
    )

    metrics = {
        "baseline": {
            "model_type": "Regressão Logística",
            "roc_auc": float(round(auc_b, 4)),
            "pr_auc": float(round(pr_b, 4)),
            "brier": float(round(brier_b, 4)),
            "lift_top10": float(round(lift_10_b, 2)),
        },
        "lightgbm": {
            "model_type": "LightGBM Classifier",
            "roc_auc": float(round(auc_m, 4)),
            "pr_auc": float(round(pr_m, 4)),
            "brier": float(round(brier_m, 4)),
            "lift_top10": float(round(lift_10_m, 2)),
        },
        "bootstrap_comparison": {
            "roc_auc_diff": boot_auc,
            "pr_auc_diff": boot_pr,
            "brier_diff": boot_brier,
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
        "Importância Global de Atributos — Risco de Evasão (TreeSHAP)",
        fig_dir / "churn_shap_global.png",
    )

    c0_id = str(test_df["customer_id"].iloc[0])
    c0_shap = contrib_df.iloc[0].values
    plot_waterfall(
        FEATURE_COLUMNS,
        c0_shap,
        base_val,
        float(probs_model[0]),
        f"Explicabilidade Local SHAP — Churn Cliente {c0_id}",
        fig_dir / "churn_waterfall_example.png",
    )

    # Curva de Calibração
    fig_cal, ax_cal = plt.subplots(figsize=(7, 6))
    ax_cal.plot(
        cal_model["pred_mean"],
        cal_model["true_mean"],
        "s-",
        color="#00529B",
        label=f"LightGBM (Brier={brier_m:.3f})",
    )
    ax_cal.plot(
        cal_base["pred_mean"],
        cal_base["true_mean"],
        "o--",
        color="#E65100",
        label=f"Baseline Logística (Brier={brier_b:.3f})",
    )
    ax_cal.plot([0, 1], [0, 1], ":", color="gray", label="Perfeitamente Calibrado")
    ax_cal.set_xlabel("Probabilidade Prevista Média")
    ax_cal.set_ylabel("Fração Real Observada de Evasão")
    ax_cal.set_title("Curva de Calibração — Churn 12m", fontweight="bold")
    ax_cal.legend(loc="upper left")
    ax_cal.grid(True, linestyle=":", alpha=0.6)
    fig_cal.tight_layout()
    fig_cal.savefig(fig_dir / "churn_calibration_curve.png", dpi=150)
    plt.close(fig_cal)

    # ---------------------------------------------------------
    # 6. Salvar predições, SHAP e modelos
    # ---------------------------------------------------------
    n_samples = len(test_df)
    order = np.argsort(-probs_model, kind="stable")
    ranks = np.empty_like(order)
    ranks[order] = np.arange(n_samples)
    decile_ranks = np.minimum((ranks * 10) // n_samples + 1, 10)

    df_preds = pd.DataFrame(
        {
            "customer_id": test_df["customer_id"].astype(str),
            "churn_prob_baseline": np.round(probs_base, 4),
            "churn_prob_model": np.round(probs_model, 4),
            "target_churn_12m": y_test.astype(int),
            "decile_model": decile_ranks.astype(int),
        }
    )

    analytics_dir = ensure_dir("data/analytics")
    preds_path = analytics_dir / "churn_predictions.parquet"
    df_preds.to_parquet(preds_path, index=False)
    log.info("Predições salvas em %s (%d clientes)", preds_path, len(df_preds))

    # Validação do contrato
    validate_or_raise(load_contract("churn_predictions"), preds_path)

    shap_path = analytics_dir / "churn_shap.parquet"
    local_top3.to_parquet(shap_path, index=False)
    log.info("SHAP local salvo em %s", shap_path)

    metrics_dir = ensure_dir("data/analytics/metrics")
    with open(metrics_dir / "churn_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    save_model_bundle(
        "churn_lightgbm",
        model_lgb,
        FEATURE_COLUMNS,
        metrics["lightgbm"],
        cutoff="2025-08-31",
        seed=seed,
    )

    _write_churn_model_card(metrics, global_imp, cal_model)

    return {
        "metrics": metrics,
        "predictions_path": str(preds_path),
        "shap_path": str(shap_path),
        "global_importance": global_imp,
    }


def _write_churn_model_card(
    metrics: dict[str, Any],
    importance_df: pd.DataFrame,
    calibration_df: pd.DataFrame | None = None,
) -> None:
    """Gera o model card auditável em docs/model_cards/churn.md."""
    m_base = metrics["baseline"]
    m_lgb = metrics["lightgbm"]
    b_comp = metrics.get("bootstrap_comparison", {})

    top_feats = "\n".join(
        f"| {row['importance_rank']} | `{row['feature']}` | {row['mean_abs_shap']:.4f} |"
        for _, row in importance_df.head(8).iterrows()
    )

    cal_table_md = ""
    if calibration_df is not None and not calibration_df.empty:
        cal_rows = "\n".join(
            f"| {int(r['bin'])} | {int(r['count'])} | {r['pred_mean']:.4f} | {r['true_mean']:.4f} |"
            for _, r in calibration_df.iterrows()
        )
        cal_table_md = f"""
### Tabela de Calibração por Faixas (LightGBM)
| Bin | Clientes | Probabilidade Média Prevista | Fração Real de Evasão |
|---|---|---|---|
{cal_rows}
"""

    card_content = f"""# Model Card — Risco de Evasão (Churn 12m)

## 1. Visão Geral e Uso Pretendido
- **Finalidade:** Estimação da probabilidade individual de evasão (churn) no horizonte de 12 meses.
- **Definição Operacional de Evasão:** Inatividade superior a **2× o intervalo típico entre voos do cliente**, com **mínimo absoluto de 180 dias sem compras** (configuração formal em `config/settings.yaml: modeling`).
- **Validação Temporal:** Origem móvel estrita (treino com corte em `2025-02-28`, teste com corte em `2025-08-31`). Zero vazamento temporal e zero split aleatório.
- **Uso no Sistema:** Cálculo do Valor em Risco (`CLV_12m × P(churn)`), classificação de estado de risco e disparo de intervenções preventivas do Agente.

## 2. Comparativo de Desempenho (Baseline vs Modelo Final)
Comparação entre o modelo linear baseline (**Regressão Logística**) e o estimador não-linear (**LightGBM Classifier**).

| Métrica | Baseline (Regressão Logística) | Modelo Final (LightGBM) | Ganho / Diferença | IC 95% Bootstrap | Significativo? |
|---|---|---|---|---|---|
| **ROC-AUC** | {m_base["roc_auc"]:.4f} | {m_lgb["roc_auc"]:.4f} | {m_lgb["roc_auc"] - m_base["roc_auc"]:+.4f} | [{b_comp.get("roc_auc_diff", {}).get("ci_lower", 0.0):.4f}, {b_comp.get("roc_auc_diff", {}).get("ci_upper", 0.0):.4f}] | {"Sim" if b_comp.get("roc_auc_diff", {}).get("significant") else "Não"} |
| **PR-AUC** | {m_base["pr_auc"]:.4f} | {m_lgb["pr_auc"]:.4f} | {m_lgb["pr_auc"] - m_base["pr_auc"]:+.4f} | [{b_comp.get("pr_auc_diff", {}).get("ci_lower", 0.0):.4f}, {b_comp.get("pr_auc_diff", {}).get("ci_upper", 0.0):.4f}] | {"Sim" if b_comp.get("pr_auc_diff", {}).get("significant") else "Não"} |
| **Brier Score** | {m_base["brier"]:.4f} | {m_lgb["brier"]:.4f} | {m_lgb["brier"] - m_base["brier"]:+.4f} | [{b_comp.get("brier_diff", {}).get("ci_lower", 0.0):.4f}, {b_comp.get("brier_diff", {}).get("ci_upper", 0.0):.4f}] | {"Sim" if b_comp.get("brier_diff", {}).get("significant") else "Não"} |
| **Lift Top 10%** | {m_base["lift_top10"]:.2f}x | {m_lgb["lift_top10"]:.2f}x | {m_lgb["lift_top10"] - m_base["lift_top10"]:+.2f}x | — | — |
{cal_table_md}
## 3. Explicabilidade (TreeSHAP)
Atributos de maior impacto sobre a probabilidade de evasão:

| Posto | Atributo | Média |SHAP| |
|---|---|---|
{top_feats}

### Figuras Auditáveis
- Importância Global: ![SHAP Global](figuras/churn_shap_global.png)
- Exemplo Local Waterfall: ![Waterfall Exemplo](figuras/churn_waterfall_example.png)
- Curva de Calibração: ![Calibração](figuras/churn_calibration_curve.png)

## 4. Governança e LGPD
- **Atributos Sensíveis Proibidos:** Variáveis demográficas (`faixa_etaria`, `genero`, `regiao`) são rigorosamente **bloqueadas** na matriz de treinamento. Testes automatizados de regressão garantem que qualquer vazamento quebre a execução (fail loud).
- **Corte Temporal:** Features calculadas exclusivamente com histórico anterior ao cutoff (`2025-08-31`).

## 5. Limitações Metodológicas
1. **Ambiente Sintético:** Modelo treinado e validado sobre a base sintética calibrada do projeto. As métricas atestam a integridade e calibração do pipeline analítico, não a taxa de retenção empírica na operação comercial.
2. **Definição de Churn:** A evasão em programas de fidelidade é não-contratual; clientes podem permanecer longos períodos sem voar antes de retornar sem que haja encerramento formal da conta.
"""
    cards_dir = ensure_dir("docs/model_cards")
    with open(cards_dir / "churn.md", "w", encoding="utf-8") as f:
        f.write(card_content)
    log.info("Model Card de Churn gerado em %s", cards_dir / "churn.md")


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

    train_churn_models(train_df, test_df)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
