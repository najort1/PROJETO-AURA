# Limitações e premissas — registro vivo

> **Documento de honestidade do projeto** (mantido pelo orquestrador).
> Registra TUDO que impede interpretação dos números como desempenho real.
> Regra: se uma limitação não está aqui, ela não foi honestamente declarada —
> este arquivo cresce a cada onda de integração.

## 1. Dados sintéticos (global)

- **Nenhum dado pessoal real** é usado em nenhuma camada. Toda a base de clientes é
  gerada por código com processo latente (arquétipos + ruído).
- Consequência direta: **todas as métricas de modelo (WAPE, AUC, F1, ARI, IC) validam
  o PIPELINE e sua metodologia — não provam desempenho no mundo real.**
- Ground truth latente é segregado em `data/curated/ground_truth.parquet`
  (consumo exclusivo de avaliação).

## 2. Fontes públicas e bloqueios (verificação em 12/10/2026)

| Fonte | Situação | Impacto | Mitigação |
|---|---|---|---|
| Microdados ANAC (voos/movimentação/aeródromos) | ✅ local (3,2 GB, 2000→2026-08) | — | Manifesto com sha256 (`docs/calibration_report.md`) |
| Microdados de tarifas ANAC | ❌ download bloqueado (CAPTCHA no portal) | Distribuição de tarifa do sintético é PREMISSA | `config/generator.yaml` pricing (premissa rotulada); reavaliar quando a fonte abrir |
| Página/regulamento Azul Fidelidade | ❌ captura automática bloqueada (HTTP 403 Akamai) | Regras do programa compiladas por pesquisa, snapshot PROVISIONAL | `config/program_rules.yaml` com status por fato + protocolo de substituição por captura manual; fail-safe para fatos não confirmados |
| Azul RI / SEC (escala do programa) | ✅ verificado por pesquisa (20,1M membros dez/2025; ~1,4M ativos/mês) | — | Registrado em `scale_facts` |
| Avaliações públicas (Reclame Aqui/lojas de app) | ❌ coleta bloqueada por termos de uso/automação | Corpus de sentimento é SINTÉTICO ROTULADO | Fronteira WS6: valida pipeline de NLP, **não mede satisfação real**; kappa humano substituído por concordância entre abordagens vs rótulo gerador (desvio declarado) |
| Taxa de cancelamento por rota | ⚠️ a confirmar pela frente WS1 (voos_basica pode conter só etapas voadas) | Atrito de cancelamento pode não ser calibrável | WS1 documenta; se indisponível, vira premissa rotulada |
| Cobertura da movimentação (atrasos por aeroporto) | ⚠️ janela 2019-03→2025-12 (2026 ausente na fonte) | Taxa de atraso de 2026 extrapola da janela observada | Declaração de cobertura no `docs/calibration_report.md` |

## 3. Agente e LLM

- **Sem credencial de LLM nesta sessão**: o agente opera no modo OFFLINE
  (compositor determinístico) — que é o modo de demonstração real e testado.
  O provedor LLM (OpenAI-compatible) é pluggável e documentado, mas sua qualidade
  de redação não foi avaliada empiricamente nesta sessão (avaliação arquitetural).
- Recomendações do modo offline são 100% rastreáveis (elegibilidade determinística +
  citações versionadas) — vantagem de auditabilidade; a redação LLM é opcional.
- Regras do programa não confirmadas para 2026 (ex.: earn/validade/teto do
  Diamante Unique) → **inelegível por fail-safe** + revisão humana.

## 4. Impacto (WS9)

- Efeito das ações de retenção (lift de retenção) e margem de contribuição são
  **PREMISSAS** com benchmarks citados — não efeitos causais medidos.
- O plano de piloto A/B existe exatamente porque o uplift real só é observável
  com controle + dados reais.

## 5. Escala e amostragem

- 50.000 clientes sintéticos (amostra para caber em laptop) vs 20,1M membros
  reais (RI dez/2025): distribuições foram calibradas, mas estatísticas de cauda
  podem diferir em escala real. O pipeline escala por código (parquet/duckdb).

