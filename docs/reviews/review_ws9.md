# Relatório de Revisão Independente — WS9 (Simulação de Impacto + Piloto A/B)

> **ADENDO DO ORQUESTRADOR (12/10/2026, pós-gate final):** este veredito histórico
> permanece íntegro e IMUTÁVEL — o revisor verificou os artefatos então vigentes
> (14.638 alvos; custo R$ 166.437,00; Δ base −R$ 153.515,79; cobertura 6.170).
> No gate de reprodução do zero, o Lead detectou e corrigiu não-determinismos
> raiz (ordem de linhas DuckDB; empates de rota; soma float em `ticket_medio`;
> ver `docs/limitations.md §7b`) e regenerou a cadeia canônica. Os números
> FINAIS publicados em `docs/impact_simulation.md` podem diferir dos citados
> aqui em ±4 clientes de fronteira (contagens) e 4ª casa decimal (pontos/ICs).
> A metodologia auditada e aprovada não mudou.

> **Projeto Aura 2.0** — Pipeline de Inteligência e Retenção do Azul Fidelidade  
> **Frente Auditada:** Workstream 9 (WS9 · Simulação de Impacto Financeiro, Análise de Sensibilidade e Dimensionamento de Piloto A/B)  
> **Revisor:** Revisor Independente Adversarial (`mega-brain`)  
> **Data da Auditoria:** 12 de Outubro de 2026  
> **Protocolo:** Revisão estrita independente sem edição de código / sem git  

---

## 1. Resumo Executivo e Veredito

| Item | Status |
|---|---|
| **Veredito da Frente** | **APROVADO** |
| **Bloqueio de Promoção** | **NÃO** (Sem impeditivos críticos ou importantes) |
| **Total de Achados** | **2** (0 Crítico, 0 Importante, 1 Menor, 1 Observação) |

### Síntese da Auditoria

A frente WS9 implementou a modelagem analítica de impacto financeiro, sensibilidade e desenho experimental do Projeto Aura 2.0 com rigor matemático, integridade computacional e transparência ética exemplar:
1. **Fórmula Canônica e Recálculo Independente (R1):** A fórmula multiplicativa de $\Delta\text{Receita} = \sum [\text{churn\_prob} \times \text{efeito} \times \text{resposta} \times \text{CLV} \times \text{margem}] - \text{custo}$ foi confirmada em código (`ml/impact/simulate.py:111-118`). O recálculo independente via pandas (sem importar o módulo da aplicação) sobre os 14.638 clientes proativos produziu exatamente **R$ -153.515,79**, coincidindo ao centavo com o ponto reportado ($\Delta = \text{R\$} 0,00$) e situando-se estritamente dentro do IC95% bootstrap `[-R$ 155.674,98 ; -R$ 151.200,89]`.
2. **Auditoria de Custos das Ações (R2):** O custo total de **R$ 166.437,00** foi recomputado a partir do inventário real em `config/actions.yaml`. As ações `educacao_beneficio_existente` (R$ 3), `pacote_experiencia_destino` (R$ 15) e `reencaminhamento_atraso` (R$ 30) possuem custos próprios declarados no YAML, não necessitando do fallback operacional de R$ 45. O fallback R$ 45 está ativo apenas para ações contratuais com custo zero (`oferta_resgate_especial`), que tiveram demanda zero no lote.
3. **Bootstrap e Sensibilidade Tornado (R3):** O módulo computacional (`python tasks.py impact`) executou em 3,6s com determinismo sob seed 42. O artefato `data/analytics/impact_scenarios.json` foi gerado com os 3 cenários e ICs não paramétricos que contêm a estimativa pontual com largura realista (~$\pm \text{R\$} 2.200$). O diagrama de tornado comprovou a hegemonia do custo operacional das ações (elasticidade de $-1,0842$ vs $+0,0842$ dos direcionadores de receita).
4. **Dimensionamento do Piloto A/B (R4):** O baseline de retenção de **85,38%** foi recalculado sobre os 2.500 clientes de Alto Valor em Risco (mediana de churn de 0,0941). A aplicação da fórmula clássica de Fleiss para teste bicaudal ($\alpha=0,05$, poder $80\%$, MDE $+2\text{pp}$) resultou exatamente em **$n = 4.618$ clientes por braço** ($n_{\text{contínuo}} = 4.617,20$). No caso fechado analítico de literatura ($p_1=0,50$, $\text{MDE}=+5\text{pp}$), o recálculo confirmou exatamente **$n = 1.565$ clientes por braço**.
5. **Honestidade Intelectual e Governança (R5):** O relatório `docs/impact_simulation.md` declara categoricamente todas as premissas adotadas, não suaviza o resultado deficitário da abordagem massificada (demonstrando que campanhas *blanket* destroem valor e justificando a priorização por VaR e automação digital), registra formalmente as limitações de causalidade e sintetismo, e apresenta paridade quase absoluta com o JSON analítico.

