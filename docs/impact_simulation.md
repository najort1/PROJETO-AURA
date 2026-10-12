# Simulação de Impacto Financeiro, Sensibilidade e Plano de Piloto A/B — PROJETO AURA 2.0

> **Frente de Implementação WS9 (task-10, encerramento do pipeline analítico).**  
> **Artefato computacional gerado:** `data/analytics/impact_scenarios.json`  
> **Módulo executável:** `python -m ml.impact.simulate` (ou via runner: `python tasks.py impact`)  
> **Testes automatizados:** `tests/test_impact.py` (9 testes verdes, 189 testes em toda a suíte)

---

## 1. Visão Geral e População Alvo

A simulação de impacto financeiro do Projeto Aura 2.0 quantifica o retorno econômico esperado ($\Delta\text{Receita}$) decorrente da execução das recomendações proativas geradas pelo Agente de Retenção sobre a carteira de clientes.

### 1.1 Definição do Alvo da Simulação

A base analítica total compreende **50.000 clientes** (`data/analytics/customers_scores.parquet`), com Valor em Risco consolidado de **R$ 8.307.728,94** e CLV 12m projetado de **R$ 39.554.463,12**.

O motor determinístico de elegibilidade e guardrails do agente (`data/analytics/agent_recommendations.parquet`) classificou os clientes em:
1. **Silêncio Responsável (`nenhuma_acao_elegivel`):** 35.362 clientes (70,72%). Clientes sem atrito comprovado, com risco irrelevante ou sem ação com ROI justificado. Possuem **custo zero** e **estão excluídos do alvo da simulação**.
2. **Ações Proativas Elegíveis (Alvo da Simulação):** **14.638 clientes** (29,28%). Clientes que preencheram todos os critérios contratuais do programa e receberam uma intervenção personalizada do playbook de retenção.

### 1.2 Distribuição e Custo do Playbook por Ação

Os custos unitários foram extraídos de `config/actions.yaml`. Para ações cujo benefício decorre do regulamento do tier (`cost_brl = 0`), foi aplicada a premissa de custo operacional de atendimento de **R$ 45,00** registrada em `docs/limitations.md §8`.

| Ação do Playbook | ID da Ação | Clientes Elegíveis | Custo Unitário (BRL) | Custo Total (BRL) | Status da Premissa |
|---|---|:---:|:---:|:---:|---|
| `aviso_antecipado_prioridade` | `ACT-AVISO-ANTENCIPADO` | 9.758 | R$ 5,00 | R$ 48.790,00 | Custo de comunicação multicanal |
| `antecipacao_de_nivel` | `ACT-ANTECIPACAO-NIVEL` | 4.610 | R$ 25,00 | R$ 115.250,00 | Custo operacional de upgrade assistido |
| `educacao_beneficio_existente` | `ACT-EDUCA-BENEFICIO` | 139 | R$ 3,00 | R$ 417,00 | Custo digital via push/email |
| `pacote_experiencia_destino` | `ACT-PACOTE-EXPERIENCIA` | 130 | R$ 15,00 | R$ 1.950,00 | Parceria Azul Viagens |
| `reencaminhamento_atraso` | `ACT-ATRATRIBUI-ATRASO` | 1 | R$ 30,00 | R$ 30,00 | Intervenção operacional de malha |
| **Total do Playbook** | — | **14.638** | **R$ 11,37 (médio)** | **R$ 166.437,00** | **Investimento total irrestrito** |

---

## 2. Metodologia de Cálculo de $\Delta\text{Receita}$ e Cenários

### 2.1 Formulação Canônica

O impacto financeiro líquido é computado cliente a cliente de forma multiplicativa transparente:

$$\Delta\text{Receita} = \sum_{i \in \text{Alvo}} \left[ P(\text{evasão evitada} \mid \text{ação})_i \times \text{CLV\_12m}_i \times \text{margem} \right] - \sum_{i \in \text{Alvo}} \text{Custo}_i$$

Onde a probabilidade de evasão evitada é expressa por:

$$P(\text{evasão evitada} \mid \text{ação})_i = \text{churn\_prob}_i \times \text{efeito\_retenção} \times \text{resposta\_do\_canal}$$