## 6. Escopo deliberadamente fora (Camada 2)

- **Uplift modeling** (priorizar quem RESPONDE à ação) fica fora do MVP
  (plano mestre: "só se houver folga") — registrado como trabalho futuro.

## 7. Pendências de integração (atualizado a cada onda pelo Lead)

- [x] Números reais das frentes WS1–WS9 preenchidos após execução e revisão.
- [x] Achados das revisões independentes incorporados (12 revisões, vereditos em docs/reviews/).

## 7b. Determinismo de regeneração completa (achado do gate final, 12/10/2026)

- **Dados sintéticos e ingestão:** 100% bitwise determinísticos (verificado em 4
  regenerações: customers 8be2bc41…, flights fc876ced…, transactions 38afb58e…,
  loyalty 821e6efa…, interactions d8b49c62…, ground_truth dc8de99b…).
- **Achado 1 — ordem de linhas:** a primeira regeneração FULL (`tasks.py all` do zero)
  revelou que o parquet de features saía com ORDEM DE LINHAS variável (COPY paralela
  do DuckDB sem `ORDER BY`). Como o treino LightGBM amostra por índice de linha,
  isso deslocava clientes de fronteira entre regenerações.
- **Achado 2 — conteúdo não determinístico:** comparando duas execuções seguidas,
  `rota_favorita` variava para 2.171 clientes (empates de `ROW_NUMBER()` sem
  desempate total) e `ticket_medio_12m` variava ±R$ 0,01 (soma paralela de
  `amount_brl` em float sujeita à ordem de agregação — ULP).
- **Correções aplicadas (Lead):**
  1. `ORDER BY customer_id` nos post-hooks dos dois marts dbt de features
     (`dbt/models/marts/features_customer*.sql`) — ordem estável;
  2. Desempate total na rota: `ORDER BY COUNT(*) DESC, rota ASC`
     (`dbt/macros/generate_features.sql`);
  3. Somas monetárias em `DECIMAL(18,2)` (soma exata, imune à ordem):
     `monetary_12m` e `target_clv_12m`;
  4. Testes de impacto deixaram de hard-codar contagens absolutas e passaram a
     validar invariantes + faixas + cross-checks derivados dos artefatos
     (`tests/test_impact.py`). Os modelos LightGBM já usavam `deterministic=True`
     + `force_col_wise=True`.
- **Verificação pós-correção:** `features` executado 2× → conteúdo 100% idêntico
  (numérico, texto e ordem); treino e score verificados estáveis entre execuções
  consecutivas (ver abaixo).
- **Achado 3 — crash silencioso por tipo Decimal (auto-infligido pelo Lead):** a
  primeira versão da correção 3 (acima) publicava `monetary_12m`/`target_clv_12m`
  como tipo **DECIMAL** no parquet. O `StandardScaler` do
  `ml/segmentation/cluster.py` então falhava com
  `TypeError: float - Decimal`, derrubando o passo `ml.segmentation.train` —
  que é o PRIMEIRO passo do alvo `tasks.py score`. Como o runner pwsh não
  propaga falhas intermediárias e os logs estavam redirecionados, **todo
  `tasks.py score` falhava silenciosamente e `customers_scores` ficou
  obsoleto (stale)**, divergindo de `churn_predictions` em 24.777 clientes
  (até 0,108 de churn_prob). Detectado por verificação de consistência
  (`customers_scores.churn_prob == round(churn_prob_model, 4)`), que se tornou
  teste de integração permanente.
  - **Correção definitiva:** a SOMA continua em `DECIMAL(18,2)` (exata,
    determinística) e a PUBLICAÇÃO converte para `::DOUBLE` (float64) —
    `dbt/macros/generate_features.sql`. Dtypes verificados float64 e conteúdo
    determinístico em 2 execuções seguidas.
  - **Nota de retratação:** numa primeira análise o Lead atribuiu a
    inconsistência a uma hipótese de corrida entre dois treinos concorrentes;
    o crash silencioso por tipo Decimal era a causa real. A regra operacional
    de nunca rodar dois alvos do `tasks.py` simultaneamente permanece válida
    (o runner não tem trava de arquivo), mas nenhum dado foi corrompido por
    concorrência — o arquivo stale era íntegro, apenas defasado.