---

## 2. Checklist de Verificações Obrigatórias (R1 a R5)

| Requisito | Descrição | Método de Auditoria Independente | Resultado Obtido | Status |
|---|---|---|---|:---:|
| **R1 · Fórmula** | Confirmar formulação matemática de $\Delta\text{Receita}$ e recalcular cenário BASE via pandas | Inspeção de `ml/impact/simulate.py` + script autônomo em `%TEMP%` cruzando `agent_recommendations` e `customers_scores` | $\Delta\text{Receita} = -\text{R\$} 153.515,79$ (diferença $\text{R\$} 0,00$ vs reportado). Dentro do IC95% `[-155.674,98 ; -151.200,89]`. | **CONFORME** |
| **R2 · Custos** | Recomputação do custo total de R$ 166.437,00 cruzando com `config/actions.yaml` | Leitura independente do YAML e produto matricial das 5 ações atribuídas aos 14.638 clientes | $9.758 \times 5 + 4.610 \times 25 + 139 \times 3 + 130 \times 15 + 1 \times 30 = \text{R\$} 166.437,00$. Ações possuem custo próprio. | **CONFORME** |
| **R3 · Bootstrap** | Execução de `tasks.py impact`, validação de ICs e sensibilidade tornado | Execução em subprocesso, leitura de `impact_scenarios.json`, verificação de monotonicidade e ranking tornado | 3 cenários gerados; ICs contêm estimativas pontuais; custo dominante ($E = -1,08$ vs $+0,08$). | **CONFORME** |
| **R4 · Piloto** | Baseline de retenção (85,38%), mediana (0,0941), N=2.500 e $n$ de Fleiss ($n=4.618$ e $n=1.565$) | Recálculo vetorial da mediana, filtragem de Alto Valor em Risco e cálculo analítico de Fleiss | Mediana = 0,094100; N = 2.500; baseline = 85,3755%; $n_{\text{piloto}} = 4.618$/braço; $n_{\text{fechado}} = 1.565$/braço. | **CONFORME** |
| **R5 · Governança** | Premissas rotuladas, déficit transparente, limitações formais e paridade doc↔JSON | Leitura linha a linha de `docs/impact_simulation.md` e diff estruturado contra `impact_scenarios.json` | Premissas marcadas `[PREMISSA]`; honestidade radical no déficit mantida; limitações presentes; paridade confirmada. | **CONFORME** |

---

## 3. R1 · Auditoria da Fórmula e Recálculo Independente do Cenário Base

### 3.1 Inspeção da Formulação Matemática em Código

No arquivo `ml/impact/simulate.py` (linhas 106–120), a função `compute_simulation_vectors` implementa a álgebra financeira cliente a cliente:

```python
# P(evasão evitada | ação) = churn_prob × efeito_retenção × resposta_do_canal
p_evitada = churn_prob * float(efeito_retencao) * float(resposta_canal)

# Receita Bruta Salva = P(evasão evitada) × CLV_12m × margem
rec_bruta = p_evitada * clv * float(margem)

# Delta Receita Líquida = Receita Bruta Salva - Custo da Ação
delta_rec = rec_bruta - cost
```

A agregação sobre toda a população elegível assume a forma canônica:
$$\Delta\text{Receita} = \sum_{i \in \text{Alvo}} \left[ \text{churn\_prob}_i \times \text{efeito\_retenção} \times \text{resposta\_canal} \times \text{clv\_12m\_previsto}_i \times \text{margem} \right] - \sum_{i \in \text{Alvo}} \text{custo}_i$$

A formulação foi considerada **estritamente correta**:
- A probabilidade de retenção incremental é multiplicativa e condicionada à resposta do canal de comunicação.
- A receita salva é calculada sobre o valor futuro previsto do cliente nos próximos 12 meses (`clv_12m_previsto`), aplicando a margem de contribuição operacional.
- O custo operacional da ação é deduzido linearmente para gerar o resultado líquido em moeda corrente (BRL).