- $\text{churn\_prob}_i$: Probabilidade individual de evasão predita pelo modelo calibrado de churn (LightGBM, Brier 0,145 — valor real em `data/analytics/metrics/churn_metrics.json`).
- $\text{CLV\_12m}_i$: Valor futuro previsto pelo modelo final de CLV (LightGBM, WAPE 0,655; o BG/NBD + Gamma-Gamma é o baseline comparativo superado — ver `docs/model_cards/clv.md`).
- $\text{efeito\_retenção}$: [PREMISSA] Redução percentual relativa no risco de evasão proporcionada pela ação.
- $\text{resposta\_do\_canal}$: [PREMISSA] Probabilidade de engajamento/abertura/adesão no canal de contato.
- $\text{margem}$: [PREMISSA] Margem líquida de contribuição da companhia aérea sobre a receita retida.

### 2.2 Tabela de Cenários e Premissas Declaradas

Todas as premissas adotadas baseiam-se em referências genéricas de mercado (*benchmarks de programas de retenção CRM*), sem invenção de parâmetros causais não observados.

| Cenário | Efeito Retenção [PREMISSA] | Resposta Canal [PREMISSA] | Margem Contribuição [PREMISSA] | Racional de Mercado |
|---|:---:|:---:|:---:|---|
| **Conservador** | 5,0% (0,05) | 12,0% (0,12) | 15,0% (0,15) | Cenário de estresse: baixa abertura em canais digitais e efeito tímido na reversão de insatisfação. |
| **Base (Recomendado)** | 10,0% (0,10) | 18,0% (0,18) | 20,0% (0,20) | Ponto central de equilíbrio da indústria de fidelidade para campanhas direcionadas. |
| **Otimista** | 15,0% (0,15) | 25,0% (0,25) | 25,0% (0,25) | Alta adesão com personalização hiper-relevante e forte elasticidade de demanda. |

---

## 3. Resultados da Simulação e Intervalos de Confiança (IC95% Bootstrap)

Para cada cenário, foram computados os valores pontuais e intervalos de confiança não paramétricos de **95% via bootstrap percentil com 1.000 reamostragens** (seed 42 fixa).

| Métrica | Conservador | Base | Otimista |
|---|:---:|:---:|:---:|
| **Clientes Alvo Elegíveis** | 14.638 | 14.638 | 14.638 |
| **Evasões Evitadas Estimadas** | 23,78 clientes | 71,33 clientes | 148,61 clientes |
| **Receita Bruta Preservada** | R$ 3.230,30 | R$ 12.921,21 | R$ 33.648,99 |
| *IC95% Receita Bruta [Bootstrap]* | *[R$ 3.121,20 ; R$ 3.342,15]* | *[R$ 12.484,79 ; R$ 13.368,61]* | *[R$ 32.512,48 ; R$ 34.814,10]* |
| **Custo Total das Ações** | R$ 166.437,00 | R$ 166.437,00 | R$ 166.437,00 |
| **$\Delta\text{Receita Líquida}$** | **R$ -163.206,70** | **R$ -153.515,79** | **R$ -132.788,01** |
| *IC95% $\Delta\text{Receita}$ [Bootstrap]* | *[R$ -165.348,13 ; R$ -160.890,50]* | *[R$ -155.674,98 ; R$ -151.200,89]* | *[R$ -134.935,50 ; R$ -130.513,91]* |
| **ROI Líquido sobre Custo** | -98,06% | -92,24% | -79,78% |

---

## 4. Análise de Break-Even e Honestidade Técnica Radical

### 4.1 Por que o $\Delta\text{Receita}$ irrestrito é negativo?

