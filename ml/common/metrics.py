"""Métricas de avaliação para modelos de CLV e Churn (Projeto Aura 2.0).

Implementações auditáveis em numpy/scipy com testes contra valores analíticos:
- WAPE (Weighted Absolute Percentage Error)
- MAE (Mean Absolute Error)
- Spearman rank correlation
- Lift por decil (1 a 10)
- Curva de Lorenz e Coeficiente de Gini de captura de receita
- ROC-AUC (via Mann-Whitney / concordância com desempate)
- PR-AUC (Average Precision / trapézio de precisão-revocação)
- Brier score
- Curva de calibração (por bins uniformes ou quantis)
- Intervalo de confiança e teste de diferença por bootstrap (IC95)
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd
from scipy import stats


def wape(y_true: np.ndarray | pd.Series, y_pred: np.ndarray | pd.Series) -> float:
    """Calcula o WAPE (Weighted Absolute Percentage Error).

    WAPE = sum(|y_true - y_pred|) / sum(y_true)

    Exemplo:
        >>> wape(np.array([10.0, 20.0]), np.array([12.0, 18.0]))
        0.13333333333333333
    """
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)
    if yt.shape != yp.shape:
        raise ValueError(f"Dimensões incompatíveis: y_true {yt.shape} vs y_pred {yp.shape}")
    denom = np.sum(yt)
    if denom == 0.0:
        raise ValueError("Soma de y_true é zero; WAPE indefinido.")
    return float(np.sum(np.abs(yt - yp)) / denom)


def mae(y_true: np.ndarray | pd.Series, y_pred: np.ndarray | pd.Series) -> float:
    """Calcula o MAE (Mean Absolute Error).

    MAE = mean(|y_true - y_pred|)
    """
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)
    if yt.shape != yp.shape:
        raise ValueError(f"Dimensões incompatíveis: y_true {yt.shape} vs y_pred {yp.shape}")
    if len(yt) == 0:
        raise ValueError("Vetores vazios para cálculo de MAE.")
    return float(np.mean(np.abs(yt - yp)))


def spearman_rank_corr(y_true: np.ndarray | pd.Series, y_pred: np.ndarray | pd.Series) -> float:
    """Calcula a correlação de postos de Spearman entre valores reais e previstos."""
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)
    if len(yt) < 2:
        raise ValueError("Pelo menos 2 elementos são necessários para correlação.")
    res = stats.spearmanr(yt, yp)
    statistic = res.statistic if hasattr(res, "statistic") else res[0]
    return float(statistic)


def lift_by_decile(
    y_true: np.ndarray | pd.Series,
    y_pred: np.ndarray | pd.Series,
    n_deciles: int = 10,
) -> pd.DataFrame:
    """Calcula o lift acumulado e por decil ordenando os indivíduos por predição decrescente.

    Decil 1 = 10% de maiores predições.
    Lift = (média observada no decil) / (média global observada).
    """
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)
    n = len(yt)
    if n < n_deciles:
        raise ValueError(f"Tamanho da amostra ({n}) menor que n_deciles ({n_deciles}).")

    global_mean = float(np.mean(yt))
    total_val = float(np.sum(yt))

    # Ordenar decrescente pela predição
    order = np.argsort(-yp, kind="stable")
    yt_sorted = yt[order]
    yp_sorted = yp[order]

    # Atribuir decis com base na posição
    # 0 até n/10 -> decil 1, etc.
    decile_indices = np.minimum((np.arange(n) * n_deciles) // n + 1, n_deciles)

    records = []
    cum_true_sum = 0.0
    cum_count = 0

    for d in range(1, n_deciles + 1):
        mask = decile_indices == d
        count = int(np.sum(mask))
        d_true_sum = float(np.sum(yt_sorted[mask]))
        d_true_mean = d_true_sum / count if count > 0 else 0.0
        d_pred_mean = float(np.mean(yp_sorted[mask])) if count > 0 else 0.0

        cum_true_sum += d_true_sum
        cum_count += count
        cum_mean = cum_true_sum / cum_count if cum_count > 0 else 0.0

        lift = (d_true_mean / global_mean) if global_mean > 0 else 1.0
        cumulative_lift = (cum_mean / global_mean) if global_mean > 0 else 1.0
        capture_rate = (cum_true_sum / total_val) if total_val > 0 else 0.0

        records.append(
            {
                "decile": d,
                "count": count,
                "pred_mean": d_pred_mean,
                "true_mean": d_true_mean,
                "lift": lift,
                "cumulative_lift": cumulative_lift,
                "capture_rate": capture_rate,
            }
        )

    return pd.DataFrame(records)


def gini_revenue_capture(
    y_true: np.ndarray | pd.Series,
    y_pred: np.ndarray | pd.Series,
) -> tuple[float, pd.DataFrame]:
    """Calcula a curva de Lorenz e o Coeficiente de Gini de captura de receita.

    Ordena clientes por score/receita prevista decrescente.
    População acumulada p_i = i/n.
    Receita real acumulada L_i = sum(y_1..i) / sum(y_all).
    Área sob a curva de Lorenz (AUC) calculada por regra dos trapézios.
    Gini de captura = 2 * AUC - 1.

    Para distribuição uniforme ou ranking aleatório, AUC ~ 0.5 e Gini ~ 0.0.
    Para concentração perfeita (top 1 captura tudo), AUC -> 1.0 e Gini -> 1.0.
    """
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)
    n = len(yt)
    if n == 0:
        raise ValueError("Vetor vazio para curva de Lorenz.")

    total_rev = float(np.sum(yt))
    if total_rev <= 0:
        raise ValueError("Receita total deve ser positiva para cálculo do Gini de captura.")

    order = np.argsort(-yp, kind="stable")
    yt_sorted = yt[order]

    cum_rev = np.cumsum(yt_sorted) / total_rev
    p_pop = np.arange(1, n + 1) / n

    p_curve = np.concatenate(([0.0], p_pop))
    l_curve = np.concatenate(([0.0], cum_rev))

    # Área sob a curva de Lorenz via regra trapezoidal
    auc_lorenz = float(np.sum(0.5 * (l_curve[:-1] + l_curve[1:]) * (p_curve[1:] - p_curve[:-1])))
    gini_capture = float(2.0 * auc_lorenz - 1.0)

    lorenz_df = pd.DataFrame(
        {
            "population_fraction": p_curve,
            "revenue_capture_fraction": l_curve,
        }
    )

    return gini_capture, lorenz_df


def roc_auc_score(y_true: np.ndarray | pd.Series, y_pred: np.ndarray | pd.Series) -> float:
    """Calcula a ROC-AUC (Área sob a curva ROC) via estatística de Wilcoxon/Mann-Whitney.

    Lida exatamente com empates (concordância probabilística).
    """
    yt = np.asarray(y_true, dtype=int)
    yp = np.asarray(y_pred, dtype=float)
    positives = yt == 1
    negatives = yt == 0

    n1 = int(np.sum(positives))
    n0 = int(np.sum(negatives))
    if n1 == 0 or n0 == 0:
        raise ValueError("y_true deve conter pelo menos uma classe positiva e uma negativa.")

    # Ranks dos valores de probabilidade (1 a n, empates recebem rank médio)
    ranks = stats.rankdata(yp)
    r1 = np.sum(ranks[positives])
    u1 = r1 - (n1 * (n1 + 1)) / 2.0
    auc = u1 / (n1 * n0)
    return float(auc)


def pr_auc_score(y_true: np.ndarray | pd.Series, y_pred: np.ndarray | pd.Series) -> float:
    """Calcula a PR-AUC (Average Precision) ordenando por predição decrescente."""
    yt = np.asarray(y_true, dtype=int)
    yp = np.asarray(y_pred, dtype=float)
    n_pos = int(np.sum(yt == 1))
    if n_pos == 0:
        raise ValueError("y_true deve conter pelo menos um caso positivo para PR-AUC.")

    # Ordenar decrescente pelo score predito
    order = np.argsort(-yp, kind="stable")
    yt_sorted = yt[order]

    tp_cum = np.cumsum(yt_sorted == 1)
    fp_cum = np.cumsum(yt_sorted == 0)

    precision = tp_cum / (tp_cum + fp_cum)
    recall = tp_cum / n_pos

    # Average Precision: soma das precisões nos pontos onde o recall aumenta
    recall_diff = np.diff(np.concatenate(([0.0], recall)))
    ap = np.sum(precision * recall_diff)
    return float(ap)


def brier_score(y_true: np.ndarray | pd.Series, y_pred: np.ndarray | pd.Series) -> float:
    """Calcula o Brier Score (erro quadrático médio das probabilidades preditas)."""
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)
    if len(yt) == 0:
        raise ValueError("Vetores vazios para cálculo de Brier Score.")
    return float(np.mean((yp - yt) ** 2))


def calibration_curve(
    y_true: np.ndarray | pd.Series,
    y_pred: np.ndarray | pd.Series,
    n_bins: int = 10,
    strategy: str = "uniform",
) -> pd.DataFrame:
    """Calcula a curva de calibração agrupando predições em faixas de probabilidade."""
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)

    if strategy == "uniform":
        bins = np.linspace(0.0, 1.0, n_bins + 1)
        bin_ids = np.digitize(yp, bins) - 1
        bin_ids = np.clip(bin_ids, 0, n_bins - 1)
    elif strategy == "quantile":
        quantiles = np.linspace(0.0, 1.0, n_bins + 1)
        bins = np.quantile(yp, quantiles)
        bins = np.unique(bins)
        if len(bins) < 2:
            bins = np.array([0.0, 1.0])
        bin_ids = np.digitize(yp, bins) - 1
        bin_ids = np.clip(bin_ids, 0, len(bins) - 2)
    else:
        raise ValueError(f"Estratégia inválida: {strategy}")

    records = []
    unique_bins = np.unique(bin_ids)
    for b in sorted(unique_bins):
        mask = bin_ids == b
        count = int(np.sum(mask))
        if count == 0:
            continue
        pred_mean = float(np.mean(yp[mask]))
        true_mean = float(np.mean(yt[mask]))
        records.append(
            {
                "bin": int(b),
                "count": count,
                "pred_mean": pred_mean,
                "true_mean": true_mean,
            }
        )
    return pd.DataFrame(records)


def bootstrap_ci(
    metric_fn: Callable[[np.ndarray, np.ndarray], float],
    y_true: np.ndarray | pd.Series,
    y_pred: np.ndarray | pd.Series,
    n_bootstraps: int = 1000,
    ci: float = 0.95,
    seed: int = 42,
) -> tuple[float, float, float]:
    """Estima intervalo de confiança bootstrap (percentil) para uma dada métrica."""
    yt = np.asarray(y_true)
    yp = np.asarray(y_pred)
    n = len(yt)
    point_est = float(metric_fn(yt, yp))

    rng = np.random.default_rng(seed)
    boot_vals = np.empty(n_bootstraps, dtype=float)

    for i in range(n_bootstraps):
        idx = rng.integers(0, n, size=n)
        try:
            boot_vals[i] = metric_fn(yt[idx], yp[idx])
        except (ValueError, ZeroDivisionError):
            boot_vals[i] = point_est

    alpha = 1.0 - ci
    lower = float(np.percentile(boot_vals, 100.0 * (alpha / 2.0)))
    upper = float(np.percentile(boot_vals, 100.0 * (1.0 - alpha / 2.0)))
    return point_est, lower, upper


def bootstrap_metric_difference(
    metric_fn: Callable[[np.ndarray, np.ndarray], float],
    y_true: np.ndarray | pd.Series,
    y_pred_model: np.ndarray | pd.Series,
    y_pred_baseline: np.ndarray | pd.Series,
    n_bootstraps: int = 1000,
    ci: float = 0.95,
    seed: int = 42,
    higher_is_better: bool = True,
) -> dict:
    """Calcula a diferença estatística (Modelo - Baseline) com IC95 e p-valor bootstrap.

    Retorna:
        dict com:
          - point_diff: diferença no conjunto completo
          - ci_lower: limite inferior do IC
          - ci_upper: limite superior do IC
          - significant: se zero está fora do IC
          - p_value: proporção de amostras bootstrap onde o modelo não supera o baseline
    """
    yt = np.asarray(y_true)
    yp_m = np.asarray(y_pred_model)
    yp_b = np.asarray(y_pred_baseline)
    n = len(yt)

    m_pt = float(metric_fn(yt, yp_m))
    b_pt = float(metric_fn(yt, yp_b))
    diff_pt = m_pt - b_pt

    rng = np.random.default_rng(seed)
    diffs = np.empty(n_bootstraps, dtype=float)

    for i in range(n_bootstraps):
        idx = rng.integers(0, n, size=n)
        try:
            m_val = metric_fn(yt[idx], yp_m[idx])
            b_val = metric_fn(yt[idx], yp_b[idx])
            diffs[i] = m_val - b_val
        except (ValueError, ZeroDivisionError):
            diffs[i] = diff_pt

    alpha = 1.0 - ci
    lower = float(np.percentile(diffs, 100.0 * (alpha / 2.0)))
    upper = float(np.percentile(diffs, 100.0 * (1.0 - alpha / 2.0)))

    if higher_is_better:
        significant = lower > 0.0
        p_val = float(np.mean(diffs <= 0.0))
    else:
        # Quando menor é melhor (ex: WAPE, MAE, Brier): diferença m_val - b_val deve ser < 0
        significant = upper < 0.0
        p_val = float(np.mean(diffs >= 0.0))

    return {
        "model_point": m_pt,
        "baseline_point": b_pt,
        "point_diff": diff_pt,
        "ci_lower": lower,
        "ci_upper": upper,
        "significant": significant,
        "p_value": p_val,
    }