- **Consistência final exigida (teste permanente):**
  `customers_scores.churn_prob == round(churn_prob_model, 4)` e
  `valor_em_risco == round(clv × churn, 2)` para os 50.000 clientes
  (`tests/test_integration.py`).

## 8. Registro de onda — integração 12/10/2026 (pós FASE B + correções)

Itens adicionados nesta onda, com evidência no código/repos:

- **Base sintética v3 (pós-correções WS2):** a qualificação em janela móvel agora impede
  pontos de transações futuras (teto temporal `<= eval_dt`); eventos de downgrade têm
  `event_type="tier_downgrade"`/`trigger_reason="qualification_cycle_expired"` (6.091
  eventos); replay de eventos reconstrói exatamente o `current_tier` de customers.parquet
  (0 divergências em 50k). Números de fidelidade: MAU 10,52%; Pareto top-20% 74,40%;
  tiers 95,61%/0,15%; sazonalidade r=0,8744 (todas dentro das tolerâncias).
- **Semestre parcial 2026-S2 no mapa de atritos:** a janela sintética termina em
  2026-08; o semestre 2026-S2 é PARCIAL (jul-ago) e está explícito no mapa (49 linhas).
  72 avaliações dessa cauda eram rotuladas silenciosamente como 2026-S1 — corrigido
  com fail-loud; pesos recalculados (app_checkin 0,1451→0,1411 foi o maior desvio).
- **Atraso por aeroporto:** `nr_aeroporto_referencia` 100% nulo na base movimentação →
  taxas de atraso são NACIONAIS (16,75% média >15 min), não por aeroporto; declarado no
  relatório de calibração.
- **Cancelamento:** formalmente `not_computable_local` (bases locais só têm etapas
  voadas e calços executados). A nota de limitação agora registra dinamicamente:
  2.471 registros de perna duplicada `cd_di='D'` no triênio (914 apenas em 2024), todos
  com decolagem nula e 0 passageiros.
- **Aeroportos comerciais:** 222 com QUALQUER tráfego comercial (inclui charters/táxi
  aéreo); 188 com tráfego estritamente regular (`cd_tipo_linha='N'`, `cd_di in ('0','4')`) —
  ambos os números agora computados e rotulados no relatório.
- **Fairness (fixtures da WS8a):** 4 de 11 grupos demográficos estão ABAIXO do limiar
  four-fifths (0,80) na seleção de alto valor — ex.: faixa 18-29 ≈ 0,41; Norte 0,56;
  Nordeste 0,61; Sul 0,61. O painel da tela 07 existe para DETECTAR e sinalizar essa
  disparidade; o roteiro de demo foi corrigido para nunca afirmar conformidade total.
  Nenhum atributo sensível entra nas features (LGPD); a disparidade emerge de
  correlações socioeconômicas dos dados sintéticos e exige plano de mitigação antes de
  qualquer piloto. A auditoria definitiva com números reais da base v3 é a frente WS5.
- **`custo_medio_acao = R$ 45`** (tela 01/simulador): PREMISSA de negócio (média ponderada
  do playbook), não valor observado — rotulada no código e aqui.
- **LLM não simulado:** sem credencial, o modo offline determinístico é o modo real
  avaliado; nenhum número de qualidade de redação LLM é reivindicado.
- **Corpus de sentimento:** ~16 famílias de templates por aspecto — F1 de presença
  próximo de 1,0 é quase-trivial por construção (valida mecânica do pipeline, não
  habilidade de NLP em linguagem espontânea); nota de honestidade no relatório WS6.
