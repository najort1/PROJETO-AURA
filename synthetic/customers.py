"""Geração de clientes sintéticos com arquétipos latentes e efeitos aleatórios (WS2)."""

from __future__ import annotations

import datetime as dt
from typing import Any

import numpy as np
import pandas as pd


def build_heterogeneity_cov_matrix(het_config: dict[str, Any]) -> tuple[np.ndarray, list[str]]:
    """Constrói matriz de covariânciaSigma para os efeitos aleatórios latentes."""
    dims = het_config.get("dimensions", ["frequency", "spend", "redemption", "churn"])
    stds = np.array(het_config.get("std_deviations", [0.38, 0.32, 0.40, 0.28]), dtype=float)
    corr_cfg = het_config.get("correlations", {})

    p = len(dims)
    corr_mat = np.eye(p, dtype=float)

    pair_map = {
        ("frequency", "spend"): corr_cfg.get("freq_spend", 0.52),
        ("frequency", "redemption"): corr_cfg.get("freq_redemption", 0.15),
        ("frequency", "churn"): corr_cfg.get("freq_churn", -0.34),
        ("spend", "redemption"): corr_cfg.get("spend_redemption", 0.20),
        ("spend", "churn"): corr_cfg.get("spend_churn", -0.25),
        ("redemption", "churn"): corr_cfg.get("redemption_churn", 0.12),
    }

    for (d1, d2), val in pair_map.items():
        if d1 in dims and d2 in dims:
            i, j = dims.index(d1), dims.index(d2)
            corr_mat[i, j] = val
            corr_mat[j, i] = val

    cov_mat = np.outer(stds, stds) * corr_mat
    # Garantir simetria e positiva definida
    cov_mat = (cov_mat + cov_mat.T) / 2.0
    min_eig = np.min(np.real(np.linalg.eigvals(cov_mat)))
    if min_eig < 1e-6:
        cov_mat += np.eye(p) * (abs(min_eig) + 1e-4)

    return cov_mat, dims


def generate_customers(
    n_customers: int,
    rng: np.random.Generator,
    generator_config: dict[str, Any],
    simulation_start: dt.date,
) -> pd.DataFrame:
    """Gera população sintética de clientes com atributos cadastrais e variáveis latentes.

    Atributos demográficos (faixa_etaria, genero, regiao) são estritamente para
    auditoria de viés e LGPD (sensitive=True), nunca para features de modelos.
    """
    archetypes_cfg = generator_config.get("archetypes", {})
    archetype_names = list(archetypes_cfg.keys())
    archetype_shares = [archetypes_cfg[k].get("share", 0.20) for k in archetype_names]
    archetype_shares = np.array(archetype_shares, dtype=float)
    archetype_shares /= archetype_shares.sum()

    # Amostragem de arquétipos latentes
    archetype_indices = rng.choice(len(archetype_names), size=n_customers, p=archetype_shares)
    chosen_archetypes = [archetype_names[idx] for idx in archetype_indices]

    # Distribuição geográfica coerente com a malha Azul (hubs principais: VCP, CNF, REC, CGB, BEL)
    regions = ["Sudeste", "Sul", "Nordeste", "Centro-Oeste", "Norte"]
    region_shares = [0.52, 0.18, 0.16, 0.10, 0.04]
    customer_regions = rng.choice(regions, size=n_customers, p=region_shares)

    airports_by_region = {
        "Sudeste": (
            ["VCP", "CNF", "SDU", "GIG", "GRU", "CGH", "RAO", "SJP", "VIX"],
            [0.44, 0.26, 0.08, 0.05, 0.05, 0.04, 0.03, 0.03, 0.02],
        ),
        "Sul": (["CWB", "POA", "FLN", "NVT", "XAP", "IGU"], [0.34, 0.30, 0.16, 0.10, 0.05, 0.05]),
        "Nordeste": (
            ["REC", "SSA", "FOR", "NAT", "MCZ", "JDO", "IOS"],
            [0.55, 0.18, 0.11, 0.06, 0.04, 0.03, 0.03],
        ),
        "Centro-Oeste": (["BSB", "CGB", "GYN", "CGR"], [0.40, 0.35, 0.15, 0.10]),
        "Norte": (["BEL", "MAO", "PVH", "MCP"], [0.52, 0.30, 0.10, 0.08]),
    }

    home_airports: list[str] = []
    for reg in customer_regions:
        ap_list, ap_probs = airports_by_region[reg]
        home_airports.append(rng.choice(ap_list, p=ap_probs))

    # Atributos demográficos com missing MCAR documentado (config/generator.yaml: missing_data)
    missing_cfg = (
        generator_config.get("latent", {})
        .get("missing_data", {})
        .get("demographic_missing_rates", {})
    )
    gender_missing_rate = missing_cfg.get("genero", 0.038)
    age_missing_rate = missing_cfg.get("faixa_etaria", 0.012)

    age_groups = ["18-24", "25-34", "35-44", "45-59", "60+"]
    age_probs = [0.12, 0.31, 0.28, 0.21, 0.08]
    sampled_ages = pd.Series(
        rng.choice(age_groups, size=n_customers, p=age_probs).astype(object),
        dtype="string",
    )
    age_mask = rng.random(size=n_customers) < age_missing_rate
    sampled_ages[age_mask] = None

    genders = ["M", "F", "Outro", "Prefiro nao informar"]
    gender_probs = [0.49, 0.48, 0.01, 0.02]
    sampled_genders = pd.Series(
        rng.choice(genders, size=n_customers, p=gender_probs).astype(object),
        dtype="string",
    )
    gender_mask = rng.random(size=n_customers) < gender_missing_rate
    sampled_genders[gender_mask] = None

    # Datas de adesão: desde 2018 até metade da simulação (para haver histórico variado)
    start_history = dt.date(2018, 1, 1)
    end_history = dt.date(2025, 6, 30)
    total_days = (end_history - start_history).days
    sampled_days = rng.integers(0, total_days, size=n_customers)
    join_dates = [
        dt.datetime.combine(start_history + dt.timedelta(days=int(d)), dt.time(0, 0, 0))
        for d in sampled_days
    ]

    # Efeitos aleatórios multivariados (heterogeneidade não observada)
    het_cfg = generator_config.get("latent", {}).get("heterogeneity", {})
    cov_mat, _ = build_heterogeneity_cov_matrix(het_cfg)
    random_effects = rng.multivariate_normal(
        mean=np.zeros(cov_mat.shape[0]), cov=cov_mat, size=n_customers
    )

    customer_ids = [f"C{i + 1:06d}" for i in range(n_customers)]

    df = pd.DataFrame(
        {
            "customer_id": customer_ids,
            "archetype": chosen_archetypes,
            "faixa_etaria": sampled_ages,
            "genero": sampled_genders,
            "regiao": customer_regions,
            "home_airport": home_airports,
            "join_date": join_dates,
            "current_tier": ["azul"] * n_customers,
            "status": ["ativo"] * n_customers,
            # Variáveis latentes preservadas internamente para geração e ground truth
            "latent_freq_effect": random_effects[:, 0],
            "latent_spend_effect": random_effects[:, 1],
            "latent_redemption_effect": random_effects[:, 2],
            "latent_churn_effect": random_effects[:, 3],
        }
    )
    return df
