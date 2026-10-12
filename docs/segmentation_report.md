# Relatório Técnico de Segmentação, Score de Alto Valor e Personas (WS5)

> **Projeto Aura 2.0** — Pipeline Reproduzível de Inteligência de Clientes e Retenção do Azul Fidelidade  
> **Frente:** Workstream 5 (WS5 · ScoreAV, Segmentação/Personas, ARI e Auditoria)  
> **Data:** 18 de Maio de 2025  
> **Status:** Concluído e Validado  

---

## 1. Sumário Executivo

A frente WS5 consolida o núcleo de inteligência de decisão do Projeto Aura 2.0. Integrando predições supervisionadas de CLV 12m e risco de evasão (churn) com histórico transacional e interacional do Azul Fidelidade, esta frente produz:
1. **Score de Alto Valor (ScoreAV):** ranking percentilar balanceado (60% CLV, 20% RFM composto, 20% Potencial) com estrita garantia anti-vazamento temporal e proibição de atributos sensíveis.
2. **Justificativa Empírica do Corte:** análise de Pareto demonstrando que o corte superior de **10%** captura **46,97%** da receita futura prevista de toda a carteira de 50.000 clientes.
3. **Análise de Sensibilidade:** prova mecânica de estabilidade do ranking sob variações de pesos ($\pm 0,10$, mantendo soma 1,0) com correlações de Spearman superiores a **0,998** e Jaccard no corte de 10% entre **87,1% e 92,7%**.
4. **Segmentação Não-Supervisionada:** modelo híbrido KMeans e Gaussian Mixture Models (GMM) com alinhamento ARI de **0,8109** e estabilidade bootstrap de **0,9123**.
5. **Recuperação de Arquétipos (ARI vs Ground Truth):** mensuração honesta de **$\text{ARI} = 0,1642$**, acompanhada de fundamentação técnica sobre a cisão entre arquétipos estocásticos latentes e clusters observáveis comportamentais.
6. **Personas Comerciais e Playbook de Retenção:** 6 personas quantificadas e mapeadas para ações acionáveis do catálogo `config/actions.yaml`.

---

## 2. Score de Alto Valor (ScoreAV)

### 2.1 Formulação Matemática
O ScoreAV é formulado como uma média ponderada de postos percentilares, eliminando distorções de escala monetária e assimetria de cauda:

$$\text{ScoreAV}_i = 0{,}60 \cdot \text{pct}(\widehat{\text{CLV}}_{12m, i}) + 0{,}20 \cdot \text{pct}(\text{RFM}_{i}) + 0{,}20 \cdot \text{pct}(\text{Potencial}_{i})$$

Onde:
- **$\text{pct}(\widehat{\text{CLV}}_{12m})$:** rank percentilar da predição pontual do modelo LightGBM treinado na WS4.
- **$\text{pct}(\text{RFM})$:** rank percentilar do escore composto padronizado:
  $$\text{RFM}_i = \frac{z(-\text{recência}_i) + z(\text{frequência}_i) + z(\text{monetário}_i)}{3}$$
  (a recência em dias é invertida pois menor inatividade indica maior proximidade de relacionamento).
- **$\text{pct}(\text{Potencial})$:** rank percentilar do composto de aceleração e margem de qualificação:
  $$\text{Potencial}_i = \frac{\text{pct}(\text{frequency\_trend}_i) + \text{pct}(\text{meta\_proximo\_nivel\_pct}_i)}{2}$$

### 2.2 Salvaguardas Éticas e Anti-Vazamento
- **Filtro Temporal Estrito:** todos os insumos derivam exclusivamente de registros com data $\le \text{cutoff}$ (`2025-08-31`).
- **Bloqueio Categórico de Atributos Sensíveis:** asserts em código garantem que `faixa_etaria`, `genero` e `regiao` jamais participem das matrizes de cálculo do ScoreAV nem da clusterização.
- **Isolamento de Targets Futuros:** nenhum target realizado (`target_clv_12m`, `target_churn_12m`) é consumido pelo algoritmo de pontuação.

---

## 3. Justificativa Empírica do Corte de Alto Valor (Curva de Pareto)

A seleção dos clientes prioritários baseia-se na concentração da receita prevista de 12 meses ($\sum \widehat{\text{CLV}} = \text{R\$}~25.412.398,82$):

