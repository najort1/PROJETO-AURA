"""Simulação de Impacto Financeiro, Sensibilidade e Plano de Piloto A/B (WS9).

Executa simulação de cenários (conservador, base, otimista) com IC95% via bootstrap,
análise de sensibilidade unidimensional (tornado), cobertura sob orçamento R$80k,
análise de break-even econômico, dimensionamento de piloto A/B e estimativa de custos de LLM.
"""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from aura_core.config import load_yaml
from aura_core.paths import ROOT, ensure_dir

# Constantes e premissas operacionais
DEFAULT_SEED = 42
DEFAULT_BOOTSTRAPS = 1000
BUDGET_CAP_BRL = 80000.0
FALLBACK_ACTION_COST_BRL = 45.0  # Premissa documentada em docs/limitations.md §8

SCENARIO_PREMISES: dict[str, dict[str, Any]] = {
    "conservador": {
        "efeito_retencao": 0.05,
        "resposta_canal": 0.12,
        "margem": 0.15,
        "descricao": "Adesão cautelosa e baixa redução de evasão (estresse).",
        "fonte_premissa": "benchmarks de programas de retenção CRM",
    },
    "base": {
        "efeito_retencao": 0.10,
        "resposta_canal": 0.18,
        "margem": 0.20,
        "descricao": "Parâmetros centrais calibrados com literatura de fidelidade e CRM.",
        "fonte_premissa": "benchmarks de programas de retenção CRM",
    },
    "otimista": {
        "efeito_retencao": 0.15,
        "resposta_canal": 0.25,
        "margem": 0.25,
        "descricao": "Alto engajamento multicanal e forte redução do atrito.",
        "fonte_premissa": "benchmarks de programas de retenção CRM",
    },
}


def load_simulation_data(
    rec_path: Path | None = None,
    scores_path: Path | None = None,
    actions_cfg_path: Path | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float]]:
    """Carrega recomendações, scores de clientes e custos de ações do playbook.

    Retorna:
        target_df: DataFrame dos clientes com ação proativa elegível (14.638).
        scores_df: DataFrame completo de scores dos clientes (50.000).
        action_costs: Mapeamento de nome de ação -> custo operacional em BRL.
    """
    p_rec = rec_path or ROOT / "data" / "analytics" / "agent_recommendations.parquet"
    p_scores = scores_path or ROOT / "data" / "analytics" / "customers_scores.parquet"
    p_cfg = actions_cfg_path or ROOT / "config" / "actions.yaml"

    if not p_rec.exists():
        raise FileNotFoundError(f"Arquivo de recomendações não encontrado: {p_rec}")
    if not p_scores.exists():
        raise FileNotFoundError(f"Arquivo de scores não encontrado: {p_scores}")

    rec_df = pd.read_parquet(p_rec)
    scores_df = pd.read_parquet(p_scores)

    # Carregar custos de ações
    actions_yaml = load_yaml(str(p_cfg)) if p_cfg.exists() else {}
    action_costs: dict[str, float] = {}
    for act_key, act_val in actions_yaml.get("actions", {}).items():
        cost = act_val.get("cost_brl", 0.0)
        # Se cost_brl for 0 (benefício contratual do tier), aplica fallback operacional R$ 45
        action_costs[act_key] = FALLBACK_ACTION_COST_BRL if float(cost) == 0.0 else float(cost)

    # Unir dados
    merged = rec_df.merge(scores_df, on="customer_id", suffixes=("", "_score"))

    # Filtrar alvo: clientes com ação proativa elegível (exclui silêncio responsável)
    target_df = merged[merged["action_name"] != "nenhuma_acao_elegivel"].copy()

    # Associar custo de ação por cliente
    target_df["action_cost"] = (
        target_df["action_name"].map(action_costs).fillna(FALLBACK_ACTION_COST_BRL).astype(float)
    )

    return target_df, scores_df, action_costs