O resultado negativo na abordagem irrestrita (contatar todos os 14.638 clientes elegíveis) não é um defeito de modelo, mas uma **verdade analítica incontornável da gestão de CRM**:
1. O custo acumulado de ações do playbook varia entre R$ 5,00 e R$ 25,00 por cliente (média de R$ 11,37).
2. Uma parcela expressiva do público elegível é formada pela persona `regional_dependente` recebendo `aviso_antecipado_prioridade` (9.758 clientes) ou `antecipacao_de_nivel` (4.610 clientes).
3. Nesses segmentos, o valor monetário anual ponderado pelo risco ($\text{churn\_prob} \times \text{CLV\_12m}$) é modesto em comparação aos custos fixos de contato.
4. Quando se multiplica uma taxa de resposta realista (12% a 25%) por um lift de retenção conservador (5% a 15%) e pela margem (20%), o retorno financeiro esperado por cliente gira em torno de **R$ 0,22 a R$ 2,30**.
5. Disparar ações pagas para toda a base elegível de forma indiferenciada ("blanket campaign") inevitavelmente destrói valor econômico.

### 4.2 Custo Máximo Unitário para Ponto de Equilíbrio (Break-Even)

Para que a execução sobre os 14.638 clientes atingisse ponto de equilíbrio ($\Delta\text{Receita} = 0$), o custo unitário máximo admissível por ação seria:
- **Cenário Conservador:** Máximo de **R$ 0,22** por ação.
- **Cenário Base:** Máximo de **R$ 0,88** por ação.
- **Cenário Otimista:** Máximo de **R$ 2,30** por ação.

*Conclusão Operacional:* Custos unitários dessa ordem só são viáveis em canais puramente digitais automatizados e de custo marginal zero, tais como notificações push no aplicativo móvel ou e-mails transacionais parametrizados.

### 4.3 Eficácia Conjunta Necessária no Cenário Atual

Mantendo-se o custo atual de R$ 166.437,00 e a margem base de 20%, o produto multiplicativo necessário $(\text{efeito\_retenção} \times \text{resposta\_do\_canal})$ para break-even na carteira total seria de **23,19%**.  
Isso exigiria, por exemplo, uma taxa de resposta de 50% combinada a uma eficácia de retenção de 46,38% — patamares irrealistas para o setor aéreo sem subsídio promocional massivo.

---

## 5. Alocação sob Orçamento Restrito (R$ 80.000)

Em ambientes corporativos reais, campanhas operam sob teto orçamentário. O Projeto Aura avalia a eficiência de corte sob o orçamento de referência de **R$ 80.000,00** (premissa central explorada na Tela 06 do painel executivo).

### 5.1 Estratégia de Priorização por Valor em Risco (Recomendada)

Ordenando os 14.638 clientes elegíveis por `valor_em_risco` decrescente até esgotar os R$ 80.000,00:

| Métrica da Campanha | Valor Real Calculado | Impacto Estratégico |
|---|:---:|---|
| **Clientes Cobertos** | **6.170 clientes** | 42,15% da base elegível de 14.638 clientes |
| **Investimento Efetivo** | **R$ 79.995,00** | 99,99% de utilização do orçamento |
| **Valor em Risco Capturado** | **R$ 2.117.680,43** | **59,00% de todo o VaR do público elegível** |
| $\Delta\text{Receita}$ Cenário Base | R$ -72.371,35 | Receita Bruta salva: R$ 7.623,65 |
| $\Delta\text{Receita}$ Cenário Otimista | R$ -60.141,75 | Receita Bruta salva: R$ 19.853,25 |

*Insight de Concentração:* Com apenas 42,15% dos clientes, o algoritmo captura **59,00% do risco financeiro total**, comprovando a eficácia da priorização orientada a dados sobre seleções aleatórias.

### 5.2 Comparativo com a Heurística da Tela 06 (Custo Médio R$ 45)

A Tela 06 do aplicativo Streamlit disponibiliza um simulador dinâmico parametrizável cujo valor padrão adota custo médio de R$ 45,00/ação:
- Sob R$ 80.000 e R$ 45,00/ação: **1.777 clientes alcançados** (12,14% do alvo).
- Investimento: R$ 79.965,00.
- A granularidade do inventário real (`actions.yaml`), com ações de R$ 5 e R$ 25, permite atender **3,47 vezes mais clientes** (6.170 vs 1.777) sob o mesmo teto financeiro.

---

## 6. Análise de Sensibilidade Unidimensional (Tornado)