| Corte Superior | Clientes ($N$) | Receita Capturada (R$) | % da Receita Total | ScoreAV Mínimo | Comentário Operacional |
|:---|:---:|:---:|:---:|:---:|:---|
| **Top 5%** | 2.500 | R$ 7.747.886,81 | 30,49% | 0,9336 | Hiper-foco em super-executivos e alta renda; deixa de fora parcela relevante em progressão |
| **Top 10% (Eleito)** | **5.000** | **R$ 11.936.438,70** | **46,97%** | **0,8840** | **Ponto ótimo de equilíbrio: captura quase metade da receita com cobertura operacional viável** |
| **Top 15%** | 7.500 | R$ 14.584.972,70 | 57,39% | 0,8369 | Ganho marginal decrescente; eleva custo total das campanhas proativas |
| **Top 20%** | 10.000 | R$ 16.486.877,65 | 64,88% | 0,7924 | Diluição do foco do time de relacionamento; abrange clientes de média frequência |

**Conclusão Técnica:** O corte em **Top 10%** (ScoreAV $\ge 0,8840$) maximiza a densidade de valor sob orçamento de retenção finito ($\le \text{R\$}~400/\text{cliente}$), alinhando-se com a diretriz de negócio de `config/settings.yaml` e as fixtures da aplicação.

---

## 4. Análise de Sensibilidade e Estabilidade do Ranking

Foi executada uma grade sistemática de perturbação de pesos $\pm 0,10$ com restrição $\sum w = 1,00$, avaliando a concordância de ordenação (Spearman, Kendall tau-b) e a estabilidade do conjunto eleito (Índice de Jaccard):

| Configuração de Pesos | Descrição | Spearman ($r_s$) | Kendall ($\tau$) | Jaccard @ 5% | Jaccard @ 10% | Jaccard @ 15% | Jaccard @ 20% |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **(0.60, 0.20, 0.20)** | **Baseline Canônico** | **1,0000** | **1,0000** | **1,0000** | **1,0000** | **1,0000** | **1,0000** |
| (0.50, 0.20, 0.30) | Mais Potencial | 0,9990 | 0,9779 | 0,8505 | 0,8713 | 0,9255 | 0,9376 |
| (0.50, 0.30, 0.20) | Mais RFM | 0,9993 | 0,9809 | 0,9253 | 0,9260 | 0,9423 | 0,9558 |
| (0.60, 0.10, 0.30) | Foco Potencial | 0,9996 | 0,9852 | 0,8839 | 0,9033 | 0,9395 | 0,9610 |
| (0.60, 0.30, 0.10) | Foco RFM | 0,9996 | 0,9839 | 0,8553 | 0,9231 | 0,9475 | 0,9656 |
| (0.70, 0.10, 0.20) | Foco CLV Alto | 0,9993 | 0,9815 | 0,9290 | 0,9272 | 0,9372 | 0,9505 |
| (0.70, 0.20, 0.10) | CLV Máximo | 0,9986 | 0,9742 | 0,8162 | 0,8947 | 0,9248 | 0,9327 |

**Achado:** Em todas as variações, o Spearman permaneceu acima de $0,998$ e a sobreposição do conjunto de Alto Valor (Jaccard @ 10%) superou $87\%$. O score é estruturalmente robusto a calibrações de pesos.

---

## 5. Modelagem de Agrupamento e Recuperação de Arquétipos

### 5.1 Seleção de K e Estabilidade
Foram avaliadas 13 features comportamentais padronizadas. O critério de Silhouette score apontou monotonicidade de separação de $K=4$ a $K=7$:
- $K=4$: Silhouette = $0,5009$
- $K=5$: Silhouette = $0,5179$
- **$K=6$ (Selecionado):** Silhouette = **$0,5258$**, Estabilidade Bootstrap $\text{ARI} = \mathbf{0{,}9123 \pm 0{,}0694}$ ($N=10$ pares).
- $K=7$: Silhouette = $0,5307$ (gera fragmentação de clusters com semântica operacional redundante).

### 5.2 Alinhamento KMeans vs GMM
A aderência entre agrupamento geométrico (KMeans) e probabilístico por densidade gaussiana (GMM) atingiu:
$$\text{ARI}(\text{KMeans}, \text{GMM}) = \mathbf{0{,}8109}$$
indicando que a estrutura dos dados possui forte coesão intrínseca independente da formulação do otimizador.

### 5.3 Recuperação de Arquétipos Latentes (ARI vs Ground Truth)
A comparação entre as atribuições de cluster observáveis e a variável latente geratriz (`latent_archetype` de `data/curated/ground_truth.parquet`) resultou em:
$$\text{ARI}(\text{Observado}, \text{Ground Truth}) = \mathbf{0{,}1642}$$