### 3.2 Filtragem do Público Elegível e Exclusão de Silêncio Responsável

Em `agent_recommendations.parquet` (50.000 recomendações geradas pelo motor WS7), foram identificados:
- **35.362 clientes** com ação `nenhuma_acao_elegivel` (`action_id: ACT-NO-ACTION`). Representam o "Silêncio Responsável", onde o agente opta por não intervir para não gerar atrito ou custo inútil. Possuem custo zero e estão formalmente excluídos da simulação.
- **14.638 clientes** com ações proativas elegíveis do playbook. Este contingente compõe o alvo integral da simulação de impacto financeiro.

### 3.3 Recálculo Independente por Script Autônomo (sem importar o módulo)

Um script Python autônomo foi executado em ambiente temporário (`%TEMP%\audit_ws9.py`) para reproduzir o cenário BASE de ponta a ponta utilizando exclusivamente a biblioteca `pandas` e `numpy`, sem importar nenhuma classe ou função de `ml.impact.simulate`:

- **Premissas Centrais:**
  - Efeito de retenção: $10\%$ ($0,10$)
  - Resposta do canal: $18\%$ ($0,18$)
  - Margem de contribuição: $20\%$ ($0,20$)
  - Custo das ações: extraído de `config/actions.yaml`

- **Resultados Independentes Recalculados:**
  - **Evasões Evitadas Estimadas:** $\sum (\text{churn\_prob} \times 0,10 \times 0,18) = \mathbf{71,3342}$ clientes.
  - **Receita Bruta Salva:** $\sum (\text{churn\_prob} \times 0,10 \times 0,18 \times \text{clv\_12m\_previsto} \times 0,20) = \mathbf{R\$\ 12.921,21}$ (12.921,2140 BRL).
  - **Custo Total das Ações:** $\mathbf{R\$\ 166.437,00}$.
  - **$\Delta\text{Receita Líquida}$:** $\text{R\$} 12.921,2140 - \text{R\$} 166.437,00 = \mathbf{R\$\ -153.515,79}$ (-153.515,7860 BRL).

- **Confronto com os Valores Reportados:**
  - Estimativa pontual reportada: **R$ -153.515,79**.
  - Erro absoluto do recálculo: **R$ 0,00** (tolerância $\pm \text{R\$} 1,00$ plenamente satisfeita).
  - Intervalo de confiança reportado (IC95% bootstrap): **[-R$ 155.674,98 ; -R$ 151.200,89]**.
  - O ponto recalculado está rigorosamente contido no intervalo de confiança.

---

## 4. R2 · Auditoria de Custos por Ação e Custo Total

### 4.1 Inventário de Custos em `config/actions.yaml`

A auditoria inspecionou as 10 ações cadastradas no arquivo `config/actions.yaml` e cruzou com as 5 ações que efetivamente receberam atribuição pelo motor determinístico de elegibilidade em `agent_recommendations.parquet`:

| Ação no Playbook | ID da Ação | Clientes Alvo | Custo Unitário no YAML (`cost_brl`) | Status do Fallback R$ 45 | Subtotal Recalculado (BRL) |
|---|---|:---:|:---:|:---:|---:|
| `aviso_antecipado_prioridade` | `ACT-AVISO-ANTENCIPADO` | 9.758 | R$ 5,00 | Não aplicável (custo próprio) | R$ 48.790,00 |
| `antecipacao_de_nivel` | `ACT-ANTECIPACAO-NIVEL` | 4.610 | R$ 25,00 | Não aplicável (custo próprio) | R$ 115.250,00 |
| `educacao_beneficio_existente` | `ACT-EDUCA-BENEFICIO` | 139 | R$ 3,00 | Não aplicável (custo próprio) | R$ 417,00 |
| `pacote_experiencia_destino` | `ACT-PACOTE-EXPERIENCIA` | 130 | R$ 15,00 | Não aplicável (custo próprio) | R$ 1.950,00 |
| `reencaminhamento_atraso` | `ACT-ATRATRIBUI-ATRASO` | 1 | R$ 30,00 | Não aplicável (custo próprio) | R$ 30,00 |
| **Total Consolidado** | — | **14.638** | — | — | **R$ 166.437,00** |

### 4.2 Verificação do Fallback Operacional de R$ 45

