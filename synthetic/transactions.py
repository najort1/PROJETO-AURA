"""Geração de transações monetárias e de fidelidade (WS2).

Gera compras aéreas, serviços ancillaries, acúmulos por parceiros/cartão/clube
e resgates de passagens em pontos conforme as regras do Azul Fidelidade.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

import numpy as np


def calculate_flight_fare(
    distance_km: float,
    advance_days: float,
    month: int,
    spend_effect: float,
    generator_config: dict[str, Any],
    rng: np.random.Generator,
) -> float:
    """Calcula tarifa dinâmica da passagem aérea baseada em distância, antecedência e sazonalidade."""
    pricing_cfg = generator_config.get("pricing", {})
    base_per_km = float(pricing_cfg.get("base_fare_per_km_brl", 0.48))
    min_fare = float(pricing_cfg.get("min_fare_brl", 180.0))
    cv = float(pricing_cfg.get("fare_dispersion_cv", 0.35))

    # Curva de antecedência (yield management): compra em cima da hora é mais cara
    advance_multiplier = 1.0 + 0.55 * np.exp(-max(advance_days, 0.0) / 10.0)

    # Sazonalidade mensal exógena
    season_map = (
        generator_config.get("latent", {})
        .get("exogenous_events", {})
        .get("monthly_seasonality", {})
    )
    month_multiplier = float(season_map.get(month, 1.0))

    # Efeito aleatório de gasto do cliente
    customer_spend_factor = max(0.6, 1.0 + 0.22 * spend_effect)

    # Ruído estocástico log-normal
    noise = np.exp(rng.normal(0, cv * 0.5))

    fare = (
        distance_km
        * base_per_km
        * advance_multiplier
        * month_multiplier
        * customer_spend_factor
        * noise
    )
    return float(round(max(min_fare, fare), 2))


def create_transaction_record(
    tx_idx: int,
    customer_id: str,
    tx_date: dt.datetime,
    tx_type: str,
    amount_brl: float,
    pontos_azul: int,
    pontos_qp: int,
    pontos_resgatados: int,
    ancillary_type: str | None = None,
    flight_id: str | None = None,
) -> dict[str, Any]:
    """Cria um registro compatível com schemas/synthetic_transactions.yaml."""
    return {
        "transaction_id": f"TX{tx_idx:07d}",
        "customer_id": customer_id,
        "transaction_date": tx_date,
        "transaction_type": tx_type,
        "amount_brl": float(round(amount_brl, 2)),
        "ancillary_type": ancillary_type if ancillary_type is not None else "nenhum",
        "pontos_azul_acumulados": int(pontos_azul),
        "pontos_qualificaveis_acumulados": int(pontos_qp),
        "pontos_azul_resgatados": int(pontos_resgatados),
        "flight_id": flight_id,
    }
