# Worklog WS7b — Avaliação do Agente sobre Clientes Reais

## 2025-05-18 — Início da WS7b
- Inicialização do módulo `ml/eval/` e criação do arquivo de rastreamento `ml/eval/WORKLOG_WS7B.md`.
- Escopo definido: amostragem estratificada (≥120 clientes), execução do `RetentionAgentPipeline`, métricas agregadas, testes adversariais em dados reais e relatórios.

## 2025-05-18 — Inspeção de Dados e Arquitetura do Agente
- Inspeção de `data/analytics/agent_input.parquet`: 50.000 clientes, 6 personas, 4 tiers presentes (azul, topázio, safira, diamante; ausência empírica de diamante_unique documentada).
- Risco: concentração em risco_baixo_estavel (44.995) e risco_baixo_potencial_alto (4.984); riscos médio/alto concentram 21 clientes no total.
- Teste preliminar do pipeline em amostra real confirmou geração correta de ações e ACT-NO-ACTION para perfis sem ofertas ativas.

## 2025-05-18 — Implementação de `ml/eval/real_input_eval.py` e Execução
- Implementação da rotina de amostragem estratificada determinística (seed=42) e avaliação do `RetentionAgentPipeline`.
- Amostra gerada: 171 clientes reais cobrindo 6 personas, 4 tiers presentes, estados de risco raros, alto valor (True/False), pontos expirando, benefícios não utilizados e atritos.
- Resultados da execução: 100.0% groundedness (49/49 citações válidas), 0 violações de política (0.0%), 46.2% ACT-NO-ACTION (79/171), latência média 32.09ms (p95: 35.59ms).
- Bateria adversarial em dados reais: 10/10 casos sanitizados/bloqueados com 0 vazamentos de payload.
- Resultados machine-readable persistidos em `data/analytics/agent_eval_real.json`.

## 2025-05-18 — Novo Alvo `tasks.py agent-eval-real`
- Adicionado alvo `agent-eval-real` no arquivo `tasks.py` apontando para `ml.eval.real_input_eval`.
- Validação via CLI executada com sucesso, mantendo todos os alvos preexistentes intactos.

## 2025-05-18 — Implementação de Testes Automatizados `tests/test_agent_eval_real.py`
- Criada suíte de testes cobrindo determinismo da amostra (bitwise idêntico), cobertura de estratos, contrato do JSON de métricas, zero violações de guardrails e sanitização dos 10 casos adversariais.
- Execução com 5/5 testes novos passando e 163/163 testes da suíte completa verdes; ruff check 100% limpo.

## 2025-05-18 — Elaboração de `docs/agent_eval_report.md`
- Redigido relatório detalhado da avaliação com todos os números reais executados (171 clientes na amostra, 100% groundedness, 0 violações, 46.2% ACT-NO-ACTION justificado pela inatividade de dormentes e regras estritas do playbook).
- Detalhamento dos 10 casos adversariais em clientes reais (0 vazamentos), matrizes de persona x ação e tier x ação, latências e seção completa de limitações honestas.