Para mensurar o impacto relativo de incertezas nas premissas sobre o $\Delta\text{Receita}$ líquido, realizou-se uma variação isolada (*one-at-a-time*) de $\pm 20\%$ ao redor do ponto de calibração Base ($\Delta\text{Receita} = \text{R\$} -153.515,79$).

### 6.1 Ranking Tornado Padronizado ($\pm 20\%$)

| Posição | Parâmetro Analisado | Faixa Avaliada [-20% ; +20%] | $\Delta\text{Receita}$ Mínimo | $\Delta\text{Receita}$ Máximo | Amplitude (Swing BRL) | Elasticidade ($E$) |
|:---:|---|:---:|:---:|:---:|:---:|:---:|
| **1º** | **`custo_acao`** | [0,80x ; 1,20x] | R$ -186.803,19 | R$ -120.228,39 | **R$ 66.574,80** | **-1,0842** |
| **2º** | **`efeito_retencao`** | [8,0% ; 12,0%] | R$ -156.100,03 | R$ -150.931,54 | **R$ 5.168,49** | **+0,0842** |
| **3º** | **`resposta_canal`** | [14,4% ; 21,6%] | R$ -156.100,03 | R$ -150.931,54 | **R$ 5.168,49** | **+0,0842** |
| **4º** | **`margem`** | [16,0% ; 24,0%] | R$ -156.100,03 | R$ -150.931,54 | **R$ 5.168,49** | **+0,0842** |

### 6.2 Tornado nas Faixas Globais dos Cenários

Avaliando a oscilação entre os limites do cenário Conservador e Otimista:

```
PARÂMETRO               FAIXA             AMPLITUDE DO IMPACTO FINANCEIRO (SWING BRL)
--------------------------------------------------------------------------------------
custo_acao              [0.80x - 1.20x]   ████████████████████████████████  R$ 66.574,80
efeito_retencao         [5.0% - 15.0%]    ██████                            R$ 12.921,21
resposta_canal          [12.0% - 25.0%]   ████                              R$  9.331,98
margem                  [15.0% - 25.0%]   ███                               R$  6.460,60
```

### 6.3 Diagnóstico dos Fatores Críticos

1. **O custo operacional da ação é a variável hegemônica:** Uma redução de 20% nos custos das ações gera uma economia líquida de R$ 33.287,40 — valor mais de 6 vezes superior a qualquer melhoria equivalente na taxa de resposta ou no lift de retenção.
2. **Simetria nos fatores de receita:** Devido à estrutura multiplicativa linear da receita ($\text{Efeito} \times \text{Resposta} \times \text{Margem} \times \text{VaR}$), a elasticidade percentual pontual dos três direcionadores de receita é rigorosamente idêntica (+0,0842).

---

## 7. Plano de Piloto A/B Estatístico

Para transformar as premissas em evidências causais calibradas, é indispensável executar um experimento A/B com grupo de controle puro antes de qualquer escala comercial.

### 7.1 Métrica Primária e Grupo Alvo

- **Métrica Primária:** Taxa de retenção em 12 meses pós-intervenção ($p_{\text{retencao}} = 1 - p_{\text{churn}}$).
- **Público Elegível:** Clientes classificados como **Alto Valor em Risco** (`alto_valor == True` E `churn_prob` acima da mediana).
- **Métricas Reais da Base Carregada:**
  - Total de clientes de Alto Valor: **5.005 clientes** (10,01% da base total).
  - Mediana de `churn_prob` entre Alto Valor: **0,0941** (9,41%).
  - Total de Alto Valor em Risco na amostra sintética: **2.500 clientes**.
  - **Baseline Real de Evasão ($p_1$):** **14,62%** (`churn_prob` médio de 0,146245).
  - **Baseline Real de Retenção ($1 - p_1$):** **85,38%** (0,853755).

### 7.2 Dimensionamento Amostral (Fórmula de Fleiss Two-Sample)

O cálculo do tamanho amostral por braço adota o teste bilateral de proporções com variância combinada sob $H_0$ e separada sob $H_1$:

$$n = \frac{\left( Z_{\alpha/2} \sqrt{2 \bar{p} (1 - \bar{p})} + Z_{\beta} \sqrt{p_1 (1 - p_1) + p_2 (1 - p_2)} \right)^2}{\delta^2}$$

