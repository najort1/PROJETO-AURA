# Relatório de IA Responsável, Auditoria de Equidade e Governança LGPD (WS5)

> **Projeto Aura 2.0** — Pipeline Reproduzível de Inteligência de Clientes e Retenção do Azul Fidelidade  
> **Frente:** Workstream 5 (WS5 · Auditoria de Fairness e Salvaguardas Éticas)  
> **Data:** 12 de outubro de 2026  
> **Status:** Concluído e Auditado  
> **Nota de correção (Lead, 12/10/2026):** a versão inicial deste relatório misturava
> números de fixtures com os da base real e rotulava clientes sem atributo declarado
> com bins fictícios ("30-49"/"Sudeste"). Corrigido: nulls = **"não informado"**
> (honesto, LGPD), fora do denominador e das contagens da regra 4/5; todos os números
> abaixo re-extraídos de `data/analytics/fairness_metrics.parquet` pós-regeneração.

---

## 1. Princípios de Governança e Enquadramento LGPD

O Projeto Aura 2.0 foi concebido sob princípios estritos de **Privacidade por Design (Privacy by Design)** e **Inteligência Artificial Responsável**:

1. **Dados Sintéticos Controlados (Zero PII):**
   - Todo o pipeline opera sobre uma base sintética calibrada gerada a partir de agregações estatísticas públicas da ANAC e premissas operacionais do setor aéreo brasileiro.
   - Nenhum dado pessoal identificável real (CPF, nome civil, número de telefone, cartão de crédito real) foi ingerido, armazenado ou processado.
2. **Proibição Categórica de Atributos Sensíveis nas Features:**
   - As variáveis demográficas protegidas (`faixa_etaria`, `genero` e `regiao`) existem exclusivamente para fins de auditoria de conformidade ex-post.
   - Asserts estritos em tempo de execução garantem que nenhum modelo de aprendizado supervisionado (CLV, Churn) ou não-supervisionado (KMeans, GMM, ScoreAV) utilize atributos sensíveis como preditores.
3. **Direito à Explicação e Humano no Circuito (Artigo 20 da LGPD):**
   - Decisões preditivas críticas (clientes de alto valor em risco severo) acionam obrigatoriamente a flag de **Revisão Humana (Human-in-the-Loop - HITL)** no painel operacional antes de qualquer despacho de comunicação.

---

## 2. Metodologia de Auditoria: A Regra dos Quatro Quintos (Four-Fifths Rule)

Para auditar o impacto desproporcional (*Disparate Impact*) na seleção de clientes classificados como **Alto Valor (Top 10% da carteira pelo ScoreAV)**, foi adotada a diretriz regulatória dos Quatro Quintos (EEOC 29 CFR § 1607.4):

$$\text{Razão de Disparidade (Ratio)} = \frac{\text{Taxa de Seleção do Grupo Avaliado}}{\text{Taxa de Seleção do Grupo de Maior Seleção}}$$

- **Critério de Conformidade:** Se $\text{Ratio} \ge 0{,}80$ ($80\%$), considera-se que o modelo opera sem evidência estatística de impacto desproporcional adverso.
- **Não-Conformidade (Alerta de Viés):** Se $\text{Ratio} < 0{,}80$, o subgrupo é marcado com flag de disparidade para investigação de causas de domínio e plano de mitigação.

---

## 3. Resultados Reais da Auditoria na Base de 50.000 Clientes

A tabela abaixo reporta os valores **reais e não maquiados** medidos sobre `data/analytics/customers_scores.parquet` gerado pelo pipeline:

### 3.1 Faixa Etária (grupos informados; baseline = maior taxa informada)

| Grupo Demográfico | Amostra ($N$) | Clientes Alto Valor | Taxa de Seleção | Razão vs Máximo | Churn Médio | Conformidade (4/5) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **18-24** | 5.925 | 513 | 8,66% | **0,7950** | 50,15% | ⚠️ **Não Conforme (< 0,80)** |
| **25-34** | 15.206 | 1.484 | 9,76% | 0,8961 | 49,07% | ✅ Conforme |
| **35-44** | 13.816 | 1.489 | 10,78% | 0,9896 | 48,47% | ✅ Conforme |
| **45-59** | 10.505 | 1.019 | 9,70% | 0,8906 | 49,07% | ✅ Conforme |
| **60+ (Referência)** | 3.939 | 429 | 10,89% | 1,0000 | 48,22% | ✅ Grupo Base |

### 3.2 Gênero (grupos informados; baseline = maior taxa informada)

| Grupo Demográfico | Amostra ($N$) | Clientes Alto Valor | Taxa de Seleção | Razão vs Máximo | Churn Médio | Conformidade (4/5) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Prefiro não informar (Ref.)** | 940 | 110 | 11,70% | 1,0000 | 48,27% | ✅ Grupo Base |
| **Feminino** | 23.003 | 2.408 | 10,47% | 0,8946 | 48,54% | ✅ Conforme |
| **Masculino** | 23.644 | 2.261 | 9,56% | 0,8172 | 49,39% | ✅ Conforme |
| **Outro** | 496 | 52 | 10,48% | 0,8959 | 49,09% | ✅ Conforme |

### 3.3 Região Geográfica (sem nulls na base; baseline = Norte)