#### Discussão Honesta sobre a Meta Teórica ($\ge 0{,}80$) vs Resultado Real ($0{,}1642$):
A meta preliminar do plano mestre pressupunha que os arquétipos latentes do gerador sintético se manifestariam de forma diretamente separável nas métricas agregadas dos clientes. A realidade empírica dos dados v3 revelou uma dinâmica muito mais realista:
1. **Dormência Massiva e Indistinguibilidade Observável:** 58% dos clientes `eventual_promocional`, 32% dos `lazer_premium` e 25% dos `regional_dependente` e `maximizador_milhas` não realizaram voos no período histórico. No espaço de features observáveis ($\le \text{cutoff}$), clientes sem voos e sem gastos são matematicamente indistinguíveis entre si (vetores idênticos ou quase nulos), embora possuam arquétipos latentes diferentes no gerador.
2. **Heterogeneidade Multivariada Estocástica:** Conforme modelado na WS2, cada cliente possui termos de choque individual ($\theta_{\text{freq}}$, $\theta_{\text{spend}}$, $\theta_{\text{churn}}$) com variância significativa, gerando sobreposição real nas distribuições empíricas.
3. **Emergência de Personas Operacionais (6 vs 5):** O agrupamento comportamental detectou o grupo de **`eventual_ascendente`** (clientes em aceleração de frequência e pontos, próximos ao upgrade de tier), o qual não existia como família estática única no gerador mas emerge naturalmente da dinâmica de qualificação do programa.
4. **Integridade Científica:** Nenhuma feature do ground truth foi vazada para "maquiar" o ARI. O valor reportado reflete o agrupamento não-supervisionado legítimo dos dados disponíveis em produção.

---

## 6. Caracterização Quantitativa das 6 Personas Comerciais

A tabela abaixo resume a carteira oficial gerada pelo pipeline (`data/analytics/personas_summary.parquet`):

| Persona | Membros ($N$) | Share (%) | CLV 12M Médio | Churn Médio | Valor em Risco Total | Ticket Médio | Atritos Dominantes | Ação Recomendada do Playbook |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---|:---|
| **Executivo Recorrente** | 1.312 | 2,62% | R$ 6.522,80 | 2,61% | R$ 205.091,40 | R$ 469,20 | atraso, atendimento | Contato Proativo (ACT-CONTATO) |
| **Eventual Ascendente** | 5.121 | 10,24% | R$ 2.155,50 | 18,22% | R$ 1.526.866,10 | R$ 419,90 | app_checkin, preco | Antecipação de Nível (ACT-ANTECIPACAO-NIVEL) |
| **Regional Dependente** | 9.763 | 19,53% | R$ 888,20 | 33,01% | R$ 2.315.986,10 | R$ 430,50 | conforto, cancelamento | Garantia Conectividade (ACT-CONTATO) |
| **Lazer Premium** | 4.645 | 9,29% | R$ 831,50 | 29,84% | R$ 887.678,60 | R$ 259,40 | preco, bagagem | Oferta Rota Favorita (ACT-OFERTA-ROTA) |
| **Maximizador de Milhas** | 4.949 | 9,90% | R$ 477,30 | 22,01% | R$ 454.687,00 | R$ 1.144,70 | resgate_milhas, app_checkin | Oferta Resgate Especial (ACT-RESGATE-ESPECIAL) |
| **Eventual Promocional** | 24.210 | 48,42% | R$ 209,10 | 73,60% | R$ 2.915.187,20 | R$ 185,30 | preco | Campanha Promocional (ACT-BONUS-PONTOS) |
| **Total / Média** | **50.000** | **100%** | **R$ 508,25** | **48,93%** | **R$ 8.305.496,40** | **R$ 404,18** | — | — |

---

## 7. Rastreabilidade de Artefatos Produzidos

Todos os artefatos foram validados contra seus contratos em `schemas/`:
- `data/analytics/score_av.parquet`: $50.000$ linhas $\times$ 7 colunas (validado via `schemas/score_av.yaml`).
- `data/analytics/segments.parquet`: $50.000$ linhas $\times$ 5 colunas (validado via `schemas/segments.yaml`).
- `data/analytics/personas_summary.parquet`: 6 linhas $\times$ 12 colunas (validado via `schemas/personas_summary.yaml`).
- `data/analytics/personas_profiles.json`: dicionário JSON estruturado para visualização e agentes.
- `data/analytics/customers_scores.parquet`: $50.000$ linhas $\times$ 24 colunas (validado via `schemas/customers_scores.yaml`).
- `data/analytics/customer_timeline.parquet`: $282.507$ eventos históricos (validado via `schemas/customer_timeline.yaml`).
- `data/analytics/agent_input.parquet`: $50.000$ linhas $\times$ 17 colunas (validado via `schemas/agent_input.yaml`).
