"""Motor de fidelidade e progressão de nível do Azul Fidelidade (WS2).

Implementa estritamente as regras de qualificação de config/program_rules.yaml:
- Azul: nível inicial (ordem 1)
- Topázio: 6.000 qp OU 6 trechos
- Safira: 10.000 qp OU 10 trechos
- Diamante: (12.000 qp E 12 trechos) OU R$ 25.000 gastos aéreos
- Diamante Unique: (26.000 qp E 26 trechos) OU R$ 50.000 gastos aéreos
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from aura_core.config import program_rules
from aura_core.log import get_logger

log = get_logger("synthetic.loyalty")

TIER_ORDER: dict[str, int] = {
    "azul": 1,
    "topazio": 2,
    "safira": 3,
    "diamante": 4,
    "diamante_unique": 5,
}

EARN_MULTIPLIERS: dict[str, int] = {
    "azul": 1,
    "topazio": 2,
    "safira": 3,
    "diamante": 4,
    "diamante_unique": 4,  # fail-safe para null no config
}

POINTS_VALIDITY_YEARS: dict[str, int] = {
    "azul": 2,
    "topazio": 3,
    "safira": 4,
    "diamante": 5,
    "diamante_unique": 5,  # fail-safe para null no config
}

REDEMPTION_CEILINGS: dict[str, int] = {
    "azul": 130000,
    "topazio": 120000,
    "safira": 110000,
    "diamante": 90000,
    "diamante_unique": 90000,  # fail-safe para null no config
}

# Triggers de upgrade por tier (usados para determinar trigger_reason correto)
UPGRADE_TRIGGERS: dict[str, dict[str, str]] = {
    "topazio": {
        "qualifying_points": "qualifying_points_reached",
        "segments": "segments_reached",
    },
    "safira": {
        "qualifying_points": "qualifying_points_reached",
        "segments": "segments_reached",
    },
    "diamante": {
        "qualifying_points": "qualifying_points_reached",
        "segments": "segments_reached",
        "alternative_spend": "alternative_spend_reached",
    },
    "diamante_unique": {
        "qualifying_points": "qualifying_points_reached",
        "segments": "segments_reached",
        "alternative_spend": "alternative_spend_reached",
    },
}

DOWNGRADE_TRIGGER = "qualification_cycle_expired"


def _extract_threshold(tier_cfg: dict[str, Any], field: str, default: int | None) -> int | None:
    """Extrai um threshold do YAML aplicando a política null_semantics (fail-safe).

    Valor null no YAML = regra NÃO confirmada = inelegível (None).
    Valor ausente = usa default codificado.
    """
    qual = tier_cfg.get("qualification", {})
    val = qual.get(field, default)
    if val is None:
        log.debug(
            "Threshold '%s' é null no YAML para tier '%s' → inelegível (fail-safe)",
            field,
            tier_cfg.get("key", "?"),
        )
        return None
    return int(val)


def _load_rules() -> dict[str, Any]:
    """Carrega regras do programa com fail-loud: falha propaga exceção com log."""
    try:
        return program_rules()
    except Exception as e:
        log.error("Falha ao carregar program_rules.yaml: %s", e)
        raise


def evaluate_tier(
    qualifying_points: int,
    segments: int,
    spend_brl: float,
    rules: dict[str, Any] | None = None,
) -> str:
    """Avalia o nível alcançado com base nas regras oficiais vigentes em program_rules.yaml.

    Verifica do nível mais alto para o nível base.
    Guards explícitos contra None: threshold None = inelegível.
    """
    if rules is None:
        rules = _load_rules()

    tiers_cfg = {t["key"]: t for t in rules.get("tiers", [])} if "tiers" in rules else {}

    # 1. Diamante Unique (ordem 5)
    du_cfg = tiers_cfg.get("diamante_unique", {})
    du_qp = _extract_threshold(du_cfg, "qualifying_points", 26000)
    du_seg = _extract_threshold(du_cfg, "segments", 26)
    du_alt = _extract_threshold(du_cfg, "alternative_spend_brl", 50000)
    if (
        du_qp is not None
        and qualifying_points >= du_qp
        and du_seg is not None
        and segments >= du_seg
    ) or (du_alt is not None and spend_brl >= du_alt):
        return "diamante_unique"

    # 2. Diamante (ordem 4)
    dia_cfg = tiers_cfg.get("diamante", {})
    dia_qp = _extract_threshold(dia_cfg, "qualifying_points", 12000)
    dia_seg = _extract_threshold(dia_cfg, "segments", 12)
    dia_alt = _extract_threshold(dia_cfg, "alternative_spend_brl", 25000)
    if (
        dia_qp is not None
        and qualifying_points >= dia_qp
        and dia_seg is not None
        and segments >= dia_seg
    ) or (dia_alt is not None and spend_brl >= dia_alt):
        return "diamante"

    # 3. Safira (ordem 3)
    saf_cfg = tiers_cfg.get("safira", {})
    saf_qp = _extract_threshold(saf_cfg, "qualifying_points", 10000)
    saf_seg = _extract_threshold(saf_cfg, "segments", 10)
    if (saf_qp is not None and qualifying_points >= saf_qp) or (
        saf_seg is not None and segments >= saf_seg
    ):
        return "safira"

    # 4. Topázio (ordem 2)
    top_cfg = tiers_cfg.get("topazio", {})
    top_qp = _extract_threshold(top_cfg, "qualifying_points", 6000)
    top_seg = _extract_threshold(top_cfg, "segments", 6)
    if (top_qp is not None and qualifying_points >= top_qp) or (
        top_seg is not None and segments >= top_seg
    ):
        return "topazio"

    return "azul"


def get_earn_multiplier(tier: str) -> int:
    """Retorna multiplicador de Pontos Azul por R$ gasto em passagem (1, 2, 3 ou 4)."""
    return EARN_MULTIPLIERS.get(tier, 1)


def get_points_validity_years(tier: str) -> int:
    """Retorna validade em anos do lote acumulado conforme o nível (2, 3, 4 ou 5)."""
    return POINTS_VALIDITY_YEARS.get(tier, 2)


def get_redemption_ceiling(tier: str) -> int:
    """Retorna teto de pontos por trecho nacional conforme o nível."""
    return REDEMPTION_CEILINGS.get(tier, 130000)


def determine_tier_change_event(
    previous_tier: str,
    new_tier: str,
    qualifying_points: int,
    segments: int,
    spend_brl: float,
) -> tuple[str, str]:
    """Determina o tipo de evento e o gatilho baseado na transição de tier.

    Returns:
        (event_type, trigger_reason) onde event_type ∈ {"tier_upgrade", "tier_downgrade"}.
    """
    prev_order = TIER_ORDER.get(previous_tier, 1)
    new_order = TIER_ORDER.get(new_tier, 1)

    if new_order > prev_order:
        # UPGRADE: determinar trigger baseado no novo tier e métricas
        triggers = UPGRADE_TRIGGERS.get(new_tier, {})
        # Prioridade: alternative_spend > qualifying_points > segments
        if "alternative_spend" in triggers and spend_brl >= 25000:
            return "tier_upgrade", "alternative_spend_reached"
        if "qualifying_points" in triggers and qualifying_points >= 6000:
            return "tier_upgrade", "qualifying_points_reached"
        if "segments" in triggers and segments >= 6:
            return "tier_upgrade", "segments_reached"
        # Fallback (não deveria ocorrer se evaluate_tier estiver correto)
        return "tier_upgrade", "qualifying_points_reached"

    elif new_order < prev_order:
        # DOWNGRADE: expiração do ciclo de qualificação
        return "tier_downgrade", DOWNGRADE_TRIGGER

    else:
        # Mesmo tier (retention) - não gera evento no loop atual
        return "tier_retention", ""


def create_loyalty_event(
    event_idx: int,
    customer_id: str,
    event_date: dt.datetime,
    event_type: str,
    previous_tier: str,
    new_tier: str,
    trigger_reason: str,
    qualifying_points: int,
    segments: int,
    spend_brl: float,
) -> dict[str, Any]:
    """Gera registro compatível com schemas/synthetic_loyalty_events.yaml."""
    return {
        "event_id": f"EV{event_idx:07d}",
        "customer_id": customer_id,
        "event_date": event_date,
        "event_type": event_type,
        "previous_tier": previous_tier,
        "new_tier": new_tier,
        "trigger_reason": trigger_reason,
        "qualifying_points_at_event": int(qualifying_points),
        "segments_at_event": int(segments),
        "spend_brl_at_event": float(round(spend_brl, 2)),
    }
