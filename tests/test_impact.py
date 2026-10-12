"""Testes unitários e analíticos para a frente WS9 (ml/impact/simulate.py).

Verifica:
1. Solução analítica fechada de dimensionamento amostral de teste A/B.
2. Determinismo e reprodutibilidade da simulação com seed fixa.
3. Monotonicidade estrita entre os cenários (otimista > base > conservador).
4. Não negatividade de custos e aplicação correta do fallback operacional.
5. Cobertura do intervalo de confiança bootstrap (IC95% contém estimativa pontual).
6. Coerência do orçamento de R$ 80.000 e priorização por VaR.
7. Estatísticas reais do grupo de Alto Valor em Risco e cálculo do baseline.
8. Ranking tornado de sensibilidade e identificação do fator dominante.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from ml.impact.simulate import (
    BUDGET_CAP_BRL,
    FALLBACK_ACTION_COST_BRL,
    calculate_sample_size_proportions,
    compute_break_even,
    compute_budget_coverage,
    compute_pilot_design,
    estimate_agent_costs,
    load_simulation_data,
    run_impact_simulation,
    run_sensitivity_analysis,
    simulate_scenarios,
)


def test_closed_case_sample_size_analytical() -> None:
    """Verifica caso fechado analítico conhecido da literatura: p1=0.50, MDE=0.05 -> n ≈ 1.564-1.565/braço."""
    n_analytical = calculate_sample_size_proportions(0.50, 0.05, alpha=0.05, power=0.80)
    # Valor exato teórico pela fórmula de Fleiss: 1564.67
    assert 1564.0 <= n_analytical <= 1565.0
    assert math.ceil(n_analytical) == 1565

    # Simetria de redução (p1=0.50, MDE=-0.05)
    n_reduction = calculate_sample_size_proportions(0.50, -0.05, alpha=0.05, power=0.80)
    assert pytest.approx(n_analytical, rel=1e-6) == n_reduction

    # Validações de limites e erros
    with pytest.raises(ValueError, match="intervalo aberto"):
        calculate_sample_size_proportions(0.0, 0.05)

    with pytest.raises(ValueError, match="intervalo aberto"):
        calculate_sample_size_proportions(1.0, -0.05)

    with pytest.raises(ValueError, match="não pode ser zero"):
        calculate_sample_size_proportions(0.50, 0.0)

    with pytest.raises(ValueError, match="intervalo aberto"):
        calculate_sample_size_proportions(0.95, 0.10)  # p2 = 1.05 > 1.0


def test_simulation_data_loading_and_costs() -> None:
    """Verifica integridade do carregamento de dados e custos das ações."""
    target_df, scores_df, action_costs = load_simulation_data()

    # 14.638 ações proativas elegíveis na base real
    assert len(target_df) == 14638
    assert len(scores_df) == 50000

    # Ações com cost_brl=0 em actions.yaml recebem fallback operacional R$ 45
    assert action_costs.get("oferta_resgate_especial") == FALLBACK_ACTION_COST_BRL

    # Todos os custos individuais devem ser estritamente positivos
    assert (target_df["action_cost"] > 0).all()
    assert float(target_df["action_cost"].sum()) == 166437.0


def test_scenarios_monotonicity_and_bootstrap_ci() -> None:
    """Verifica ordenação monotônica (otimista > base > conservador) e propriedades do bootstrap IC95%."""
    target_df, _, _ = load_simulation_data()
    scenarios = simulate_scenarios(target_df, n_bootstraps=300, seed=42)

    sc_cons = scenarios["conservador"]["metricas"]
    sc_base = scenarios["base"]["metricas"]
    sc_otim = scenarios["otimista"]["metricas"]

    # Monotonicidade de receita bruta e delta receita
    assert sc_otim["receita_bruta_salva_brl"] > sc_base["receita_bruta_salva_brl"] > sc_cons["receita_bruta_salva_brl"]
    assert sc_otim["delta_receita_brl"] > sc_base["delta_receita_brl"] > sc_cons["delta_receita_brl"]
    assert sc_otim["evasoes_evitadas"] > sc_base["evasoes_evitadas"] > sc_cons["evasoes_evitadas"]

    # Custo total das ações é invariante entre cenários
    assert sc_cons["custo_total_acoes_brl"] == sc_base["custo_total_acoes_brl"] == sc_otim["custo_total_acoes_brl"]
    assert sc_base["custo_total_acoes_brl"] == 166437.0

    # Estimativa pontual deve estar contida dentro do IC95% bootstrap para todos os cenários
    for sc_name in ["conservador", "base", "otimista"]:
        m = scenarios[sc_name]["metricas"]
        ic_delta = m["ic95_delta_receita"]
        assert ic_delta["limite_inferior"] <= ic_delta["estimativa_pontual"] <= ic_delta["limite_superior"]

        ic_bruta = m["ic95_receita_bruta"]
        assert ic_bruta["limite_inferior"] <= ic_bruta["estimativa_pontual"] <= ic_bruta["limite_superior"]


def test_determinism_with_fixed_seed(tmp_path: Path) -> None:
    """Verifica que a simulação é estritamente determinística com seed fixa."""
    target_df, _, _ = load_simulation_data()

    res1 = simulate_scenarios(target_df, n_bootstraps=150, seed=42)
    res2 = simulate_scenarios(target_df, n_bootstraps=150, seed=42)

    assert res1["base"]["metricas"]["ic95_delta_receita"] == res2["base"]["metricas"]["ic95_delta_receita"]

    # Validação ponta a ponta gerando JSON
    p1 = tmp_path / "sim1.json"
    p2 = tmp_path / "sim2.json"
    run_impact_simulation(p1)
    run_impact_simulation(p2)

    with open(p1, encoding="utf-8") as f1, open(p2, encoding="utf-8") as f2:
        d1 = json.load(f1)
        d2 = json.load(f2)

    # Remover timestamp dinâmico para comparação estrita
    d1["meta"].pop("gerado_em")
    d2["meta"].pop("gerado_em")
    assert d1 == d2


def test_budget_coverage_and_var_prioritization() -> None:
    """Verifica conformidade do corte de orçamento de R$ 80.000."""
    target_df, _, _ = load_simulation_data()
    cov = compute_budget_coverage(target_df, budget=BUDGET_CAP_BRL)

    var_strat = cov["estrategia_priorizacao_var"]
    assert var_strat["investimento_total_brl"] <= BUDGET_CAP_BRL
    assert var_strat["clientes_cobertos"] == 6170
    assert var_strat["cobertura_pct"] == pytest.approx(42.15, abs=0.1)
    # Captura mais de 50% do VaR do público alvo apesar de cobrir 42% dos clientes
    assert var_strat["var_capturado_pct"] > 55.0

    # Heurística R$ 45
    t06 = cov["heuristica_custo_medio_tela06"]
    assert t06["clientes_cobertos"] == int(BUDGET_CAP_BRL // 45.0)
    assert t06["investimento_total_brl"] <= BUDGET_CAP_BRL


def test_sensitivity_tornado_ranking() -> None:
    """Verifica que a análise tornado classifica o custo da ação como parâmetro mais impactante."""
    target_df, _, _ = load_simulation_data()
    sens = run_sensitivity_analysis(target_df, delta_rel=0.20)

    ranking = sens["ranking_tornado_padronizado"]
    assert len(ranking) == 4

    param_names = [r["parametro"] for r in ranking]
    assert set(param_names) == {"custo_acao", "efeito_retencao", "resposta_canal", "margem"}

    # Custo da ação possui a maior amplitude absoluta (swing de R$ 66k vs R$ 5k das receitas)
    assert ranking[0]["parametro"] == "custo_acao"
    assert ranking[0]["amplitude_swing_brl"] > 60000.0


def test_break_even_analysis_consistency() -> None:
    """Verifica consistência matemática dos pontos de break-even."""
    target_df, _, _ = load_simulation_data()
    be = compute_break_even(target_df)

    sc_be = be["custo_acao_break_even_por_cenario"]
    # Custos de break-even são monotonicamente crescentes
    assert (
        sc_be["otimista"]["custo_maximo_por_acao_brl"]
        > sc_be["base"]["custo_maximo_por_acao_brl"]
        > sc_be["conservador"]["custo_maximo_por_acao_brl"]
    )

    # Eficácia conjunta necessária é positiva e superior a 15%
    assert 0.15 < be["joint_effect_response_necessario_base"] < 0.35


def test_pilot_design_high_value_at_risk() -> None:
    """Verifica baseline empírico e dimensionamento do piloto A/B para Alto Valor em Risco."""
    _, scores_df, _ = load_simulation_data()
    pilot = compute_pilot_design(scores_df)

    assert pilot["populacao_alto_valor_total"] == 5005
    assert pilot["tamanho_publico_elegivel_amostra_50k"] == 2500
    assert pytest.approx(pilot["churn_prob_mediana_alto_valor"], abs=1e-3) == 0.0941

    # Baseline real de retenção ~85.38% (churn ~14.62%)
    assert 0.14 <= pilot["baseline_churn_prob_real"] <= 0.16
    assert 0.84 <= pilot["baseline_retencao_12m_real"] <= 0.86

    # MDE +2pp exige n ≈ 4.618 por braço
    mde_2pp = pilot["dimensionamento_primario_mde_2pp"]
    assert mde_2pp["n_por_braco"] == 4618
    assert mde_2pp["n_total"] == 9236

    # Tabela de MDEs monotônica decrescente em n
    tbl = pilot["tabela_sensibilidade_mde"]
    for i in range(len(tbl) - 1):
        assert tbl[i]["n_por_braco"] > tbl[i + 1]["n_por_braco"]


def test_agent_cost_offline_and_llm() -> None:
    """Verifica custos operacionais documentados do agente."""
    costs = estimate_agent_costs(50000)

    # Modo offline tem custo estritamente zero
    assert costs["modo_offline"]["custo_por_recomendacao_brl"] == 0.0
    assert costs["modo_offline"]["custo_total_brl"] == 0.0

    # Modo LLM possui faixas coerentes
    llm = costs["modo_llm_estimado"]
    assert llm["faixa_tokens_por_cliente"] == [600, 900]
    assert llm["volume_total_tokens_faixa"] == [30000000, 45000000]

    tiers = llm["faixas_por_tier_modelo"]
    for t_data in tiers.values():
        c_min, c_max = t_data["custo_brl_faixa"]
        assert 0.0 < c_min < c_max
