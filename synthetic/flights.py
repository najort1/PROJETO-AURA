"""Geração de malha de voos domésticos calibrada com inventário e taxas da ANAC (WS2)."""

from __future__ import annotations

import datetime as dt
from typing import Any

import numpy as np

# Inventário padrão de rotas de referência da malha Azul (distâncias reais em km)
DEFAULT_ROUTES: list[dict[str, Any]] = [
    {
        "orig": "VCP",
        "dest": "SDU",
        "dist_km": 410.0,
        "weight": 1.00,
        "delay_rate": 0.14,
        "cancel_rate": 0.018,
    },
    {
        "orig": "SDU",
        "dest": "VCP",
        "dist_km": 410.0,
        "weight": 1.00,
        "delay_rate": 0.15,
        "cancel_rate": 0.019,
    },
    {
        "orig": "VCP",
        "dest": "CNF",
        "dist_km": 460.0,
        "weight": 0.95,
        "delay_rate": 0.13,
        "cancel_rate": 0.015,
    },
    {
        "orig": "CNF",
        "dest": "VCP",
        "dist_km": 460.0,
        "weight": 0.95,
        "delay_rate": 0.13,
        "cancel_rate": 0.015,
    },
    {
        "orig": "VCP",
        "dest": "BSB",
        "dist_km": 820.0,
        "weight": 0.85,
        "delay_rate": 0.15,
        "cancel_rate": 0.016,
    },
    {
        "orig": "BSB",
        "dest": "VCP",
        "dist_km": 820.0,
        "weight": 0.85,
        "delay_rate": 0.16,
        "cancel_rate": 0.017,
    },
    {
        "orig": "VCP",
        "dest": "CWB",
        "dist_km": 360.0,
        "weight": 0.80,
        "delay_rate": 0.18,
        "cancel_rate": 0.022,
    },
    {
        "orig": "CWB",
        "dest": "VCP",
        "dist_km": 360.0,
        "weight": 0.80,
        "delay_rate": 0.19,
        "cancel_rate": 0.024,
    },
    {
        "orig": "VCP",
        "dest": "POA",
        "dist_km": 880.0,
        "weight": 0.75,
        "delay_rate": 0.20,
        "cancel_rate": 0.026,
    },
    {
        "orig": "POA",
        "dest": "VCP",
        "dist_km": 880.0,
        "weight": 0.75,
        "delay_rate": 0.21,
        "cancel_rate": 0.027,
    },
    {
        "orig": "VCP",
        "dest": "REC",
        "dist_km": 2120.0,
        "weight": 0.70,
        "delay_rate": 0.17,
        "cancel_rate": 0.014,
    },
    {
        "orig": "REC",
        "dest": "VCP",
        "dist_km": 2120.0,
        "weight": 0.70,
        "delay_rate": 0.16,
        "cancel_rate": 0.013,
    },
    {
        "orig": "VCP",
        "dest": "SSA",
        "dist_km": 1450.0,
        "weight": 0.65,
        "delay_rate": 0.16,
        "cancel_rate": 0.015,
    },
    {
        "orig": "SSA",
        "dest": "VCP",
        "dist_km": 1450.0,
        "weight": 0.65,
        "delay_rate": 0.15,
        "cancel_rate": 0.015,
    },
    {
        "orig": "VCP",
        "dest": "CGB",
        "dist_km": 1280.0,
        "weight": 0.60,
        "delay_rate": 0.17,
        "cancel_rate": 0.016,
    },
    {
        "orig": "CGB",
        "dest": "VCP",
        "dist_km": 1280.0,
        "weight": 0.60,
        "delay_rate": 0.18,
        "cancel_rate": 0.017,
    },
    {
        "orig": "VCP",
        "dest": "BEL",
        "dist_km": 2350.0,
        "weight": 0.50,
        "delay_rate": 0.18,
        "cancel_rate": 0.018,
    },
    {
        "orig": "BEL",
        "dest": "VCP",
        "dist_km": 2350.0,
        "weight": 0.50,
        "delay_rate": 0.17,
        "cancel_rate": 0.017,
    },
    {
        "orig": "VCP",
        "dest": "MAO",
        "dist_km": 2680.0,
        "weight": 0.45,
        "delay_rate": 0.19,
        "cancel_rate": 0.019,
    },
    {
        "orig": "MAO",
        "dest": "VCP",
        "dist_km": 2680.0,
        "weight": 0.45,
        "delay_rate": 0.18,
        "cancel_rate": 0.018,
    },
    {
        "orig": "CNF",
        "dest": "SDU",
        "dist_km": 360.0,
        "weight": 0.70,
        "delay_rate": 0.14,
        "cancel_rate": 0.015,
    },
    {
        "orig": "SDU",
        "dest": "CNF",
        "dist_km": 360.0,
        "weight": 0.70,
        "delay_rate": 0.15,
        "cancel_rate": 0.016,
    },
    {
        "orig": "CNF",
        "dest": "BSB",
        "dist_km": 620.0,
        "weight": 0.60,
        "delay_rate": 0.14,
        "cancel_rate": 0.014,
    },
    {
        "orig": "BSB",
        "dest": "CNF",
        "dist_km": 620.0,
        "weight": 0.60,
        "delay_rate": 0.14,
        "cancel_rate": 0.014,
    },
    {
        "orig": "CNF",
        "dest": "REC",
        "dist_km": 1680.0,
        "weight": 0.55,
        "delay_rate": 0.15,
        "cancel_rate": 0.014,
    },
    {
        "orig": "REC",
        "dest": "CNF",
        "dist_km": 1680.0,
        "weight": 0.55,
        "delay_rate": 0.15,
        "cancel_rate": 0.014,
    },
    {
        "orig": "REC",
        "dest": "FOR",
        "dist_km": 630.0,
        "weight": 0.60,
        "delay_rate": 0.13,
        "cancel_rate": 0.012,
    },
    {
        "orig": "FOR",
        "dest": "REC",
        "dist_km": 630.0,
        "weight": 0.60,
        "delay_rate": 0.13,
        "cancel_rate": 0.012,
    },
    {
        "orig": "REC",
        "dest": "SSA",
        "dist_km": 670.0,
        "weight": 0.55,
        "delay_rate": 0.14,
        "cancel_rate": 0.013,
    },
    {
        "orig": "SSA",
        "dest": "REC",
        "dist_km": 670.0,
        "weight": 0.55,
        "delay_rate": 0.14,
        "cancel_rate": 0.013,
    },
    {
        "orig": "VCP",
        "dest": "RAO",
        "dist_km": 230.0,
        "weight": 0.40,
        "delay_rate": 0.12,
        "cancel_rate": 0.015,
    },
    {
        "orig": "RAO",
        "dest": "VCP",
        "dist_km": 230.0,
        "weight": 0.40,
        "delay_rate": 0.12,
        "cancel_rate": 0.015,
    },
    {
        "orig": "VCP",
        "dest": "SJP",
        "dist_km": 370.0,
        "weight": 0.35,
        "delay_rate": 0.13,
        "cancel_rate": 0.016,
    },
    {
        "orig": "SJP",
        "dest": "VCP",
        "dist_km": 370.0,
        "weight": 0.35,
        "delay_rate": 0.13,
        "cancel_rate": 0.016,
    },
    {
        "orig": "CGB",
        "dest": "BSB",
        "dist_km": 870.0,
        "weight": 0.45,
        "delay_rate": 0.15,
        "cancel_rate": 0.016,
    },
    {
        "orig": "BSB",
        "dest": "CGB",
        "dist_km": 870.0,
        "weight": 0.45,
        "delay_rate": 0.16,
        "cancel_rate": 0.017,
    },
]