Foi auditada a regra de fallback registrada em `ml/impact/simulate.py:80-83`:
```python
cost = act_val.get("cost_brl", 0.0)
# Se cost_brl for 0 (benefício contratual do tier), aplica fallback operacional R$ 45
action_costs[act_key] = FALLBACK_ACTION_COST_BRL if float(cost) == 0.0 else float(cost)
```

**Esclarecimento Fático:**
- As ações `educacao_beneficio_existente` (R$ 3), `pacote_experiencia_destino` (R$ 15) e `reencaminhamento_atraso` (R$ 30) **NÃO possuem custo 0 no YAML**. Cada uma possui seu custo próprio explicitado no arquivo de configuração.
- A única ação em `config/actions.yaml` com `cost_brl: 0` é `oferta_resgate_especial` (`ACT-RESGATE-ESPECIAL`), pois refere-se a cotas contratuais já garantidas do tier Safira/Diamante. Caso essa ação tivesse sido recomendada, ela receberia o fallback de R$ 45.
- Contudo, na base de 50.000 clientes, **nenhum cliente recebeu a recomendação de `oferta_resgate_especial`**.
- Logo, todas as 14.638 recomendações ativas foram precificadas pelos valores unitários nominais do YAML (R$ 5, R$ 25, R$ 3, R$ 15, R$ 30), totalizando exatamente **R$ 166.437,00**.

---

## 5. R3 · Bootstrap, Intervalos de Confiança e Análise de Sensibilidade

### 5.1 Execução do Módulo e Geração do Artefato JSON

O módulo de simulação foi executado via linha de comando oficial (`python tasks.py impact`, mapeado para `python -m ml.impact.simulate` em `tasks.py:71-72`). A execução consumiu 3,61s e atualizou com sucesso o arquivo canônico `data/analytics/impact_scenarios.json`.

Todos os 9 testes analíticos automatizados em `tests/test_impact.py` foram executados pelo revisor via pytest (`& .venv\Scripts\python.exe -m pytest tests/test_impact.py -v`), obtendo **100% de aprovação (9 passed in 3.61s)**.

### 5.2 Validação dos 3 Cenários e Sanity Check do Bootstrap

Os três cenários canônicos foram extraídos do JSON analítico e auditados contra os critérios estatísticos:

| Parâmetro / Métrica | Cenário Conservador | Cenário Base (Recomendado) | Cenário Otimista |
|---|:---:|:---:|:---:|
| **Efeito Retenção [PREMISSA]** | 5,0% (0,05) | 10,0% (0,10) | 15,0% (0,15) |
| **Resposta Canal [PREMISSA]** | 12,0% (0,12) | 18,0% (0,18) | 25,0% (0,25) |
| **Margem Contribuição [PREMISSA]** | 15,0% (0,15) | 20,0% (0,20) | 25,0% (0,25) |
| **Evasões Evitadas (JSON)** | 23,78 clientes | 71,33 clientes | 148,61 clientes |
| **Receita Bruta Salva** | R$ 3.230,30 | R$ 12.921,21 | R$ 33.648,99 |
| **IC95% Receita Bruta [Bootstrap]** | [R$ 3.205,56 ; R$ 3.253,74] | [R$ 12.822,23 ; R$ 13.014,96] | [R$ 33.391,22 ; R$ 33.893,12] |
| **Custo Total das Ações** | R$ 166.437,00 | R$ 166.437,00 | R$ 166.437,00 |
| **$\Delta\text{Receita Líquida}$** | **R$ -163.206,70** | **R$ -153.515,79** | **R$ -132.788,01** |
| **IC95% $\Delta\text{Receita}$ [Bootstrap]** | **[R$ -165.348,13 ; R$ -160.890,50]** | **[R$ -155.674,98 ; -R$ 151.200,89]** | **[R$ -134.935,50 ; -R$ -130.513,91]** |
| **Largura do IC95% (Max - Min)** | R$ 4.457,63 | R$ 4.474,09 | R$ 4.421,59 |
| **Ponto Contido no IC95%?** | **SIM** | **SIM** | **SIM** |
| **ROI Líquido sobre Custo** | -98,06% | -92,24% | -79,78% |

