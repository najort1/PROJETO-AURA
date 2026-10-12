"""Testes analíticos rigorosos para métricas de avaliação (ml/common/metrics.py).

Testa cada métrica contra valores teóricos conhecidos e equivalência scikit-learn.
"""

import numpy as np
import pytest
from sklearn import metrics as sk_metrics

from ml.common.metrics import (
    bootstrap_ci,
    bootstrap_metric_difference,
    brier_score,
    calibration_curve,
    gini_revenue_capture,
    lift_by_decile,
    mae,
    pr_auc_score,
    roc_auc_score,
    spearman_rank_corr,
    wape,
)


def test_wape_analytical():
    # Caso analítico conhecido: sum(|y - y_hat|) / sum(y)
    # y = [10, 20], y_pred = [12, 18] -> erros [2, 2] -> soma 4; soma y = 30 -> 4/30 = 2/15
    y_true = np.array([10.0, 20.0])
    y_pred = np.array([12.0, 18.0])
    assert pytest.approx(wape(y_true, y_pred), rel=1e-6) == 4.0 / 30.0

    # Predição perfeita -> WAPE = 0.0
    assert wape(np.array([100.0, 50.0]), np.array([100.0, 50.0])) == 0.0

    # Falha se dimensões forem diferentes
    with pytest.raises(ValueError):
        wape(np.array([1.0, 2.0]), np.array([1.0]))

    # Falha se soma de y_true for zero
    with pytest.raises(ValueError):
        wape(np.array([0.0, 0.0]), np.array([1.0, 2.0]))


def test_mae_analytical():
    y_true = np.array([10.0, 20.0, 30.0])
    y_pred = np.array([15.0, 15.0, 35.0])
    # erros absolutos: 5, 5, 5 -> MAE = 5.0
    assert pytest.approx(mae(y_true, y_pred)) == 5.0
    assert pytest.approx(mae(y_true, y_pred)) == sk_metrics.mean_absolute_error(y_true, y_pred)


def test_spearman_monotonic():
    # Perfeitamente monotônico crescente
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
    assert pytest.approx(spearman_rank_corr(x, y)) == 1.0

    # Perfeitamente decrescente
    assert pytest.approx(spearman_rank_corr(x, -y)) == -1.0


def test_lift_by_decile_constructed():
    # Construir 100 amostras: 10 decis com 10 elementos cada
    # O decil 1 (top 10 predito) tem valor real médio 20.0
    # Os outros 9 decis têm valor real médio 10.0
    # Média global = (10*20 + 90*10)/100 = (200 + 900)/100 = 11.0
    # Lift esperado do decil 1 = 20.0 / 11.0 = 1.818181...
    n = 100
    y_pred = np.linspace(100, 1, n)  # ordenado decrescente

    y_true = np.ones(n) * 10.0
    y_true[:10] = 20.0  # os primeiros 10 (decil 1) têm 20.0

    df_lift = lift_by_decile(y_true, y_pred, n_deciles=10)

    assert len(df_lift) == 10
    assert df_lift.loc[0, "decile"] == 1
    assert df_lift.loc[0, "count"] == 10
    assert pytest.approx(df_lift.loc[0, "true_mean"]) == 20.0
    assert pytest.approx(df_lift.loc[0, "lift"], rel=1e-4) == 20.0 / 11.0
    # A taxa acumulada de captura no decil 10 deve ser 1.0 (100%)
    assert pytest.approx(df_lift.loc[9, "capture_rate"]) == 1.0


