"""Testes estatísticos e de sanidade para os modelos BG/NBD e Gamma-Gamma (ml/clv/bgnbd_gamma.py)."""

import numpy as np
import pytest

from ml.clv.bgnbd_gamma import (
    BGNBDGammaGammaPipeline,
    BGNBDModel,
    GammaGammaModel,
    check_frequency_monetary_correlation,
)


@pytest.fixture
def synthetic_rfm():
    rng = np.random.default_rng(42)
    n = 200
    tenure = rng.uniform(60, 365, size=n)
    frequency = rng.poisson(3.0, size=n)
    recency = np.where(frequency > 0, tenure * rng.uniform(0.1, 0.95, size=n), 0.0)
    # Gasto médio por voo/transação em torno de R$ 400
    monetary = np.where(frequency > 0, rng.gamma(8.0, 50.0, size=n), 0.0)
    return frequency, recency, tenure, monetary


def test_bgnbd_fit_and_params(synthetic_rfm):
    freq, rec, ten, _ = synthetic_rfm
    model = BGNBDModel()
    model.fit(freq, rec, ten)

    assert model.is_fitted
    assert model.r > 0.0
    assert model.alpha > 0.0
    assert model.a > 1.0  # Garantido pela parametrização
    assert model.b > 0.0


def test_expected_transactions_monotonicity_recency():
    """Sanidade: Quanto maior o tempo de inatividade desde a última compra, menor a esperança de compras futuras."""
    model = BGNBDModel()
    model.r = 1.2
    model.alpha = 15.0
    model.a = 2.5
    model.b = 3.0
    model.is_fitted = True

    # Cliente A: última compra há 5 dias (t_x = 95, T = 100)
    # Cliente B: última compra há 80 dias (t_x = 20, T = 100)
    # Ambos com mesma frequência x = 3 e mesmo tenure T = 100
    exp_A = model.expected_transactions(t=30, frequency=3, recency=95, tenure=100)
    exp_B = model.expected_transactions(t=30, frequency=3, recency=20, tenure=100)

    assert float(exp_A) > float(exp_B), "Cliente com recência mais recente deve ter maior E[Y(t)]"

    # Probabilidade de estar vivo deve ser estritamente maior para A
    p_alive_A = model.probability_alive(frequency=3, recency=95, tenure=100)
    p_alive_B = model.probability_alive(frequency=3, recency=20, tenure=100)
    assert float(p_alive_A) > float(p_alive_B)


def test_expected_transactions_monotonicity_frequency():
    """Sanidade: Clientes com maior frequência histórica têm maior esperança de compras futuras."""
    model = BGNBDModel()
    model.r = 1.0
    model.alpha = 10.0
    model.a = 2.0
    model.b = 2.0
    model.is_fitted = True

    exp_low = model.expected_transactions(t=30, frequency=1, recency=80, tenure=100)
    exp_high = model.expected_transactions(t=30, frequency=6, recency=80, tenure=100)

    assert float(exp_high) > float(exp_low)


def test_gamma_gamma_monotonicity_and_shrinkage():
    """Sanidade: Gamma-Gamma deve preservar monotonicidade no gasto médio e efetuar retração bayesiana."""
    model = GammaGammaModel()
    # Ajuste manual para testar propriedades analíticas
    model.p = 5.0
    model.q = 3.0
    model.gamma = 100.0  # prior mean = (100 * 5) / (3 - 1) = 250.0
    model.is_fitted = True

    # Monotonicidade: gasto maior gera esperança maior
    exp_low_spend = model.expected_monetary_value(frequency=3, monetary_value=200.0)
    exp_high_spend = model.expected_monetary_value(frequency=3, monetary_value=600.0)
    assert float(exp_high_spend) > float(exp_low_spend)

    # Retração Bayesiana:
    # Cliente com poucas transações (x=1, m=600) se aproxima mais da média a priori (250)
    # do que cliente com muitas transações (x=20, m=600)
    exp_few = float(model.expected_monetary_value(frequency=1, monetary_value=600.0))
    exp_many = float(model.expected_monetary_value(frequency=20, monetary_value=600.0))

    assert exp_few < exp_many
    assert exp_few < 600.0  # retraído para baixo rumo aos 250


def test_frequency_monetary_correlation_check():
    freq = np.array([1, 2, 3, 4, 5, 6, 7])
    mon = np.array([300.0, 310.0, 290.0, 320.0, 305.0, 315.0, 300.0])

    res = check_frequency_monetary_correlation(freq, mon)
    assert res["valid"] is True
    assert "pearson_r" in res
    assert "spearman_r" in res


def test_full_clv_pipeline(synthetic_rfm):
    freq, rec, ten, mon = synthetic_rfm
    pipeline = BGNBDGammaGammaPipeline()
    pipeline.fit(freq, rec, ten, mon)

    assert pipeline.is_fitted
    preds_12m = pipeline.predict_clv_12m(freq, rec, ten, mon, horizon_days=365.0)

    assert len(preds_12m) == len(freq)
    assert np.all(preds_12m >= 0.0)
    assert np.all(np.isfinite(preds_12m))