**Auditoria de Sanidade Estatística:**
- **Inclusão do Ponto:** Para todos os três cenários, a estimativa pontual está rigorosamente centrada e contida dentro do intervalo de confiança não paramétrico de 95% (bootstrap percentil com 1.000 reamostragens e seed 42).
- **Largura Plausível:** A dispersão do IC ($\approx \pm \text{R\$} 2.230$ em torno do ponto central) reflete com precisão o erro padrão amostral da soma vetorial de $14.638$ clientes com variância intrínseca nos CLVs e probabilidades preditas.
- **Monotonicidade Estrita:** Observa-se monotonicidade perfeita: $\Delta\text{Receita}_{\text{Otimista}} > \Delta\text{Receita}_{\text{Base}} > \Delta\text{Receita}_{\text{Conservador}}$ e $\text{ReceitaBruta}_{\text{Otimista}} > \text{ReceitaBruta}_{\text{Base}} > \text{ReceitaBruta}_{\text{Conservador}}$.

### 5.3 Análise de Sensibilidade Unidimensional (Tornado)

O ranking tornado padronizado gerado a partir de uma perturbação de $\pm 20\%$ ao redor do ponto de calibração Base ($\Delta\text{Receita} = -\text{R\$} 153.515,79$) foi verificado no JSON e revalidado analiticamente:

| Posição | Parâmetro Variado | Faixa Avaliada [-20% ; +20%] | $\Delta\text{Receita}$ Mínimo | $\Delta\text{Receita}$ Máximo | Amplitude (Swing BRL) | Elasticidade ($E$) |
|:---:|---|:---:|:---:|:---:|:---:|:---:|
| **1º** | **`custo_acao`** | [0,80x ; 1,20x] | R$ -186.803,19 | R$ -120.228,39 | **R$ 66.574,80** | **-1,0842** |
| **2º** | **`efeito_retencao`** | [8,0% ; 12,0%] | R$ -156.100,03 | R$ -150.931,54 | **R$ 5.168,49** | **+0,0842** |
| **3º** | **`resposta_canal`** | [14,4% ; 21,6%] | R$ -156.100,03 | R$ -150.931,54 | **R$ 5.168,49** | **+0,0842** |
| **4º** | **`margem`** | [16,0% ; 24,0%] | R$ -156.100,03 | R$ -150.931,54 | **R$ 5.168,49** | **+0,0842** |

**Diagnóstico Econômico e Confirmação de Hipótese:**
- **Dominância do Custo:** O custo operacional das ações é a variável disparadamente hegemônica, com amplitude de **R$ 66.574,80** e elasticidade pontual de **-1,0842**. Cada 1% de redução no custo das ações melhora o $\Delta\text{Receita}$ em 1,08%.
- **Simetria dos Direcionadores de Receita:** Os três parâmetros de receita (`efeito_retencao`, `resposta_canal` e `margem`) possuem rigorosamente o mesmo swing de **R$ 5.168,49** e a mesma elasticidade de **+0,0842**, o que confirma a consistência matemática da álgebra multiplicativa linear ($\text{Efeito} \times \text{Resposta} \times \text{Margem} \times \text{VaR}$).
- O custo é $\approx 12,88$ vezes mais influente no resultado final do que qualquer um dos parâmetros de conversão comercial.

---

## 6. R4 · Dimensionamento Amostral do Piloto A/B e Baseline

### 6.1 Recálculo Independente da População Alvo e Baseline Real

A estratificação da base sintética de clientes (`customers_scores.parquet`, 50.000 clientes) foi recomputada via pandas no script autônomo em `%TEMP%`:

1. **População de Alto Valor:**
   - Critério: `alto_valor == True`
   - Total encontrado: **5.005 clientes** (10,01% da base total de 50k).
2. **Mediana da Probabilidade de Evasão:**
   - Mediana de `churn_prob` entre clientes de alto valor: **0,094100** (9,41%).
3. **Público Elegível de Alto Valor em Risco:**
   - Critério: `alto_valor == True` e `churn_prob > 0,0941`
   - Total encontrado: **2.500 clientes** (exatamente 49,95% do estrato de alto valor).
4. **Baseline de Evasão e Retenção:**
   - Média de `churn_prob` no grupo de risco: $\bar{p}_{\text{churn}} = \mathbf{0,146245}$ (14,62%).
   - Baseline de retenção em 12 meses: $p_1 = 1 - \bar{p}_{\text{churn}} = 1 - 0,146245 = \mathbf{0,853755} \rightarrow \mathbf{85,38\%}$.

### 6.2 Formulação de Fleiss para Teste de Proporções

Para o dimensionamento do tamanho amostral por braço ($n$) no teste de hipótese bicaudal de duas proporções independentes ($H_0: p_1 = p_2$ vs $H_1: p_1 \ne p_2$), o projeto adota a formulação padrão de Fleiss:

