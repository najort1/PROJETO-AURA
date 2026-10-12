"""Processo estocástico latente de churn e consolidação do Ground Truth (WS2).

Calcula o hazard individual multifatorial, simula eventos de desistência,
determina evasão observada (inatividade) e compila data/curated/ground_truth.parquet.
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from aura_core.log import get_logger
from aura_core.paths import path

log = get_logger("synthetic.churn")


def load_friction_weights(generator_config: dict[str, Any]) -> tuple[dict[str, float], str]:
    """Carrega pesos dos atritos de friction_weights.json se existir; senão usa premissa parametrizada."""
    fpath = path("data/curated/friction_weights.json")
    if fpath.exists():
        try:
            with open(fpath, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "weights" in data:
                log.info("Pesos de atrito carregados de data/curated/friction_weights.json")
                return {
                    k: float(v) for k, v in data["weights"].items()
                }, "data/curated/friction_weights.json"
        except Exception as e:
            log.warning("Falha ao ler friction_weights.json (%s); recorrendo à premissa", e)

    default_weights = (
        generator_config.get("behavior", {})
        .get("friction_response", {})
        .get(
            "weights",
            {
                "atraso": 0.32,
                "bagagem": 0.28,
                "app_checkin": 0.18,
                "resgate_milhas": 0.35,
                "atendimento": 0.25,
                "preco": 0.22,
            },
        )
    )
    log.info(
        "Utilizando pesos de atrito da premissa de config/generator.yaml (substituição pendente de WS6)"
    )
    return {k: float(v) for k, v in default_weights.items()}, "config/generator.yaml (premise)"


def compute_ground_truth(
    customers_df: pd.DataFrame,
    transactions_df: pd.DataFrame,
    interactions_df: pd.DataFrame,
    generator_config: dict[str, Any],
    target_start: pd.Timestamp,
    target_end: pd.Timestamp,
    rng: np.random.Generator,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Computa métricas reais do período alvo (CLV 12m, hazard latente e evasão observada).

    Retorna:
        - ground_truth_df: tabela segregada (consumers: [evaluation_only])
        - updated_customers_df: customers com current_tier e status atualizados.
    """
    weights, _ = load_friction_weights(generator_config)
    archetypes_cfg = generator_config.get("archetypes", {})
    tier_reduction_map = (
        generator_config.get("behavior", {})
        .get("churn_hazard", {})
        .get(
            "tier_hazard_reduction",
            {
                "azul": 0.0,
                "topazio": 0.20,
                "safira": 0.38,
                "diamante": 0.60,
                "diamante_unique": 0.85,
            },
        )
    )

    # 1. CLV real no período alvo (2025-09-01 a 2026-08-31)
    target_txs = transactions_df[
        (transactions_df["transaction_date"] >= target_start)
        & (transactions_df["transaction_date"] <= target_end)
    ]
    clv_by_cust = target_txs.groupby("customer_id")["amount_brl"].sum().to_dict()

    # 2. Contagem e intensidade de atritos por cliente
    frictions = interactions_df[interactions_df["has_friction"] == 1]
    friction_counts = frictions.groupby("customer_id").size().to_dict()

    weighted_frictions: dict[str, float] = {}
    if not frictions.empty:
        scores = frictions["aspect"].astype(str).map(weights).fillna(0.20) * frictions[
            "friction_intensity"
        ].astype(float)
        weighted_frictions = scores.groupby(frictions["customer_id"]).sum().to_dict()

    # 3. Inatividade observada no período alvo (churn_observed_12m)
    last_tx_date = transactions_df.groupby("customer_id")["transaction_date"].max().to_dict()

    # Estimativa de intervalo típico por cliente a partir de voos totais
    total_tx_counts = transactions_df.groupby("customer_id").size().to_dict()

    gt_records: list[dict[str, Any]] = []
    final_statuses: list[str] = []

    for c in customers_df.itertuples():
        cid = str(c.customer_id)
        arch = str(c.archetype)
        tier = str(getattr(c, "current_tier", "azul"))
        arch_info = archetypes_cfg.get(arch, {})

        base_hazard = float(arch_info.get("base_churn_hazard_annual", 0.15))
        annual_freq = float(arch_info.get("trips_per_year_mean", 6.0))
        price_sens = float(arch_info.get("price_elasticity", -1.0))
        redemp_prop = float(arch_info.get("redemption_propensity", 0.30))

        theta_freq = float(c.latent_freq_effect)
        theta_spend = float(c.latent_spend_effect)
        theta_churn = float(c.latent_churn_effect)

        tot_frictions = int(friction_counts.get(cid, 0))
        wf = float(weighted_frictions.get(cid, 0.0))

        tier_red = float(tier_reduction_map.get(tier, 0.0))

        # Hazard de risco proporcional
        hazard = base_hazard * np.exp(theta_churn + 0.35 * wf - tier_red)
        hazard = max(0.01, min(3.0, hazard))

        p_churn_latent = 1.0 - np.exp(-hazard)
        latent_churn_event = 1 if rng.random() < p_churn_latent else 0

        # Evasão observada: inatividade > 180 dias ao término da janela
        last_date = last_tx_date.get(cid, pd.to_datetime(c.join_date))
        inactivity_days = (target_end - last_date).days

        n_tx = total_tx_counts.get(cid, 1)
        typical_interval = 365.0 / max(1.0, float(n_tx) / 3.0)
        is_inactive = (
            1 if (inactivity_days >= 180 and inactivity_days >= 2.0 * typical_interval) else 0
        )

        clv_12m = float(round(clv_by_cust.get(cid, 0.0), 2))

        final_status = "inativo" if is_inactive == 1 else "ativo"
        final_statuses.append(final_status)

        gt_records.append(
            {
                "customer_id": cid,
                "latent_archetype": arch,
                "clv_real_12m": clv_12m,
                "churn_observed_12m": int(is_inactive),
                "latent_churn_event_12m": int(latent_churn_event),
                "latent_base_hazard": float(round(base_hazard, 4)),
                "latent_annual_frequency": float(round(annual_freq, 2)),
                "latent_price_sensitivity": float(round(price_sens, 4)),
                "latent_redemption_propensity": float(round(redemp_prop, 4)),
                "latent_freq_effect": float(round(theta_freq, 4)),
                "latent_spend_effect": float(round(theta_spend, 4)),
                "latent_churn_effect": float(round(theta_churn, 4)),
                "total_frictions_lifetime": tot_frictions,
            }
        )

    ground_truth_df = pd.DataFrame(gt_records)

    updated_cust = customers_df.copy()
    updated_cust["status"] = final_statuses
    # Remover colunas latentes de auditoria da tabela pública de customers
    drop_cols = [
        "latent_freq_effect",
        "latent_spend_effect",
        "latent_redemption_effect",
        "latent_churn_effect",
    ]
    updated_cust = updated_cust.drop(
        columns=[col for col in drop_cols if col in updated_cust.columns]
    )

    return ground_truth_df, updated_cust