| Grupo Demográfico | Amostra ($N$) | Clientes Alto Valor | Taxa de Seleção | Razão vs Máximo | Churn Médio | Conformidade (4/5) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Norte (Referência)** | 1.978 | 300 | 15,17% | 1,0000 | 48,06% | ✅ Grupo Base |
| **Nordeste** | 8.027 | 881 | 10,98% | **0,7236** | 48,95% | ⚠️ **Não Conforme (< 0,80)** |
| **Centro-Oeste** | 5.016 | 532 | 10,61% | **0,6993** | 48,81% | ⚠️ **Não Conforme (< 0,80)** |
| **Sudeste** | 26.015 | 2.534 | 9,74% | **0,6422** | 48,83% | ⚠️ **Não Conforme (< 0,80)** |
| **Sul** | 8.964 | 758 | 8,46% | **0,5575** | 49,56% | ⚠️ **Não Conforme (< 0,80)** |

### 3.4 Grupos com dado não informado (transparência LGPD — fora da regra 4/5)

Clientes que não declararam o atributo NÃO são imputados com valor factual
(nunca "Sudeste" ou uma faixa etária inventada): são rotulados **"não informado"**.
O grupo é reportado por transparência, mas não participa do julgamento
demográfico da regra 4/5 (não é um grupo demográfico — é um artefato de completude):

| Dimensão | N "não informado" | Alto Valor | Taxa | Razão (informativa) |
|:---|:---:|:---:|:---:|:---:|
| faixa_etaria | 609 | 71 | 11,66% | 1,0705 |
| genero | 1.917 | 174 | 9,08% | 0,7756 |
| regiao | 0 | — | — | — |

**Síntese da auditoria: 9 de 14 grupos demográficos informados conformes; 5 não conformes** (faixa 18-24 e as regiões Sul, Sudeste, Centro-Oeste e Nordeste).

---

## 4. Diagnóstico Técnico das Disparidades Observadas

### 4.1 Faixa Etária: Sub-representação de Jovens (18-24 anos @ 0,7950)
- **Causa Raiz Econômica:** Clientes na faixa de 18 a 24 anos estão em início de carreira, com menor renda disponível e quase nula participação em viagens corporativas de negócios (que geram as passagens com tarifa cheia e curta antecedência).
- **Reflexo no Modelo:** Como o ScoreAV pondera fortemente CLV previsto e histórico de gastos, o padrão econômico observado na aviação naturalmente reduz a incidência de jovens no decil superior de valor.

### 4.2 Região Geográfica: Efeito Anômalo da Concentração Regional no Norte
- **Causa Estrutural do Setor Aéreo:** A Azul Linhas Aéreas detém papel vital na conectividade da Amazônia Legal e interior do Norte, operando rotas com baixa concorrência, distâncias continentais e tickets médios elevados.
- **Distorção no Denominador:** A taxa de seleção no Norte é desproporcionalmente alta (**15,17%**). Quando essa taxa se torna o denominador da razão 4/5, todas as demais regiões (incluindo o Sudeste, que representa 52% da amostra e tem taxa de 9,74%) caem matematicamente abaixo de $0,80 \times 15,17\% = 12,14\%$.
- **Achado de Auditoria:** O problema não é uma penalização das demais regiões, mas sim uma superconcentração de clientes de perfil regional cativo de alto gasto no Norte.

---

## 5. Princípio da Honestidade Analítica: Não-Manipulação de Scores

A diretriz de engenharia deste projeto veda categoricamente o "conserto artificial" da disparidade por meio de cotas forçadas ou manipulação dos pesos do ScoreAV:
- **Scores Devem Medir Risco e Valor Real:** O ScoreAV é um instrumento de mensuração econômica e comportamental. Distorcê-lo artificialmente geraria alocação ineficiente do orçamento de retenção da companhia.
- **Auditoria Transparente:** O papel da auditoria de fairness é **revelar a realidade**, permitindo que a liderança de produto e de negócios tome medidas compensatórias deliberadas na camada de campanha, e não que os cientistas de dados escondam a disparidade sob modelos calibrados artificialmente.

---

## 6. Salvaguardas Operacionais e Plano de Mitigação

### 6.1 Transparência de Citações e RAG Versionado
Para impedir alucinações nas ofertas de retenção geradas por agentes generativos:
- O agente só tem permissão de ofertar benefícios sustentados por um `fact_id` oficial do regulamento (ex.: `AF-TIER-SAFIRA`, `AF-RESGATE-ESPECIAL-2025`).
- Nenhuma ação fora do inventário congelado de `config/actions.yaml` pode ser executada.

### 6.2 Humano no Circuito (HITL)
No painel de acompanhamento (`app/views/04_agente.py` e `app/views/07_ia_responsavel.py`):
- Clientes com `churn_prob > 0.75` e `clv_12m_previsto > R$ 12.000` recebem bloqueio preventivo de envio automático, exigindo aprovação manual de um operador de relacionamento humano.
- O operador pode editar o texto da mensagem, com registro auditável em log de decisões (`decisions.jsonl`).

### 6.3 Plano de Ações Mitigadoras para Campanhas
1. **Campanha Jovem Universitário (Faixa 18-24):**
   - Criação de réguas de incentivo com metas acessíveis de acúmulo de pontos em viagens de férias, sem exigir o gasto monetário corporativo.
2. **Normalização Intrarregional:**
   - Em campanhas de CRM segmentadas por praça geográfica, calibrar o limiar de elegibilidade de alto valor relativamente à mediana de cada região, garantindo que o público cativo do Sul e Sudeste não seja preterido em ofertas promocionais.
3. **Monitoramento Contínuo:**
   - Auditoria automatizada integrada ao pipeline CI/CD via `tasks.py fairness`, emitindo alertas a cada re-treinamento da base.