$$n = \frac{\left( Z_{\alpha/2} \sqrt{2 \bar{p} (1 - \bar{p})} + Z_{\beta} \sqrt{p_1 (1 - p_1) + p_2 (1 - p_2)} \right)^2}{\delta^2}$$

Onde:
- $\alpha = 0,05$ bilateral $\Rightarrow Z_{\alpha/2} = 1,9599639845$
- Poder $1 - \beta = 0,80 \Rightarrow Z_{\beta} = 0,8416212336$
- $\delta = \text{MDE} = +0,02$ (+2 pontos percentuais)
- $p_1 = 0,853755$ (baseline do controle)
- $p_2 = p_1 + \delta = 0,873755$ (taxa esperada no tratamento)
- $\bar{p} = (p_1 + p_2) / 2 = 0,863755$

### 6.3 Recálculo do Dimensionamento Primário (+2pp) e Caso Fechado

O revisor recomputou analiticamente os dois casos via script independente:

1. **Piloto Primário com Baseline Real ($p_1 = 0,8538$, $\text{MDE} = +2\text{pp}$):**
   - $n_{\text{contínuo}} = 4.617,2045$
   - $n_{\text{arredondado}} = \lceil 4.617,2045 \rceil = \mathbf{4.618\text{ clientes por braço}}$.
   - Tamanho amostral total ($2n$): $\mathbf{9.236\text{ clientes}}$.
   - Bate **100%** com o valor do JSON (`plano_piloto_ab.dimensionamento_primario_mde_2pp.n_por_braco = 4618`) e com o texto de `docs/impact_simulation.md`.

2. **Caso Analítico Fechado de Literatura ($p_1 = 0,50$, $\text{MDE} = +5\text{pp}$):**
   - Para validação metodológica de calibração clássica ($p_1 = 0,50$, $p_2 = 0,55$, $\alpha=0,05$, poder $80\%$):
   - $n_{\text{contínuo}} = 1.564,6721$
   - $n_{\text{arredondado}} = \lceil 1.564,6721 \rceil = \mathbf{1.565\text{ clientes por braço}}$.
   - Bate **100%** com o valor de referência (`tests/test_impact.py::test_closed_case_sample_size_analytical`) e com `docs/impact_simulation.md §7.2`.

### 6.4 Viabilidade na Amostra Local vs Escala Corporativa Real

O plano registra com honestidade técnica a discrepância de capacidade amostral:
- **Amostra Sintética Local (50k):** O contingente elegível de Alto Valor em Risco é de 2.500 clientes. Como o teste de +2pp requer 9.236 clientes ($2 \times 4.618$), o experimento **não cabe** nessa amostra local. O MDE mínimo detectável com 80% de poder na amostra local é de **+4pp** ($n=1.082$/braço, total 2.164 clientes).
- **Escala Corporativa (Azul Fidelidade 20,1M):** Na base real do programa, a população de alto valor estimada ultrapassa 140.000 membros (>70.000 em risco), permitindo folga para mais de 7 experimentos simultâneos com MDE de +2pp ou pilotos altamente refinados com MDE de +1pp.

### 6.5 Cobertura sob Teto Orçamentário de R$ 80.000 (VaR)

A auditoria revalidou a simulação de restrição orçamentária:
- Ordenação por `valor_em_risco` decrescente consome **R$ 79.995,00** para cobrir **6.170 clientes** (42,15% da base de 14.638).
- Esses 6.170 clientes concentram **R$ 2.117.680,36** de Valor em Risco, capturando **59,00%** de todo o risco da base elegível (vs R$ 3.589.378,35 total).
- Frente à heurística simplificada de custo médio de R$ 45 (Tela 06), que cobriria 1.777 clientes, o algoritmo do playbook com ações de R$ 5 e R$ 25 entrega uma cobertura **3,47 vezes superior**.

---

## 7. R5 · Auditoria de Governança, Honestidade Intelectual e Paridade Documental

### 7.1 Rotulagem Estrita de Premissas Operacionais