Com $\alpha = 0,05$ bilateral ($Z_{\alpha/2} = 1,95996$) e poder estatístico $1 - \beta = 0,80$ ($Z_{\beta} = 0,84162$).

#### Caso Analítico Fechado (Verificação de Literatura)
Para um caso de calibração clássico com baseline $p_1 = 50\%$ e $\text{MDE} = 5\text{pp}$ ($p_2 = 55\%$):
$$n = \frac{\left( 1,95996 \sqrt{2 \times 0,525 \times 0,475} + 0,84162 \sqrt{0,25 + 0,2475} \right)^2}{0,05^2} = 1.564,67 \approx 1.565 \text{ clientes/braço}$$
O módulo computacional reproduz exatamente esse valor (`tests/test_impact.py`), validando a precisão da fórmula.

### 7.3 Tabela de Dimensionamento por MDE no Baseline Real (85,38%)

| MDE Testado | Taxa Alvo ($p_2$) | $n$ por Braço | Tamanho Total ($2n$) | Cabe no Risco Local (2.500)? | Cabe no Alto Valor Local (5.005)? |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **+1,0 pp** | 86,38% | 19.040 | 38.080 | Não | Não |
| **+2,0 pp (Primário)** | **87,38%** | **4.618** | **9.236** | **Não** | **Não** |
| **+3,0 pp** | 88,38% | 1.988 | 3.976 | Não | **Sim (1 piloto)** |
| **+4,0 pp** | 89,38% | 1.082 | 2.164 | **Sim (1 piloto)** | **Sim (2 pilotos)** |
| **+5,0 pp** | 90,38% | 668 | 1.336 | **Sim (1 piloto)** | **Sim (3 pilotos)** |

### 7.4 Análise Honesta de Capacidade e Escala

1. **Amostra Sintética Local (50.000 clientes):**
   - O contingente local de Alto Valor em Risco é de apenas **2.500 clientes**.
   - Para um MDE realista de **+2pp**, seriam necessários **9.236 clientes**, inviabilizando o teste nessa amostra local sem extrapolar para outros níveis de risco.
   - Na amostra local, o efeito mínimo detectável com 80% de poder é de **+4pp** ($n=1.082$/braço, total 2.164).
2. **Escala Corporativa Real (Azul Fidelidade — 20,1M de membros):**
   - Conforme dados oficiais de RI (dez/2025), o programa conta com 20,1M de membros cadastrados e cerca de 1,4M de usuários ativos mensais (MAU).
   - O estrato de Alto Valor projetado em escala real ultrapassa **140.000 clientes**, dos quais mais de **70.000** encontram-se em situação de risco de evasão.
   - Em produção, há folga estatística suficiente para executar **mais de 7 pilotos simultâneos com MDE de +2pp**, ou rodar experimentos com sensibilidade de +1pp com total rigor.

### 7.5 Janela Temporal e Métricas Proxy Intermediárias

- **Janela Definitiva (12 Meses):** Indispensável para auditoria do ciclo de requalificação anual e constatação do churn econômico formal.
- **Janela Proxy Intermediária (90 Dias):** Para governança ágil e controle de danos, adota-se um checkpoint aos 90 dias medindo métricas antecedentes com alta correlação com retenção:
  1. Reativação de transações ou emissão de passagens no trimestre.
  2. Abertura e clique no canal de contato (taxa de contato útil).
  3. Resgate de pontos ou ativação de benefício do tier.

### 7.6 Salvaguardas de IA Responsável

O piloto deve respeitar integralmente as diretrizes de governança ética e conformidade legal:
1. **Humano no Circuito (*Human-in-the-Loop*):** Todas as intervenções geradas pelo agente são submetidas a workflow de aprovação humana no painel de CRM (já demonstrado na Tela 04 do app).
2. **Direito de Opt-Out:** Clientes podem cancelar comunicações proativas a qualquer momento, em estrito cumprimento da LGPD.
3. **Auditoria Contínua de Viés:** A cada ciclo de retreino ou atualização de batches, executa-se obrigatoriamente a verificação de conformidade da regra dos Quatro Quintos via `python tasks.py fairness` (`ml/fairness/audit.py`), impedindo disparidades demográficas por idade, gênero ou região geográfica.

