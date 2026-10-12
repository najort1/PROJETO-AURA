"""Geração de interações de atendimento e eventos de atrito com dados faltantes MAR (WS2)."""

from __future__ import annotations

import datetime as dt
from typing import Any

import numpy as np


def sample_nps_rating(
    has_friction: int,
    friction_intensity: float,
    is_high_tier: bool,
    rng: np.random.Generator,
    mar_config: dict[str, Any],
) -> float | None:
    """Amostra nota NPS com mecanismo formal MAR (Missing at Random).

    Clientes com forte atrito ou clientes de alto escalão respondem mais,
    enquanto a grande maioria indiferente não preenche pesquisa (missing ~58%).
    """
    base_prob = float(mar_config.get("base_response_prob", 0.30))
    friction_boost = float(mar_config.get("friction_response_boost", 0.45))
    tier_boost = float(mar_config.get("high_tier_response_boost", 0.15))

    p_response = base_prob
    if has_friction:
        p_response += friction_boost * min(1.0, friction_intensity + 0.2)
    if is_high_tier:
        p_response += tier_boost

    p_response = min(0.90, max(0.10, p_response))

    if rng.random() > p_response:
        return None  # Missing MAR

    if has_friction:
        # Atrito gera notas baixas (detratores 0-6)
        if friction_intensity > 0.6:
            score = rng.choice([0, 1, 2, 3, 4], p=[0.25, 0.30, 0.25, 0.15, 0.05])
        else:
            score = rng.choice([3, 4, 5, 6], p=[0.20, 0.35, 0.30, 0.15])
    else:
        # Sem atrito: promotores ou neutros (7-10)
        score = rng.choice([7, 8, 9, 10], p=[0.10, 0.25, 0.35, 0.30])

    return float(score)


def create_interaction_record(
    interaction_idx: int,
    customer_id: str,
    interaction_dt: dt.datetime,
    channel: str,
    aspect: str,
    has_friction: int,
    friction_intensity: float,
    nps_rating: float | None,
    resolution_status: str,
) -> dict[str, Any]:
    """Cria um registro compatível com schemas/synthetic_interactions.yaml."""
    return {
        "interaction_id": f"INT{interaction_idx:07d}",
        "customer_id": customer_id,
        "interaction_date": interaction_dt,
        "channel": channel,
        "aspect": aspect,
        "has_friction": int(has_friction),
        "friction_intensity": float(round(friction_intensity, 2)),
        "nps_rating": nps_rating,
        "resolution_status": resolution_status,
    }
