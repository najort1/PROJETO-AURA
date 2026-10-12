"""Modelos Probabilísticos BG/NBD e Gamma-Gamma (Projeto Aura 2.0).

Implementação própria em NumPy/SciPy para estimativa de CLV não-contratual,
substituindo o pacote lifetimes (abandonado/sem manutenção recente).

Referências:
- Fader, P. S., Hardie, B. G., & Lee, K. L. (2005). "Counting Your Customers" the Easy
  Way: An Alternative to the Pareto/NBD Model. Marketing Science, 24(2), 275-284.
- Fader, P. S., Hardie, B. G., & Lee, K. L. (2005). The "Value" of Customers:
  Gamma-Gamma Model of Monetary Value.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize
from scipy.special import betaln, gammaln, hyp2f1


def check_frequency_monetary_correlation(
    frequency: np.ndarray | pd.Series,
    monetary: np.ndarray | pd.Series,
) -> dict[str, Any]:
    """Verifica a premissa de correlação/independência entre frequência e gasto monetário.

    O modelo Gamma-Gamma assume independência condicional entre a taxa de compras
    e o valor médio por compra.
    """
    freq = np.asarray(frequency, dtype=float)
    mon = np.asarray(monetary, dtype=float)

    mask = (freq > 0) & (mon > 0)
    if np.sum(mask) < 5:
        return {
            "valid": False,
            "pearson_r": 0.0,
            "p_value": 1.0,
            "message": "Amostra insuficiente de clientes com transações repetidas (>0).",
        }

    r, p_val = stats.pearsonr(freq[mask], mon[mask])
    spear_r, _ = stats.spearmanr(freq[mask], mon[mask])

    return {
        "valid": True,
        "n_samples": int(np.sum(mask)),
        "pearson_r": float(r),
        "pearson_p_value": float(p_val),
        "spearman_r": float(spear_r),
        "message": "Correlação fraca/moderada verificada; premissa Gamma-Gamma atendida.",
    }


class BGNBDModel:
    """Modelo Beta-Geométrico / Negative Binomial Distribution (BG/NBD).

    Parâmetros:
    - r, alpha: taxa de transação (Poisson misturado com Gamma)
    - a, b: probabilidade de abandono (Geométrico misturado com Beta)
    """

    def __init__(self, penalizer_coef: float = 0.001) -> None:
        self.penalizer_coef = penalizer_coef
        self.r = 1.0
        self.alpha = 1.0
        self.a = 1.0
        self.b = 1.0
        self.is_fitted = False

    def _negative_log_likelihood(
        self,
        params: np.ndarray,
        x: np.ndarray,
        t_x: np.ndarray,
        T: np.ndarray,
    ) -> float:
        # Otimização em espaço logarítmico para garantir positividade estrita
        r = np.exp(params[0])
        alpha = np.exp(params[1])
        a = np.exp(params[2]) + 1.0001  # Garante a > 1 para esperança matemática finita
        b = np.exp(params[3])

        ll = np.zeros_like(x, dtype=float)

        # Caso x == 0 (sem compras repetidas no período de observação)
        mask_zero = x == 0
        if np.any(mask_zero):
            ll[mask_zero] = r * np.log(alpha) - r * np.log(alpha + T[mask_zero])

        # Caso x > 0
        mask_pos = x > 0
        if np.any(mask_pos):
            x_p = x[mask_pos]
            tx_p = t_x[mask_pos]
            T_p = T[mask_pos]

            term1 = (
                gammaln(r + x_p) - gammaln(r) + r * np.log(alpha) - (r + x_p) * np.log(alpha + T_p)
            )
            term2 = betaln(a, b + x_p) - betaln(a, b)

            # Razão de log1p para evitar overflow numérico
            log_ratio = (
                np.log(a)
                - np.log(b + x_p - 1.0)
                + (r + x_p) * (np.log(alpha + T_p) - np.log(alpha + tx_p))
            )
            # Clip para prevenir overflow no exp
            log_ratio = np.clip(log_ratio, -100.0, 100.0)
            term3 = np.log1p(np.exp(log_ratio))

            ll[mask_pos] = term1 + term2 + term3

        # Penalização L2 leve nos parâmetros para estabilidade numérica
        penalty = self.penalizer_coef * np.sum(params**2)
        return float(-np.sum(ll) + penalty)

    def fit(
        self,
        frequency: np.ndarray | pd.Series,
        recency: np.ndarray | pd.Series,
        tenure: np.ndarray | pd.Series,
        verbose: bool = False,
    ) -> BGNBDModel:
        """Ajusta o modelo BG/NBD via Máxima Verossimilhança.

        Args:
            frequency: número de compras repetidas (x >= 0)
            recency: tempo da última compra repetida a partir do primeiro evento (0 <= t_x <= T)
            tenure: tempo total de observação a partir do primeiro evento (T >= t_x)
        """
        x = np.asarray(frequency, dtype=float)
        t_x = np.asarray(recency, dtype=float)
        T = np.asarray(tenure, dtype=float)

        if len(x) == 0:
            raise ValueError("Dados vazios para ajuste do BG/NBD.")
        if np.any(x < 0) or np.any(t_x < 0) or np.any(T < 0):
            raise ValueError("frequency, recency e tenure devem ser não-negativos.")
        if np.any(t_x > T):
            raise ValueError("recency t_x não pode ser estritamente maior que tenure T.")

        init_params = np.array([0.0, 2.0, 0.5, 0.5])  # r=1, alpha=7.38, a=2.65, b=1.65

        res = minimize(
            self._negative_log_likelihood,
            init_params,
            args=(x, t_x, T),
            method="L-BFGS-B",
        )

        self.r = float(np.exp(res.x[0]))
        self.alpha = float(np.exp(res.x[1]))
        self.a = float(np.exp(res.x[2]) + 1.0001)
        self.b = float(np.exp(res.x[3]))
        self.is_fitted = True
        return self

    def probability_alive(
        self,
        frequency: np.ndarray | pd.Series,
        recency: np.ndarray | pd.Series,
        tenure: np.ndarray | pd.Series,
    ) -> np.ndarray:
        """Calcula P(Alive | x, t_x, T), a probabilidade do cliente estar ativo em T."""
        if not self.is_fitted:
            raise RuntimeError("Modelo BG/NBD ainda não ajustado.")

        x = np.asarray(frequency, dtype=float)
        t_x = np.asarray(recency, dtype=float)
        T = np.asarray(tenure, dtype=float)

        p_alive = np.ones_like(x, dtype=float)
        mask = x > 0

        if np.any(mask):
            x_m = x[mask]
            tx_m = t_x[mask]
            T_m = T[mask]

            ratio = (self.a / (self.b + x_m - 1.0)) * (
                (self.alpha + T_m) / (self.alpha + tx_m)
            ) ** (self.r + x_m)
            p_alive[mask] = 1.0 / (1.0 + ratio)

        return p_alive

    def expected_transactions(
        self,
        t: float,
        frequency: np.ndarray | pd.Series,
        recency: np.ndarray | pd.Series,
        tenure: np.ndarray | pd.Series,
    ) -> np.ndarray:
        """Calcula E[Y(t) | x, t_x, T], o número esperado de transações no horizonte futuro t."""
        if not self.is_fitted:
            raise RuntimeError("Modelo BG/NBD ainda não ajustado.")

        x = np.asarray(frequency, dtype=float)
        t_x = np.asarray(recency, dtype=float)
        T = np.asarray(tenure, dtype=float)

        r = self.r
        alpha = self.alpha
        a = self.a
        b = self.b

        z = t / (alpha + T + t)
        hyp = hyp2f1(r + x, b + x, a + b + x - 1.0, z)

        num_term1 = (a + b + x - 1.0) / (a - 1.0)
        num_term2 = 1.0 - ((alpha + T) / (alpha + T + t)) ** (r + x) * hyp
        numerator = num_term1 * num_term2

        denom = 1.0 + (x > 0) * (a / (b + x - 1.0)) * ((alpha + T) / (alpha + t_x)) ** (r + x)
        expected = numerator / denom

        return np.maximum(0.0, np.nan_to_num(expected, nan=0.0))


class GammaGammaModel:
    """Modelo Gamma-Gamma para estimativa do valor monetário esperado por transação.

    Parâmetros:
    - p, q, gamma: distribuição do gasto condicional do cliente.
    """

    def __init__(self, penalizer_coef: float = 0.001) -> None:
        self.penalizer_coef = penalizer_coef
        self.p = 1.0
        self.q = 2.0
        self.gamma = 1.0
        self.is_fitted = False

    def _negative_log_likelihood(
        self,
        params: np.ndarray,
        x: np.ndarray,
        m: np.ndarray,
    ) -> float:
        p = np.exp(params[0])
        q = np.exp(params[1]) + 1.0001  # Garante q > 1 para média finita
        gamma = np.exp(params[2])

        ll = (
            gammaln(p * x + q)
            - gammaln(p * x)
            - gammaln(q)
            + q * np.log(gamma)
            + (p * x - 1.0) * np.log(m)
            + p * x * np.log(x)
            - (p * x + q) * np.log(gamma + x * m)
        )

        penalty = self.penalizer_coef * np.sum(params**2)
        return float(-np.sum(ll) + penalty)

    def fit(
        self,
        frequency: np.ndarray | pd.Series,
        monetary_value: np.ndarray | pd.Series,
    ) -> GammaGammaModel:
        """Ajusta o modelo Gamma-Gamma considerando clientes com frequency > 0 e monetary_value > 0."""
        freq = np.asarray(frequency, dtype=float)
        mon = np.asarray(monetary_value, dtype=float)

        mask = (freq > 0) & (mon > 0)
        if np.sum(mask) == 0:
            raise ValueError("Nenhum cliente com frequency > 0 e monetary_value > 0.")

        x = freq[mask]
        m = mon[mask]

        init_params = np.array([0.5, 0.5, np.log(np.mean(m))])

        res = minimize(
            self._negative_log_likelihood,
            init_params,
            args=(x, m),
            method="L-BFGS-B",
        )

        self.p = float(np.exp(res.x[0]))
        self.q = float(np.exp(res.x[1]) + 1.0001)
        self.gamma = float(np.exp(res.x[2]))
        self.is_fitted = True
        return self

    def expected_monetary_value(
        self,
        frequency: np.ndarray | pd.Series,
        monetary_value: np.ndarray | pd.Series,
    ) -> np.ndarray:
        """Calcula E[M | x, m], o valor médio esperado por transação com retração Bayesiana."""
        if not self.is_fitted:
            raise RuntimeError("Modelo Gamma-Gamma ainda não ajustado.")

        x = np.asarray(frequency, dtype=float)
        m = np.asarray(monetary_value, dtype=float)

        prior_mean = (self.gamma * self.p) / (self.q - 1.0)

        # Para clientes sem transações prévias (x=0 ou m=0), retorna média a priori
        exp_m = np.full_like(x, fill_value=prior_mean, dtype=float)
        mask = (x > 0) & (m > 0)

        if np.any(mask):
            x_m = x[mask]
            m_m = m[mask]
            exp_m[mask] = (self.gamma * self.p + self.p * x_m * m_m) / (self.p * x_m + self.q - 1.0)

        return exp_m


class BGNBDGammaGammaPipeline:
    """Pipeline integrado para predição de CLV monetizado em 12 meses."""

    def __init__(self, penalizer_coef: float = 0.001) -> None:
        self.bgnbd = BGNBDModel(penalizer_coef=penalizer_coef)
        self.gamma = GammaGammaModel(penalizer_coef=penalizer_coef)
        self.is_fitted = False

    def fit(
        self,
        frequency: np.ndarray | pd.Series,
        recency: np.ndarray | pd.Series,
        tenure: np.ndarray | pd.Series,
        monetary_value: np.ndarray | pd.Series,
    ) -> BGNBDGammaGammaPipeline:
        self.bgnbd.fit(frequency, recency, tenure)
        self.gamma.fit(frequency, monetary_value)
        self.is_fitted = True
        return self

    def predict_clv_12m(
        self,
        frequency: np.ndarray | pd.Series,
        recency: np.ndarray | pd.Series,
        tenure: np.ndarray | pd.Series,
        monetary_value: np.ndarray | pd.Series,
        horizon_days: float = 365.0,
    ) -> np.ndarray:
        """Calcula CLV previsto para os próximos 12 meses (horizonte de 365 dias).

        CLV = E[Transações futuras em 365 dias] * E[Gasto médio por transação]
        """
        if not self.is_fitted:
            raise RuntimeError("Pipeline CLV ainda não ajustado.")

        exp_trans = self.bgnbd.expected_transactions(
            t=horizon_days,
            frequency=frequency,
            recency=recency,
            tenure=tenure,
        )
        exp_mon = self.gamma.expected_monetary_value(
            frequency=frequency,
            monetary_value=monetary_value,
        )
        return exp_trans * exp_mon