### 7.7 Plano de Transição para Nuvem (Swap Snowflake)

Conforme arquitetado em `docs/snowflake_plan.md` e nos scripts DDL/Carga em `sql/snowflake/`:
1. Os dados do piloto serão ingeridos diretamente no ambiente corporativo Snowflake (`AURA_ANALYTICS.AGENT_RECOMMENDATIONS`).
2. O contrato de dados é rigorosamente mantido (`schemas/recommendations.yaml`), permitindo alternar a fonte de dados do DuckDB local para o Snowflake Data Cloud sem alteração de lógica analítica.

---

## 8. Estimativa de Custos Operacionais do Agente

O Projeto Aura 2.0 foi desenhado para maximizar a auditabilidade regulatória e a previsibilidade financeira na inferência.

### 8.1 Modo Offline (Modo Oficial Avaliado)

- **Tecnologia:** Motor de regras determinísticas, verificação de elegibilidade em árvore de decisão e busca vetorial RAG sobre regras do programa.
- **Custo por Recomendação:** **R$ 0,00**.
- **Custo Total para 50.000 clientes:** **R$ 0,00**.
- **Vantagens:** Reprodutibilidade estrita, ausência de latência de rede, zero custo de API externa, conformidade regulatória auditável e ausência de alucinações.

### 8.2 Modo LLM (Estimativa Prospectiva em Nuvem)

Caso a organização opte por utilizar redação generativa via modelos de linguagem em nuvem:
- **Premissa de Tokens por Cliente:** 600 a 900 tokens (combinando prompt de contexto, histórico de transações e mensagem gerada).
- **Volume Total (50.000 clientes):** 30.000.000 a 45.000.000 tokens.
- **Premissa de Câmbio:** USD 1,00 = BRL 5,50.

| Tier de Modelo LLM | Modelos Típicos de Mercado | Preço por Milhão de Tokens (USD) | Custo Total Estimado (USD) | Custo Total Estimado (BRL) | Custo por Cliente (BRL) |
|---|---|:---:|:---:|:---:|:---:|
| **Econômico / Destilado** | GPT-4o-mini, DeepSeek V3 | $0,40 / 1M | $12,00 a $18,00 | **R$ 66,00 a R$ 99,00** | ~R$ 0,002 |
| **Intermediário / Rápido** | Claude 3.5 Haiku, Gemini Flash | $1,50 / 1M | $45,00 a $67,50 | **R$ 247,50 a R$ 371,25** | ~R$ 0,007 |
| **Fronteira Completo** | GPT-4o, Claude 3.5 Sonnet | $5,00 / 1M | $150,00 a $225,00 | **R$ 825,00 a R$ 1.237,50** | ~R$ 0,025 |

*Nota de Transparência:* Nesta sessão do PROJETO AURA 2.0, o modo avaliado empiricamente e validado por testes é o **modo offline determinístico**. As cifras de LLM constituem projeção paramétrica documentada.

---

## 9. Limitações e Honestidade Científica

Em conformidade com a política viva de limitações do projeto (`docs/limitations.md`), destacam-se as seguintes restrições:

1. **Efeito Não Causal:** O efeito de retenção adotado (5%, 10%, 15%) é uma **PREMISSA declarada**, não uma relação de causalidade observada empiricamente na carteira. O verdadeiro uplift só pode ser estabelecido por meio do piloto A/B com grupo de controle.
2. **Base Sintética Calibrada:** Embora gerada a partir de microdados ANAC e fatos públicos do programa Azul Fidelidade, a base é sintética. Os resultados comprovam a solidez metodológica e a coerência do pipeline de ponta a ponta, mas não constituem promessa contratual de retorno corporativo.
3. **Ausência de Modelagem de Uplift Individual (Uplift Modeling):** O MVP prioriza por risco absoluto (`valor_em_risco`), e não pela propensão incremental ao tratamento ("uplift"). O desenvolvimento de modelos de uplift de duas árvores (T-Learner/X-Learner) é registrado como evolução futura.