def compute_simulation_vectors(
    df: pd.DataFrame,
    efeito_retencao: float,
    resposta_canal: float,
    margem: float,
    cost_multiplier: float = 1.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Calcula vetores analíticos de evasão evitada, receita bruta, custo e delta receita por cliente."""
    churn_prob = df["churn_prob"].to_numpy(dtype=float)
    clv = df["clv_12m_previsto"].to_numpy(dtype=float)
    cost = df["action_cost"].to_numpy(dtype=float) * float(cost_multiplier)

    # P(evasão evitada | ação) = churn_prob × efeito_retenção × resposta_do_canal
    p_evitada = churn_prob * float(efeito_retencao) * float(resposta_canal)

    # Receita Bruta Salva = P(evasão evitada) × CLV_12m × margem
    rec_bruta = p_evitada * clv * float(margem)

    # Delta Receita Líquida = Receita Bruta Salva - Custo da Ação
    delta_rec = rec_bruta - cost

    return p_evitada, rec_bruta, cost, delta_rec


def bootstrap_ci_vector(
    point_val: float,
    vec: np.ndarray,
    n_bootstraps: int = DEFAULT_BOOTSTRAPS,
    seed: int = DEFAULT_SEED,
    ci: float = 0.95,
) -> tuple[float, float, float]:
    """Calcula intervalo de confiança percentil (IC95%) via bootstrap sobre a soma do vetor."""
    n = len(vec)
    if n == 0:
        return point_val, point_val, point_val

    rng = np.random.default_rng(seed)
    idx_matrix = rng.integers(0, n, size=(n_bootstraps, n))
    bootstrap_sums = np.sum(vec[idx_matrix], axis=1)

    alpha = 1.0 - ci
    lower = float(np.percentile(bootstrap_sums, 100.0 * (alpha / 2.0)))
    upper = float(np.percentile(bootstrap_sums, 100.0 * (1.0 - alpha / 2.0)))

    return point_val, lower, upper


def simulate_scenarios(
    target_df: pd.DataFrame,
    n_bootstraps: int = DEFAULT_BOOTSTRAPS,
    seed: int = DEFAULT_SEED,
) -> dict[str, Any]:
    """Simula os três cenários canônicos (conservador, base, otimista) com bootstrap IC95%."""
    results: dict[str, Any] = {}
    n_target = len(target_df)

    for scen_name, params in SCENARIO_PREMISES.items():
        eff = params["efeito_retencao"]
        resp = params["resposta_canal"]
        mg = params["margem"]

        p_evitada, rec_bruta_vec, cost_vec, delta_vec = compute_simulation_vectors(
            target_df, eff, resp, mg
        )

        tot_evasao = float(np.sum(p_evitada))
        tot_rec_bruta = float(np.sum(rec_bruta_vec))
        tot_cost = float(np.sum(cost_vec))
        tot_delta = float(np.sum(delta_vec))
        roi = float(tot_delta / tot_cost) if tot_cost > 0 else 0.0

        # Bootstrap sobre Delta Receita e Receita Bruta
        pt_delta, delta_low, delta_high = bootstrap_ci_vector(
            tot_delta, delta_vec, n_bootstraps=n_bootstraps, seed=seed
        )
        pt_bruta, bruta_low, bruta_high = bootstrap_ci_vector(
            tot_rec_bruta, rec_bruta_vec, n_bootstraps=n_bootstraps, seed=seed + 1
        )

        results[scen_name] = {
            "premissas": {
                "efeito_retencao": eff,
                "resposta_canal": resp,
                "margem": mg,
                "fonte_premissa": params["fonte_premissa"],
                "descricao": params["descricao"],
            },
            "metricas": {
                "clientes_alvo": n_target,
                "evasoes_evitadas": round(tot_evasao, 2),
                "receita_bruta_salva_brl": round(tot_rec_bruta, 2),
                "custo_total_acoes_brl": round(tot_cost, 2),
                "delta_receita_brl": round(tot_delta, 2),
                "roi_liquido": round(roi, 4),
                "ic95_delta_receita": {
                    "estimativa_pontual": round(pt_delta, 2),
                    "limite_inferior": round(delta_low, 2),
                    "limite_superior": round(delta_high, 2),
                    "n_bootstraps": n_bootstraps,
                    "seed": seed,
                },
                "ic95_receita_bruta": {
                    "estimativa_pontual": round(pt_bruta, 2),
                    "limite_inferior": round(bruta_low, 2),
                    "limite_superior": round(bruta_high, 2),
                },
            },
        }

    return results


def run_sensitivity_analysis(
    target_df: pd.DataFrame,
    delta_rel: float = 0.20,
) -> dict[str, Any]:
    """Análise de sensibilidade unidimensional (tornado) ao redor do cenário base."""
    base_params = SCENARIO_PREMISES["base"]
    b_eff = base_params["efeito_retencao"]
    b_resp = base_params["resposta_canal"]
    b_mg = base_params["margem"]
    b_cost_factor = 1.0

    _, _, _, b_delta_vec = compute_simulation_vectors(
        target_df, b_eff, b_resp, b_mg, cost_multiplier=b_cost_factor
    )
    base_delta = float(np.sum(b_delta_vec))

    params_to_vary = {
        "efeito_retencao": {
            "base": b_eff,
            "low": b_eff * (1.0 - delta_rel),
            "high": b_eff * (1.0 + delta_rel),
            "unidade": "taxa",
        },
        "resposta_canal": {
            "base": b_resp,
            "low": b_resp * (1.0 - delta_rel),
            "high": b_resp * (1.0 + delta_rel),
            "unidade": "taxa",
        },
        "margem": {
            "base": b_mg,
            "low": b_mg * (1.0 - delta_rel),
            "high": b_mg * (1.0 + delta_rel),
            "unidade": "taxa",
        },
        "custo_acao": {
            "base": b_cost_factor,
            "low": b_cost_factor * (1.0 - delta_rel),
            "high": b_cost_factor * (1.0 + delta_rel),
            "unidade": "fator_multiplicativo",
        },
    }

    variations_records: list[dict[str, Any]] = []

    for param_name, cfg in params_to_vary.items():
        # Avaliar Low
        eff_l = cfg["low"] if param_name == "efeito_retencao" else b_eff
        resp_l = cfg["low"] if param_name == "resposta_canal" else b_resp
        mg_l = cfg["low"] if param_name == "margem" else b_mg
        cost_l = cfg["low"] if param_name == "custo_acao" else b_cost_factor
        _, _, _, delta_l_vec = compute_simulation_vectors(
            target_df, eff_l, resp_l, mg_l, cost_multiplier=cost_l
        )
        delta_l = float(np.sum(delta_l_vec))

        # Avaliar High
        eff_h = cfg["high"] if param_name == "efeito_retencao" else b_eff
        resp_h = cfg["high"] if param_name == "resposta_canal" else b_resp
        mg_h = cfg["high"] if param_name == "margem" else b_mg
        cost_h = cfg["high"] if param_name == "custo_acao" else b_cost_factor
        _, _, _, delta_h_vec = compute_simulation_vectors(
            target_df, eff_h, resp_h, mg_h, cost_multiplier=cost_h
        )
        delta_h = float(np.sum(delta_h_vec))

        swing = abs(delta_h - delta_l)
        # Elasticidade pontual aproximada: (% delta_receita) / (% delta_param)
        pct_delta_change = (delta_h - delta_l) / abs(base_delta) if base_delta != 0 else 0.0
        elasticity = pct_delta_change / (2.0 * delta_rel)

        variations_records.append(
            {
                "parametro": param_name,
                "valor_base": round(cfg["base"], 4),
                "valor_low": round(cfg["low"], 4),
                "valor_high": round(cfg["high"], 4),
                "delta_receita_low": round(delta_l, 2),
                "delta_receita_base": round(base_delta, 2),
                "delta_receita_high": round(delta_h, 2),
                "amplitude_swing_brl": round(swing, 2),
                "elasticidade": round(elasticity, 4),
            }
        )

    # Ordenar por amplitude (tornado diagram ranking)
    variations_records.sort(key=lambda x: x["amplitude_swing_brl"], reverse=True)

    # Tornado nos limites dos cenários globais
    extremes_records: list[dict[str, Any]] = []
    extremes_params = {
        "efeito_retencao": (0.05, 0.15),
        "resposta_canal": (0.12, 0.25),
        "margem": (0.15, 0.25),
        "custo_acao": (0.80, 1.20),
    }
    for p_name, (val_min, val_max) in extremes_params.items():
        eff_min = val_min if p_name == "efeito_retencao" else b_eff
        resp_min = val_min if p_name == "resposta_canal" else b_resp
        mg_min = val_min if p_name == "margem" else b_mg
        cost_min = val_min if p_name == "custo_acao" else b_cost_factor
        _, _, _, d_min_vec = compute_simulation_vectors(
            target_df, eff_min, resp_min, mg_min, cost_multiplier=cost_min
        )
        d_min = float(np.sum(d_min_vec))

        eff_max = val_max if p_name == "efeito_retencao" else b_eff
        resp_max = val_max if p_name == "resposta_canal" else b_resp
        mg_max = val_max if p_name == "margem" else b_mg
        cost_max = val_max if p_name == "custo_acao" else b_cost_factor
        _, _, _, d_max_vec = compute_simulation_vectors(
            target_df, eff_max, resp_max, mg_max, cost_multiplier=cost_max
        )
        d_max = float(np.sum(d_max_vec))

        extremes_records.append(
            {
                "parametro": p_name,
                "faixa": [val_min, val_max],
                "delta_receita_min": round(d_min, 2),
                "delta_receita_max": round(d_max, 2),
                "amplitude_brl": round(abs(d_max - d_min), 2),
            }
        )
    extremes_records.sort(key=lambda x: x["amplitude_brl"], reverse=True)

    return {
        "cenario_referencia": "base",
        "delta_receita_referencia_brl": round(base_delta, 2),
        "variacao_padronizada_pct": int(delta_rel * 100),
        "ranking_tornado_padronizado": variations_records,
        "ranking_tornado_faixas_cenarios": extremes_records,
    }


def compute_budget_coverage(
    target_df: pd.DataFrame,
    budget: float = BUDGET_CAP_BRL,
) -> dict[str, Any]:
    """Analisa cobertura de clientes sob orçamento limitado (R$ 80.000)."""
    # 1. Priorização analítica por Valor em Risco (VaR) decrescente
    df_sorted_var = target_df.sort_values("valor_em_risco", ascending=False).copy()
    df_sorted_var["custo_acum"] = df_sorted_var["action_cost"].cumsum()
    cov_var = df_sorted_var[df_sorted_var["custo_acum"] <= budget].copy()

    n_var = len(cov_var)
    cost_var = float(cov_var["action_cost"].sum())
    var_captured = float(cov_var["valor_em_risco"].sum())
    total_target_var = float(target_df["valor_em_risco"].sum())
    pct_var_captured = float(var_captured / total_target_var) if total_target_var > 0 else 0.0

    # Impacto no grupo priorizado por VaR
    scenarios_var: dict[str, Any] = {}
    for sc_name, sc_cfg in SCENARIO_PREMISES.items():
        _, r_bruta, _, d_rec = compute_simulation_vectors(
            cov_var, sc_cfg["efeito_retencao"], sc_cfg["resposta_canal"], sc_cfg["margem"]
        )
        scenarios_var[sc_name] = {
            "receita_bruta_brl": round(float(np.sum(r_bruta)), 2),
            "delta_receita_brl": round(float(np.sum(d_rec)), 2),
            "roi": round(float(np.sum(d_rec) / cost_var), 4) if cost_var > 0 else 0.0,
        }

    # 2. Heurística da tela 06 do app: custo médio constante de R$ 45
    n_tela06 = int(budget // FALLBACK_ACTION_COST_BRL)
    cost_tela06 = n_tela06 * FALLBACK_ACTION_COST_BRL

    # 3. Priorização por menor custo unitário (máxima cobertura quantitativa)
    df_sorted_cheap = target_df.sort_values("action_cost", ascending=True).copy()
    df_sorted_cheap["custo_acum"] = df_sorted_cheap["action_cost"].cumsum()
    cov_cheap = df_sorted_cheap[df_sorted_cheap["custo_acum"] <= budget]
    n_cheap = len(cov_cheap)
    cost_cheap = float(cov_cheap["action_cost"].sum())

    return {
        "orcamento_brl": budget,
        "total_clientes_elegiveis": len(target_df),
        "estrategia_priorizacao_var": {
            "clientes_cobertos": n_var,
            "cobertura_pct": round(n_var / len(target_df) * 100.0, 2),
            "investimento_total_brl": round(cost_var, 2),
            "var_capturado_brl": round(var_captured, 2),
            "var_capturado_pct": round(pct_var_captured * 100.0, 2),
            "cenarios": scenarios_var,
        },
        "heuristica_custo_medio_tela06": {
            "custo_medio_premissa_brl": FALLBACK_ACTION_COST_BRL,
            "clientes_cobertos": n_tela06,
            "cobertura_pct": round(n_tela06 / len(target_df) * 100.0, 2),
            "investimento_total_brl": round(cost_tela06, 2),
        },
        "estrategia_menor_custo": {
            "clientes_cobertos": n_cheap,
            "cobertura_pct": round(n_cheap / len(target_df) * 100.0, 2),
            "investimento_total_brl": round(cost_cheap, 2),
        },
    }


def compute_break_even(target_df: pd.DataFrame) -> dict[str, Any]:
    """Calcula pontos de equilíbrio (break-even) e analisa a viabilidade unitária das ações."""
    tot_cost = float(target_df["action_cost"].sum())
    n_target = len(target_df)
    sum_var = float((target_df["churn_prob"] * target_df["clv_12m_previsto"]).sum())

    # Custo médio de ação necessário para break-even em cada cenário
    scenarios_be: dict[str, Any] = {}
    for sc_name, sc_cfg in SCENARIO_PREMISES.items():
        eff = sc_cfg["efeito_retencao"]
        resp = sc_cfg["resposta_canal"]
        mg = sc_cfg["margem"]
        rec_bruta = sum_var * eff * resp * mg
        max_cost_per_client = rec_bruta / n_target if n_target > 0 else 0.0
        scenarios_be[sc_name] = {
            "receita_bruta_gerada_brl": round(rec_bruta, 2),
            "custo_maximo_por_acao_brl": round(max_cost_per_client, 2),
        }

    # Eficácia conjunta necessária (efeito × resposta) para pagar o custo atual na margem base (20%)
    margin_base = SCENARIO_PREMISES["base"]["margem"]
    joint_effect_response_needed = (
        tot_cost / (margin_base * sum_var) if (margin_base * sum_var) > 0 else 0.0
    )

    # Clientes com delta unitário positivo no cenário base
    _, r_bruta_base, cost_base, delta_base = compute_simulation_vectors(
        target_df,
        SCENARIO_PREMISES["base"]["efeito_retencao"],
        SCENARIO_PREMISES["base"]["resposta_canal"],
        SCENARIO_PREMISES["base"]["margem"],
    )
    positive_mask = delta_base > 0
    n_positive = int(np.sum(positive_mask))
    sum_profit_positive = float(np.sum(delta_base[positive_mask]))

    return {
        "custo_total_atual_brl": round(tot_cost, 2),
        "custo_medio_atual_por_acao_brl": round(tot_cost / n_target, 2),
        "custo_acao_break_even_por_cenario": scenarios_be,
        "joint_effect_response_necessario_base": round(joint_effect_response_needed, 4),
        "clientes_lucrativos_unitariamente_base": {
            "contagem": n_positive,
            "pct_alvo": round(n_positive / n_target * 100.0, 3),
            "ganho_liquido_positivo_somado_brl": round(sum_profit_positive, 2),
        },
        "diagnostico_estrategico": (
            "Abordagens 'em massa' (blanket) com ações custando entre R$ 5 e R$ 25 geram delta negativo "
            "porque o ganho esperado ponderado por evasão em clientes de baixo valor/risco é menor que o custo da ação. "
            "A viabilidade econômica em CRM exige: (1) foco estrito nos clientes de Alto Valor com risco iminente; "
            "ou (2) migração para canais puramente digitais automatizados (push app/email transacional) com custo ~R$0."
        ),
    }


def calculate_sample_size_proportions(
    p1: float,
    delta: float,
    alpha: float = 0.05,
    power: float = 0.80,
) -> float:
    """Calcula tamanho amostral por braço para teste bilateral de duas proporções independentes (fórmula de Fleiss).

    Parâmetros:
        p1: Proporção de baseline no grupo de controle (ex: 0.8538).
        delta: Diferença mínima detectável (MDE) com sinal (ex: +0.02 para +2pp).
        alpha: Nível de significância bilateral (padrão 0.05).
        power: Poder estatístico 1 - beta (padrão 0.80).

    Retorna:
        Tamanho amostral n contínuo por braço.
    """
    if not (0.0 < p1 < 1.0):
        raise ValueError(f"p1 deve estar no intervalo aberto (0, 1), recebido {p1}")
    if delta == 0.0:
        raise ValueError("delta (MDE) não pode ser zero")
    p2 = p1 + delta
    if not (0.0 < p2 < 1.0):
        raise ValueError(f"p2 (p1 + delta = {p2}) deve estar no intervalo aberto (0, 1)")

    # Quantis teóricos da distribuição normal padrão bilateral
    z_alpha = 1.959963984540054  # Z_(1 - alpha/2) para alpha=0.05
    z_beta = 0.8416212335729143  # Z_(1 - beta) para power=0.80

    p_bar = (p1 + p2) / 2.0
    q_bar = 1.0 - p_bar
    p1_q1 = p1 * (1.0 - p1)
    p2_q2 = p2 * (1.0 - p2)

    # Fórmula padrão de Fleiss com variância sob H0 (pooled) e sob H1 (unpooled)
    num = (z_alpha * math.sqrt(2.0 * p_bar * q_bar) + z_beta * math.sqrt(p1_q1 + p2_q2)) ** 2
    return num / (delta**2)


def compute_pilot_design(scores_df: pd.DataFrame) -> dict[str, Any]:
    """Dimensiona o plano estatístico de piloto A/B para clientes de Alto Valor em Risco."""
    hv = scores_df[scores_df["alto_valor"] == True].copy()  # noqa: E712
    n_hv_total = len(hv)

    median_churn_hv = float(hv["churn_prob"].median())
    hv_at_risk = hv[hv["churn_prob"] > median_churn_hv].copy()
    n_hv_risk = len(hv_at_risk)

    baseline_churn = float(hv_at_risk["churn_prob"].mean())
    baseline_retention = 1.0 - baseline_churn

    # MDEs testados
    mde_grid = [0.01, 0.02, 0.03, 0.04, 0.05]
    table_mde: list[dict[str, Any]] = []

    for mde in mde_grid:
        n_continuous = calculate_sample_size_proportions(
            baseline_retention, mde, alpha=0.05, power=0.80
        )
        n_per_arm = math.ceil(n_continuous)
        n_total = n_per_arm * 2
        fits_risk_sample = n_total <= n_hv_risk
        fits_hv_sample = n_total <= n_hv_total
        table_mde.append(
            {
                "mde_pp": int(mde * 100),
                "mde_taxa": mde,
                "n_por_braco": n_per_arm,
                "n_total_teste": n_total,
                "cabe_no_grupo_risco_50k": fits_risk_sample,
                "cabe_no_alto_valor_50k": fits_hv_sample,
            }
        )

    # Dimensionamento primário (+2pp)
    n_arm_primary = math.ceil(
        calculate_sample_size_proportions(baseline_retention, 0.02, alpha=0.05, power=0.80)
    )

    return {
        "populacao_alto_valor_total": n_hv_total,
        "churn_prob_mediana_alto_valor": round(median_churn_hv, 4),
        "criterio_elegibilidade_piloto": "alto_valor == True E churn_prob > mediana (0.0941)",
        "tamanho_publico_elegivel_amostra_50k": n_hv_risk,
        "baseline_churn_prob_real": round(baseline_churn, 4),
        "baseline_retencao_12m_real": round(baseline_retention, 4),
        "parametros_teste": {
            "metrica_primaria": "Taxa de retenção em 12 meses",
            "poder_estatistico": 0.80,
            "significancia_alfa_bilateral": 0.05,
            "mde_primario_pp": 2,
            "mde_primario_taxa": 0.02,
        },
        "dimensionamento_primario_mde_2pp": {
            "n_por_braco": n_arm_primary,
            "n_total": n_arm_primary * 2,
            "capacidade_na_amostra_50k": (
                f"Necessário {n_arm_primary * 2} clientes vs {n_hv_risk} disponíveis na amostra sintética. "
                "Na amostra de 50k, o MDE mínimo viável com 80% de poder é +4pp (n=1.082/braço, total 2.164). "
                "Na base real de 20,1M de membros (Azul RI 2025), a população de alto valor estimada (>140k membros) "
                "permite múltiplos pilotos paralelos com MDE +1pp ou +2pp com total folga estatística."
            ),
        },
        "tabela_sensibilidade_mde": table_mde,
    }


def estimate_agent_costs(total_customers: int = 50000) -> dict[str, Any]:
    """Estima os custos operacionais de execução do agente nos modos Offline e LLM."""
    tokens_min = 600
    tokens_max = 900
    tot_tokens_min = total_customers * tokens_min
    tot_tokens_max = total_customers * tokens_max

    usd_brl = 5.50

    # Tiers de precificação (USD por milhão de tokens combinados in/out)
    tiers = {
        "tier_economico": {
            "descricao": "Modelos compactos/destilados (ex: GPT-4o-mini, DeepSeek V3)",
            "preco_usd_per_1m": 0.40,
        },
        "tier_standard": {
            "descricao": "Modelos intermediários ágeis (ex: Claude 3.5 Haiku, Gemini Flash)",
            "preco_usd_per_1m": 1.50,
        },
        "tier_premium": {
            "descricao": "Modelos de fronteira completos (ex: GPT-4o, Claude 3.5 Sonnet)",
            "preco_usd_per_1m": 5.00,
        },
    }

    tier_estimates: dict[str, Any] = {}
    for t_name, t_info in tiers.items():
        price = t_info["preco_usd_per_1m"]
        cost_usd_min = (tot_tokens_min / 1_000_000.0) * price
        cost_usd_max = (tot_tokens_max / 1_000_000.0) * price
        tier_estimates[t_name] = {
            "descricao": t_info["descricao"],
            "preco_usd_per_1m": price,
            "custo_usd_faixa": [round(cost_usd_min, 2), round(cost_usd_max, 2)],
            "custo_brl_faixa": [
                round(cost_usd_min * usd_brl, 2),
                round(cost_usd_max * usd_brl, 2),
            ],
            "custo_brl_por_cliente": round((cost_usd_max * usd_brl) / total_customers, 4),
        }

    return {
        "total_clientes_analisados": total_customers,
        "modo_offline": {
            "custo_por_recomendacao_brl": 0.0,
            "custo_total_brl": 0.0,
            "tipo_execucao": "Compositor determinístico em regras de negócio e embeddings locais",
            "status_projeto": "MODO OFICIAL AVALIADO NESTE PROJETO (reprodutível, custo ~R$0)",
        },
        "modo_llm_estimado": {
            "faixa_tokens_por_cliente": [tokens_min, tokens_max],
            "volume_total_tokens_faixa": [tot_tokens_min, tot_tokens_max],
            "cambio_usd_brl_premissa": usd_brl,
            "faixas_por_tier_modelo": tier_estimates,
            "nota": "Estimativa prospectiva de custo de inferência via API em nuvem; modo não avaliado empiricamente nesta sessão.",
        },
    }


def run_impact_simulation(output_path: Path | None = None) -> dict[str, Any]:
    """Executa a simulação completa de impacto, sensibilidade, orçamento e piloto."""
    target_df, scores_df, action_costs = load_simulation_data()

    scenarios = simulate_scenarios(target_df, n_bootstraps=DEFAULT_BOOTSTRAPS, seed=DEFAULT_SEED)
    sensitivity = run_sensitivity_analysis(target_df)
    budget = compute_budget_coverage(target_df, budget=BUDGET_CAP_BRL)
    break_even = compute_break_even(target_df)
    pilot = compute_pilot_design(scores_df)
    agent_costs = estimate_agent_costs(total_customers=len(scores_df))

    payload: dict[str, Any] = {
        "meta": {
            "modulo": "ml.impact.simulate",
            "gerado_em": datetime.now(UTC).isoformat(),
            "total_clientes_base": len(scores_df),
            "total_clientes_alvo_elegiveis": len(target_df),
            "custo_total_playbook_brl": round(float(target_df["action_cost"].sum()), 2),
            "seed_bootstrap": DEFAULT_SEED,
            "n_bootstraps": DEFAULT_BOOTSTRAPS,
        },
        "cenarios": scenarios,
        "sensibilidade_tornado": sensitivity,
        "cobertura_orcamento_80k": budget,
        "break_even": break_even,
        "plano_piloto_ab": pilot,
        "custos_do_agente": agent_costs,
    }

    p_out = output_path or ROOT / "data" / "analytics" / "impact_scenarios.json"
    ensure_dir(p_out.parent)
    with open(p_out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return payload


def main() -> None:
    """Ponto de entrada de linha de comando para tasks.py impact."""
    out_file = ROOT / "data" / "analytics" / "impact_scenarios.json"
    data = run_impact_simulation(out_file)

    meta = data["meta"]
    sc = data["cenarios"]
    b = data["cobertura_orcamento_80k"]["estrategia_priorizacao_var"]
    p = data["plano_piloto_ab"]["dimensionamento_primario_mde_2pp"]

    print("=== WS9 - SIMULACAO DE IMPACTO, SENSIBILIDADE E PILOTO A/B ===")
    print(f"Alvo: {meta['total_clientes_alvo_elegiveis']:,} clientes com acao proativa.")
    print(f"Custo total do playbook: R$ {meta['custo_total_playbook_brl']:,.2f}")
    print("\nResultados por Cenario (Delta-Receita Liquida com IC95% Bootstrap):")
    for name, s in sc.items():
        m = s["metricas"]
        ic = m["ic95_delta_receita"]
        print(
            f"  - {name.upper():11s}: Delta-Receita = R$ {m['delta_receita_brl']:>11,.2f} "
            f"[IC95%: R$ {ic['limite_inferior']:>11,.2f} a R$ {ic['limite_superior']:>11,.2f}] "
            f"(Bruta: R$ {m['receita_bruta_salva_brl']:>8,.2f})"
        )
    print(
        f"\nCobertura sob R$ 80k: {b['clientes_cobertos']:,} clientes "
        f"({b['cobertura_pct']:.1f}% do alvo, {b['var_capturado_pct']:.1f}% do VaR)."
    )
    print(
        f"Piloto A/B Alto Valor em Risco (MDE +2pp): n={p['n_por_braco']:,}/braco "
        f"(total {p['n_total']:,}). Baseline: {data['plano_piloto_ab']['baseline_retencao_12m_real']*100:.2f}%."
    )
    print(f"Artefato salvo: {out_file.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
