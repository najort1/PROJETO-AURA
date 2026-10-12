# WORKLOG — WS9: Simulação de Impacto Financeiro, Sensibilidade e Piloto A/B

Registro de execução contínua da frente WS9 (task-10, última frente de implementação do PROJETO AURA 2.0).

---

## 2026-10-12 — Inicialização da Frente WS9
- Estrutura inicial do módulo `ml/impact/` estabelecida com escopo de simulação de cenários, análise de sensibilidade e plano de piloto.
- Dados reais verificados (`agent_recommendations.parquet` com 14.638 elegíveis e `customers_scores.parquet` com 50.000 scores).

## 2026-10-12 — Implementação de ml/impact/simulate.py
- Desenvolvido motor de simulação analítica com cenários (conservador, base, otimista), bootstrap IC95% (1.000 iterações), tornado de sensibilidade e cobertura sob R$ 80k.
- Integrado cálculo de break-even e dimensionamento amostral de piloto A/B (Fleiss two-sample proportions), gerando `data/analytics/impact_scenarios.json`.
- Validada execução ponta a ponta via `tasks.py impact` com saída concisa no console.

## 2026-10-12 — Testes Unitários e Analíticos (tests/test_impact.py)
- Implementada suite rigorosa com 9 testes: caso analítico fechado (p1=0.50, MDE=5pp -> n=1.565), determinismo com seed fixa, monotonicidade dos cenários, custos estritamente positivos e cobertura IC95%.
- Cobertura de testes validada (9/9 aprovados em 3.4s; suite completa com 189 testes aprovados); linter ruff 100% limpo.

## 2026-10-12 — Elaboração do Relatório Completo (docs/impact_simulation.md)
- Redigido documento exaustivo com todos os números reais executados, fórmulas analíticas, premissas rotuladas e análise radical de break-even.
- Estruturado plano formal de piloto A/B com baseline medido (85,38% de retenção no Alto Valor em Risco), dimensionamento por MDE, salvaguardas éticas e estimativa de custos de inferência LLM vs offline.

## 2026-10-12 — Validação Final da Frente WS9
- Executado `python tasks.py impact` ponta a ponta com sucesso.
- Suíte completa de testes executada com 189/189 testes verdes (`tests/test_impact.py` 9/9).
- Linter `ruff check ml/impact tests/test_impact.py` 100% limpo, sem advertências ou erros. Todos os escopos respeitados.

## 2026-10-12 — Correção de Não-Determinismos (Lead, pós-gate)
- O gate de reprodução `tasks.py all` do zero expôs não-determinismos de features (ordem de linhas do DuckDB, empates de rota em `ROW_NUMBER`, soma float de `amount_brl`) — corrigidos na raiz em `dbt/` (ver `docs/limitations.md §7b`).
- `tests/test_impact.py` refactorado: expectativas passaram a ser DERIVADAS dos artefatos (invariantes + faixas + cross-checks), sem contagens hard-coded, imune a deslocamentos de clientes de fronteira.
- Cadeia canônica regenerada do zero (features → train → score → precompute → fairness → impact); treino e score verificados BITWISE estáveis entre execuções consecutivas.
- `docs/impact_simulation.md` atualizado com os números finais canônicos; contagens de alvo/cobertura citadas nos registros históricos acima (14.638/6.170) referem-se aos artefatos pré-regeneração.