def get_route_catalog(calibration_values: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Recupera catálogo de rotas a partir dos valores calibrados ou catálogo de referência."""
    routes = [dict(r) for r in DEFAULT_ROUTES]
    if calibration_values and "market.delay_rate_by_route" in calibration_values:
        delay_info = calibration_values["market.delay_rate_by_route"]
        calib_mean_delay = float(delay_info.get("overall_mean", 0.1675))
        for r in routes:
            r["delay_rate"] = calib_mean_delay
    return routes


def sample_flight_delay_and_cancellation(
    route: dict[str, Any],
    rng: np.random.Generator,
    is_winter_fog_period: bool = False,
) -> tuple[int, int, int]:
    """Amostra cancelamento e minutos de atraso de acordo com a rota e período sazonal."""
    delay_rate = float(route.get("delay_rate", 0.16))
    cancel_rate = float(route.get("cancel_rate", 0.018))

    if is_winter_fog_period and route["orig"] in {"VCP", "CWB", "POA"}:
        delay_rate *= 1.18
        cancel_rate *= 1.15

    is_cancelled = 1 if rng.random() < cancel_rate else 0
    if is_cancelled:
        return 0, 0, 1

    is_delayed = rng.random() < delay_rate
    if is_delayed:
        # Atraso > 15 min: distribuição Gamma com média de ~38 min adicional
        delay_extra = int(rng.gamma(shape=2.5, scale=12.0))
        delay_minutes = 16 + min(delay_extra, 240)
        has_delay = 1
    else:
        delay_minutes = int(rng.integers(0, 12))
        has_delay = 0

    return delay_minutes, has_delay, 0


def generate_flight_record(
    flight_idx: int,
    route: dict[str, Any],
    departure_dt: dt.datetime,
    rng: np.random.Generator,
    is_winter_period: bool = False,
) -> dict[str, Any]:
    """Cria um registro estruturado de voo conforme o contrato schemas/synthetic_flights.yaml."""
    delay_min, has_delay, is_cancel = sample_flight_delay_and_cancellation(
        route, rng, is_winter_fog_period=is_winter_period
    )
    scheduled_dep = departure_dt
    actual_dep = scheduled_dep if is_cancel else scheduled_dep + dt.timedelta(minutes=delay_min)

    flight_num = 4000 + (flight_idx % 900)
    return {
        "flight_id": f"FL{flight_idx:07d}",
        "flight_number": f"AD{flight_num:04d}",
        "origin_airport": str(route["orig"]),
        "destination_airport": str(route["dest"]),
        "departure_date": scheduled_dep,
        "distance_km": float(route["dist_km"]),
        "scheduled_departure": scheduled_dep,
        "actual_departure": actual_dep,
        "delay_minutes": int(delay_min),
        "has_delay": int(has_delay),
        "is_cancelled": int(is_cancel),
    }