A documentação analítica (`docs/impact_simulation.md`) foi submetida a varredura linha a linha para verificar a classificação transparente de hipóteses:
- **Efeito de Retenção (5% a 15%):** Declarado expressamente com a tag `[PREMISSA]` nas seções 2.1 e 2.2, contextualizado em benchmarks de retenção de CRM de fidelidade.
- **Taxa de Resposta do Canal (12% a 25%):** Declarada com a tag `[PREMISSA]`, refletindo taxas históricas de abertura e clique em comunicação omnicanal.
- **Margem de Contribuição (15% a 25%):** Declarada com a tag `[PREMISSA]`, representando a margem de contribuição operacional sobre receita incremental no setor aéreo.
- **Fallback de Ação R$ 45:** Explicitamente documentado na seção 1.2 com citação e vínculo a `docs/limitations.md §8`.
- **Premissa Cambial (USD 1,00 = BRL 5,50):** Rotulada como premissa paramétrica na seção 8.2 para precificação de tokens de inferência.
- **Preços por Token de LLM:** Declarados como estimativas prospectivas de mercado na seção 8.2 (US$ 0,40 / 1,50 / 5,00 por milhão de tokens combinados).

### 7.2 Honestidade Intelectual Radical: O Déficit não foi Suavizado

O relatório técnico dedica a Seção 4 integralmente à análise de ponto de equilíbrio e justificativa do $\Delta\text{Receita}$ negativo:
- **Ausência de Maquiagem:** O documento não tenta disfarçar o déficit de **R$ -153.515,79** no cenário base nem o ROI negativo de **-92,24%**.
- **Racional de CRM:** Explica didaticamente que intervenções custando entre R$ 5 e R$ 25 geram retorno esperado de apenas **R$ 0,22 a R$ 2,30** por cliente quando aplicadas indiscriminadamente sobre segmentos de baixo risco ou baixo CLV.
- **Diretriz Estratégica:** Demonstra com rigor numérico que campanhas "em massa" (*blanket campaigns*) destroem valor financeiro, e que a sustentabilidade de programas de retenção reside exclusivamente em:
  1. Segmentação estrita em clientes de Alto Valor com risco iminente;
  2. Migração para canais 100% digitais com custo marginal nulo (notificações push no app / e-mail transacional).

### 7.3 Registro Formal de Limitações Metodológicas

A Seção 9 de `docs/impact_simulation.md` cumpre o protocolo de transparência do projeto ao listar:
1. **Efeito Não Causal:** O lift de retenção é uma premissa analítica e não uma evidência causal observada; a causalidade real depende estritamente do piloto A/B com grupo de controle.
2. **Natureza Sintética da Carteira:** Embora calibrada contra dados públicos e regulamentos da Azul, a base é sintética e tem caráter demonstrativo de engenharia de software e modelagem estatística.
3. **Ausência de Modelagem de Uplift Individual:** O modelo prioriza por valor em risco absoluto ($VaR = P_{\text{churn}} \times CLV$) e não por propensão individual ao tratamento (Uplift Causal via T-Learner ou X-Learner), registrado como oportunidade de evolução.

### 7.4 Auditoria Cruzada de Paridade Numérica: `docs/impact_simulation.md` vs `impact_scenarios.json`

O confronto sistemático entre os valores descritos no documento e o artefato computacional gerado revelou altíssima paridade:

| Parâmetro / Métrica | Valor no Documento Markdown | Valor no JSON Analítico | Paridade Confirmada |
|---|:---:|:---:|:---:|
| **Clientes Alvo Elegíveis** | 14.638 | 14.638 | **SIM (100%)** |
| **Custo Total do Playbook** | R$ 166.437,00 | R$ 166.437,00 | **SIM (100%)** |
| **$\Delta\text{Receita}$ Conservador** | R$ -163.206,70 | R$ -163.206,70 | **SIM (100%)** |
| **IC95% Conservador** | [-R$ 165.348,13 ; -R$ 160.890,50] | [-R$ 165.348,13 ; -R$ 160.890,50] | **SIM (100%)** |
| **$\Delta\text{Receita}$ Base** | R$ -153.515,79 | R$ -153.515,79 | **SIM (100%)** |
| **IC95% Base** | [-R$ 155.674,98 ; -R$ 151.200,89] | [-R$ 155.674,98 ; -R$ 151.200,89] | **SIM (100%)** |
| **$\Delta\text{Receita}$ Otimista** | R$ -132.788,01 | R$ -132.788,01 | **SIM (100%)** |
| **IC95% Otimista** | [-R$ 134.935,50 ; -R$ 130.513,91] | [-R$ 134.935,50 ; -R$ 130.513,91] | **SIM (100%)** |
| **Receita Bruta Salva (Cons/Base/Otim)** | R$ 3.230,30 / 12.921,21 / 33.648,99 | R$ 3.230,30 / 12.921,21 / 33.648,99 | **SIM (100%)** |
| **Break-even Unitário (Cons/Base/Otim)** | R$ 0,22 / R$ 0,88 / R$ 2,30 | R$ 0,22 / R$ 0,88 / R$ 2,30 | **SIM (100%)** |
| **Clientes Cobertos sob R$ 80k (VaR)** | 6.170 (42,15%) | 6.170 (42,15%) | **SIM (100%)** |
| **Investimento Efetivo sob R$ 80k** | R$ 79.995,00 | R$ 79.995,00 | **SIM (100%)** |
| **Valor em Risco Capturado (VaR)** | R$ 2.117.680,43 | R$ 2.117.680,36 | **RESSALVA (R$ 0,07)** |
| **VaR Capturado %** | 59,00% | 59,00% | **SIM (100%)** |
| **População Alto Valor / Mediana** | 5.005 clientes / 0,0941 | 5.005 clientes / 0,0941 | **SIM (100%)** |
| **Público Piloto Alto Valor em Risco** | 2.500 clientes | 2.500 clientes | **SIM (100%)** |
| **Baseline Retenção ($1 - p_1$)** | 85,38% | 85,38% | **SIM (100%)** |
| **$n$ Amostral Piloto MDE +2pp** | 4.618 / braço (total 9.236) | 4.618 / braço (total 9.236) | **SIM (100%)** |
| **$n$ Caso Fechado Analítico (50%/5pp)** | 1.565 / braço (total 3.130) | 1.565 / braço (total 3.130) | **SIM (100%)** |
| **Custos LLM (Econ/Std/Prem)** | R$ 66-99 / R$ 247-371 / R$ 825-1.238 | R$ 66-99 / R$ 247,5-371,25 / R$ 825-1.237,5 | **SIM (100%)** |
| **Tornado: Amplitude Custo vs Demais** | R$ 66.574,80 vs R$ 5.168,49 | R$ 66.574,80 vs R$ 5.168,49 | **SIM (100%)** |
| **Evasões Evitadas Estimadas** | 23,47 / 70,42 / 146,70 | 23,78 / 71,33 / 148,61 | **RESSALVA (1,3%)** |

---

## 8. Quadro Consolidado de Achados e Recomendações

### Quadro de Achados

| ID | Classificação | Requisito | Descrição Sintética | Impacto no Projeto | Ação Recomendada |
|---|---|:---:|---|---|---|
| **ACH-01** | **MENOR** | R5 · Paridade | Discrepância de 1,3% na linha descritiva de Evasões Evitadas Estimadas na tabela da Seção 3 de `docs/impact_simulation.md` (reporta 23,47 / 70,42 / 146,70 enquanto o JSON computa 23,78 / 71,33 / 148,61). | Nulo sobre o resultado financeiro ($\Delta\text{Receita}$, Receita Bruta e Custo batem 100% ao centavo). | Atualizar a linha descritiva da tabela no markdown para espelhar exatamente os números serializados em `impact_scenarios.json` em próxima revisão documental. |
| **ACH-02** | **OBSERVAÇÃO** | R5 · Paridade | Discrepância residual de R$ 0,07 no VaR Capturado sob R$ 80k (R$ 2.117.680,43 no documento vs R$ 2.117.680,36 no JSON). | Desprezível (erro relativo de 0,000003% em R$ 2,1 milhões decorrente de ponto flutuante). | Ajustar os centavos no texto da Seção 5.1 para R$ 2.117.680,36 para paridade de string exata. |

---

## 9. Conclusão da Auditoria

A frente **WS9 (Simulação de Impacto Financeiro + Piloto A/B)** cumpriu integralmente todos os objetivos analíticos e de engenharia com qualidade excepcional:
- A modelagem matemática é irrefutável e foi revalidada por recálculo independente em pandas.
- O custo do playbook de ações decorre fielmente de `config/actions.yaml`.
- Os intervalos de confiança e testes estatísticos do piloto possuem embasamento teórico clássico (bootstrap percentil e fórmula de Fleiss).
- A governança analítica praticou transparência e honestidade técnica radical, apresentando resultados sem artifícios promocionais e ancorando o projeto na realidade corporativa.

**Veredito:** **APROVADO** (sem achados Críticos ou Importantes).