def test_gini_revenue_capture_uniform_and_concentrated():
    # 1) Caso uniforme: todas as receitas são idênticas (ex: 100 clientes com receita R$ 10)
    # A curva de Lorenz de captura é a reta identidade L(p) = p.
    # Área sob a reta de (0,0) a (1,1) é 0.5.
    # Gini = 2 * 0.5 - 1 = 0.0.
    n = 1000
    y_true_unif = np.ones(n) * 50.0
    y_pred_unif = np.linspace(100, 1, n)

    gini_unif, df_lorenz = gini_revenue_capture(y_true_unif, y_pred_unif)
    assert pytest.approx(gini_unif, abs=1e-3) == 0.0
    assert df_lorenz["population_fraction"].iloc[0] == 0.0
    assert df_lorenz["revenue_capture_fraction"].iloc[-1] == 1.0

    # 2) Caso hiper-concentrado: 1 cliente possui 100% da receita e o modelo coloca-o em 1º lugar
    y_true_conc = np.zeros(n)
    y_true_conc[0] = 10000.0  # todo o valor está no primeiro
    y_pred_conc = np.linspace(100, 1, n)

    gini_conc, _ = gini_revenue_capture(y_true_conc, y_pred_conc)
    # Área é praticamente 1.0 -> Gini ~ 1.0 (para n grande, > 0.99)
    assert gini_conc > 0.99


def test_roc_auc_vs_scikit():
    rng = np.random.default_rng(123)
    y_true = rng.integers(0, 2, size=200)
    y_pred = rng.uniform(0.0, 1.0, size=200)

    my_auc = roc_auc_score(y_true, y_pred)
    sk_auc = sk_metrics.roc_auc_score(y_true, y_pred)
    assert pytest.approx(my_auc, rel=1e-5) == sk_auc

    # Caso extremo perfeito
    y_perf = np.array([1, 1, 0, 0])
    p_perf = np.array([0.9, 0.8, 0.2, 0.1])
    assert roc_auc_score(y_perf, p_perf) == 1.0

    # Caso invertido
    assert roc_auc_score(y_perf, 1.0 - p_perf) == 0.0


def test_pr_auc_vs_scikit():
    rng = np.random.default_rng(456)
    y_true = rng.integers(0, 2, size=300)
    y_pred = rng.uniform(0.0, 1.0, size=300)

    my_pr = pr_auc_score(y_true, y_pred)
    sk_pr = sk_metrics.average_precision_score(y_true, y_pred)
    assert pytest.approx(my_pr, rel=1e-4) == sk_pr


def test_brier_score_vs_scikit():
    y_true = np.array([1, 0, 1, 1, 0])
    y_pred = np.array([0.9, 0.1, 0.8, 0.7, 0.2])

    my_brier = brier_score(y_true, y_pred)
    sk_brier = sk_metrics.brier_score_loss(y_true, y_pred)
    assert pytest.approx(my_brier) == sk_brier


def test_calibration_curve():
    y_true = np.array([0, 0, 0, 1, 1, 1, 1, 1])
    y_pred = np.array([0.1, 0.15, 0.2, 0.7, 0.8, 0.85, 0.9, 0.95])
    cal_df = calibration_curve(y_true, y_pred, n_bins=5, strategy="uniform")
    assert not cal_df.empty
    assert "pred_mean" in cal_df.columns
    assert "true_mean" in cal_df.columns
    # Bin baixo tem true_mean 0.0, bin alto tem true_mean 1.0
    assert cal_df.iloc[0]["true_mean"] < cal_df.iloc[-1]["true_mean"]


def test_bootstrap_ci_and_difference():
    rng = np.random.default_rng(789)
    y_true = rng.normal(100, 15, size=150)
    # Modelo 1 é muito bom (ruído pequeno)
    y_pred_m1 = y_true + rng.normal(0, 2, size=150)
    # Baseline é fraco (ruído grande)
    y_pred_base = y_true + rng.normal(0, 15, size=150)

    pt, low, high = bootstrap_ci(mae, y_true, y_pred_m1, n_bootstraps=300, ci=0.95, seed=42)
    assert low <= pt <= high

    # Teste de diferença Modelo - Baseline em MAE (menor é melhor)
    res = bootstrap_metric_difference(
        mae,
        y_true,
        y_pred_m1,
        y_pred_base,
        n_bootstraps=300,
        ci=0.95,
        seed=42,
        higher_is_better=False,
    )
    # Modelo 1 tem MAE menor que o Baseline, então point_diff < 0
    assert res["point_diff"] < 0
    assert res["ci_upper"] < 0  # IC estritamente negativo => diferença significativa
    assert res["significant"] is True
