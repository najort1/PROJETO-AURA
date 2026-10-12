# Relatório de Revisão Independente — WS5 Parte B
**Auditoria de Fairness, ARI, Personas, Timeline e Honestidade dos Relatórios**  
**Projeto AURA 2.0**  
**Data:** 2025-05-18  
**Status da Revisão:** Concluído (Auditado)

> **ADENDO DO ORQUESTRADOR (12/10/2026, pós-gate final):** veredito histórico
> íntegro e imutável — B3 reconciliou as personas então vigentes
> (48,42% eventual_promocional; executivo CLV R$ 6.522,82). No retreino
> canônico pós-correção de não-determinismos (`docs/limitations.md §7b`),
> essas estatísticas moveram na 2ª casa decimal
> (48,41%; R$ 6.527,77). As 6 personas, seus nomes e a reconciliação
> biunívoca com `actions.yaml` permanecem idênticos.

---

## 1. Sumário Executivo e Veredito Parcial

- **Veredito:** ❌ **REPROVADO (B)** *(devido à presença de 1 achado de severidade IMPORTANTE no bloco B4 — vazamento temporal de datas na Linha do Tempo)*
- **Resumo dos Componentes Auditados:**
  - **B1 (Fairness):** ✅ **100% Conforme**. Recálculo independente em pandas confirma exatamente os valores de `fairness_metrics.parquet` e `docs/responsible_ai.md` §3. Tratamento de nulos com categoria `"não informado"` sem rótulos factuais artificiais. Total de 14 grupos demográficos informados: **9 conformes** e **5 não conformes** (18-24 @ 0,7950; Sul @ 0,5575; Sudeste @ 0,6422; Centro-Oeste @ 0,6993; Nordeste @ 0,7236).
  - **B2 (ARI):** ✅ **100% Conforme**. Recálculo exato de $\text{ARI} = \mathbf{0{,}1642}$ (0,164245). Discussão técnica em `docs/segmentation_report.md` §5.3 é plenamente honesta, justificando a dormência maciça da base ($57,20\%$ sem voos em 12m), a separação observável vs. latente e a emergência legítima da persona operacional `eventual_ascendente`.
  - **B3 (Personas):** ✅ **100% Conforme**. Reconciliação biunívoca entre os 6 nomes de `personas_summary.parquet` e os filtros de elegibilidade em `config/actions.yaml` (`personas_any`). Perfis quantitativos coerentes (`eventual_promocional` com 48,42% da base e 73,59% de churn; `executivo_recorrente` com 2,62% da base e CLV de R$ 6.522,82). Reconciliação semântica dos centróides transparente e bem documentada.
  - **B4 (Customer Timeline):** ⚠️ **REPROVADO [IMPORTANTE]**. O total de eventos bate ($282.507$ eventos, $30.453$ clientes cobertos). Porém, a asserção de que *"nenhum evento é posterior ao cutoff 2025-08-31"* falha: **$\text{MAX}(data) = \text{2025-11-29}$**, com **$4.802$ eventos de voo posteriores ao cutoff**, devido ao uso de `departure_date` sem filtro de teto temporal em passagens pré-compradas (`ml/segmentation/timeline.py`).
  - **B5 (Testes de Fairness):** ✅ **100% Conforme**. `pytest tests/test_fairness.py -q` executado com 3 testes passando verdes; teste com fixture 4/5 (Grupo A 100%, Grupo B 70% $\to$ ratio 0,70, Grupo C 85% $\to$ ratio 0,85) existe, está rigoroso e correto.

---

## 2. [B1] Análise de Fairness (Recálculo Independente)

### 2.1 Metodologia e Recálculo Independente (sem uso de `ml/fairness`)
O recálculo foi realizado via script independente em Python/Pandas diretamente a partir dos microdados brutos de escores em `data/analytics/customers_scores.parquet` ($N = 50.000$ clientes) e confrontado linha a linha contra a tabela analítica persistida `data/analytics/fairness_metrics.parquet` e o relatório formal `docs/responsible_ai.md` §3.

- **Baseline da Regra 4/5:** O grupo de referência (denominador) foi definido como o subgrupo demográfico **com a maior taxa de seleção entre os grupos informados** (excluindo explicitamente a categoria "não informado").
  - *Faixa Etária:* Grupo `60+` (Taxa de seleção: $10,891\%$ ou $0,1089$).
  - *Gênero:* Grupo `Prefiro nao informar` (Taxa de seleção: $11,702\%$ ou $0,1170$).
  - *Região:* Grupo `Norte` (Taxa de seleção: $15,167\%$ ou $0,1517$).
- **Tratamento de Dados Faltantes (Nulls):**
  - Em `data/curated/synthetic/customers.parquet`, os valores nulos totalizam exatamente:
    - `faixa_etaria`: 609 nulos;
    - `genero`: 1.917 nulos;
    - `regiao`: 0 nulos.
  - Na pipeline e em `customers_scores.parquet`, 100% desses registros são classificados estritamente como **"não informado"**, sem nenhuma imputação factual inventada (respeito irrestrito ao princípio da integridade e LGPD).
  - Conforme preconizado pelas diretrizes de governança ética, os registros "não informados" constam na tabela por transparência, mas **não participam** do cômputo regulatório demográfico da regra dos 4/5.

### 2.2 Confronto Linha a Linha: Recálculo vs `fairness_metrics.parquet` vs `docs/responsible_ai.md` §3

| Dimensão | Subgrupo Demográfico | Amostra ($N$) | Alto Valor | Taxa Seleção (Calc) | Taxa Seleção (PQ) | Razão vs Máx (Calc) | Razão vs Máx (PQ) | Status 4/5 (Calc) | Status 4/5 (PQ) | Doc §3 Bate? |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Faixa Etária** | 18-24 | 5.925 | 513 | 8,658% | 0,0866 | **0,7950** | **0,7950** | ⚠️ Não Conforme | False | ✅ 100% |
| | 25-34 | 15.206 | 1.484 | 9,759% | 0,0976 | 0,8961 | 0,8961 | ✅ Conforme | True | ✅ 100% |
| | 35-44 | 13.816 | 1.489 | 10,777% | 0,1078 | 0,9896 | 0,9896 | ✅ Conforme | True | ✅ 100% |
| | 45-59 | 10.505 | 1.019 | 9,700% | 0,0970 | 0,8906 | 0,8906 | ✅ Conforme | True | ✅ 100% |
| | 60+ (Ref.) | 3.939 | 429 | 10,891% | 0,1089 | 1,0000 | 1,0000 | ✅ Conforme | True | ✅ 100% |
| *(Informativo)* | não informado | 609 | 71 | 11,658% | 0,1166 | 1,0705 | 1,0705 | Informativo | True | ✅ 100% |
| **Gênero** | Feminino (F) | 23.003 | 2.408 | 10,468% | 0,1047 | 0,8946 | 0,8946 | ✅ Conforme | True | ✅ 100% |
| | Masculino (M) | 23.644 | 2.261 | 9,563% | 0,0956 | 0,8172 | 0,8172 | ✅ Conforme | True | ✅ 100% |
| | Outro | 496 | 52 | 10,484% | 0,1048 | 0,8959 | 0,8959 | ✅ Conforme | True | ✅ 100% |
| | Prefiro não informar (Ref.) | 940 | 110 | 11,702% | 0,1170 | 1,0000 | 1,0000 | ✅ Conforme | True | ✅ 100% |
| *(Informativo)* | não informado | 1.917 | 174 | 9,077% | 0,0908 | 0,7756 | 0,7756 | Informativo | True | ✅ 100% |
| **Região** | Norte (Ref.) | 1.978 | 300 | 15,167% | 0,1517 | 1,0000 | 1,0000 | ✅ Conforme | True | ✅ 100% |
| | Nordeste | 8.027 | 881 | 10,975% | 0,1098 | **0,7236** | **0,7236** | ⚠️ Não Conforme | False | ✅ 100% |
| | Centro-Oeste | 5.016 | 532 | 10,606% | 0,1061 | **0,6993** | **0,6993** | ⚠️ Não Conforme | False | ✅ 100% |
| | Sudeste | 26.015 | 2.534 | 9,741% | 0,0974 | **0,6422** | **0,6422** | ⚠️ Não Conforme | False | ✅ 100% |
| | Sul | 8.964 | 758 | 8,456% | 0,0846 | **0,5575** | **0,5575** | ⚠️ Não Conforme | False | ✅ 100% |

### 2.3 Síntese dos Grupos Demográficos Informados
- **Total de Grupos Informados Avaliados:** 14 grupos (5 Faixa Etária + 4 Gênero + 5 Região).
- **Grupos Conformes ($\text{Ratio} \ge 0{,}80$):** **9 grupos** (64,3%).
- **Grupos Não Conformes ($\text{Ratio} < 0{,}80$):** **5 grupos** (35,7%):
  1. `faixa_etaria: 18-24` ($\text{ratio} = 0{,}7950$);
  2. `regiao: Sul` ($\text{ratio} = 0{,}5575$);
  3. `regiao: Sudeste` ($\text{ratio} = 0{,}6422$);
  4. `regiao: Centro-Oeste` ($\text{ratio} = 0{,}6993$);
  5. `regiao: Nordeste` ($\text{ratio} = 0{,}7236$).
- **Discrepâncias Encontradas:** **ZERO**. A consistência entre o recálculo independente em pandas, os valores gravados em `fairness_metrics.parquet` e as tabelas documentadas em `docs/responsible_ai.md` §3 é de **100%** (diferença máxima absoluta $< 10^{-6}$). Confirmado que o Lead corrigiu com precisão os valores de fixture anteriormente reportados.

---

## 3. [B2] ARI e Honestidade da Discussão de Segmentação

### 3.1 Recálculo Independente do ARI
O Adjusted Rand Index (ARI) foi recalculado utilizando a biblioteca canônica `sklearn.metrics.adjusted_rand_score`, cruzando os rótulos de clusterização não-supervisionada gerados em `data/analytics/segments.parquet` (`cluster_kmeans`, $K=6$) com os rótulos geradores latentes em `data/curated/ground_truth.parquet` (`latent_archetype`, 5 arquétipos):

- **ARI Reportado na Documentação:** $0,1642$ (docs/segmentation_report.md §1 e §5.3)
- **ARI Recalculado:** $\mathbf{0{,}164245}$ (arredondado para 4 casas decimais: **$0,1642$**)
- **Divergência:** $\mathbf{0{,}0000}$ (Confirmação exata).

### 3.2 Julgamento da Discussão de Honestidade Analítica (docs/segmentation_report.md §5.3)
A documentação em `docs/segmentation_report.md` §5.3 aborda diretamente a disparidade entre a meta teórica preliminar ($\text{ARI} \ge 0{,}80$) e o resultado empírico real ($\text{ARI} = 0,1642$). A discussão técnica foi julgada plenamente **honesta, rigorosa e fundamentada**, sem qualquer tentativa de maquiar ou omitir os fatos:

1. **Dormência Massiva na Base Comportamental:**
   - Auditoria empírica independente comprovou que **$28.602$ de $50.000$ clientes ($57,20\%$)** possuem frequência de voos nula (`frequency_12m == 0`) e $23.935$ ($47,87\%$) possuem gastos nulos no período pré-cutoff.
   - Entre os arquétipos latentes, a inatividade atinge $80,09\%$ dos clientes em `eventual_promocional`, $78,67\%$ em `maximizador_milhas` e $60,98\%$ em `lazer_premium`.
   - No espaço euclidiano de features observáveis, clientes inativos geram vetores idênticos ou quase indistinguíveis, tornando matematicamente impossível a separação geométrica perfeita dos arquétipos latentes apenas com o histórico transacional pré-cutoff.
2. **Separação Observável vs. Estocástica Latente:**
   - O gerador sintético (WS2) introduz perturbações estocásticas individuais ($\theta_{\text{freq}}$, $\theta_{\text{spend}}$, $\theta_{\text{churn}}$), criando sobreposições reais nas distribuições observáveis.
3. **Emergência da Persona `eventual_ascendente`:**
   - O clustering ($K=6$) identificou um grupo operacionalmente vital que não figurava como família estática única no gerador sintético: clientes em aceleração recente de frequência e acúmulo de pontos qualificáveis, próximos da meta de upgrade de categoria.
4. **Integridade Metodológica e Ética:**
   - O relatório pontua enfaticamente que variáveis latentes não foram vazadas para inflar artificialmente o ARI. O valor reflete com integridade científica a performance do agrupamento não-supervisionado.

---

## 4. [B3] Coerência e Honestidade das Personas

### 4.1 Confronto de Nomenclatura (`personas_summary.parquet` vs `config/actions.yaml`)
Foi realizado o confronto exato do inventário de personas presente em `data/analytics/personas_summary.parquet` contra os filtros de elegibilidade `personas_any` em `config/actions.yaml`.
- **Nomes em `personas_summary.parquet`:**
  1. `executivo_recorrente`
  2. `lazer_premium`
  3. `maximizador_milhas`
  4. `regional_dependente`
  5. `eventual_ascendente`
  6. `eventual_promocional`
- **Nomes em `config/actions.yaml` (`personas_any`):**
  - Exatamente as mesmas 6 chaves, com alinhamento semântico estrito a cada ação (ex.: `contato_proativo_relacionamento` elegível para `executivo_recorrente`, `regional_dependente`, `maximizador_milhas`; `antecipacao_de_nivel` para `eventual_ascendente`, `executivo_recorrente`, `maximizador_milhas`).
  - Nenhuma persona órfã ou ausente em qualquer uma das pontas.

### 4.2 Coerência dos Perfis Quantitativos
A auditoria dos microdados analíticos confirmou os parâmetros quantitativos essenciais:
- **`eventual_promocional`:**
  - Volume: $24.210$ clientes (**$48,42\%$** da base, aderente à estimativa de $\sim 48\%$).
  - Churn médio: **$73,59\%$** (probabilidade de evasão severa, refletindo inatividade).
  - CLV médio previsto: **R\$ 209,11**; Ticket médio: **R\$ 185,34**.
  - Principal atrito: `preco`.
- **`executivo_recorrente`:**
  - Volume: $1.312$ clientes (**$2,62\%$** da base, aderente à estimativa de $\sim 2,6\%$).
  - Churn médio: **$2,64\%$** (fidelidade corporativa de altíssima estabilidade).
  - CLV médio previsto: **R\$ 6.522,82** ($\sim \text{R\$}~6{,}5\text{k}$).
  - Ticket médio: **R\$ 469,17**.
  - Atritos dominantes: `atraso`, `atendimento`.
- **Demais Personas:**
  - `regional_dependente`: $9.763$ clientes ($19,53\%$), CLV R\$ 888,16, Churn $32,98\%$.
  - `eventual_ascendente`: $5.121$ clientes ($10,24\%$), CLV R\$ 2.155,46, Churn $18,17\%$.
  - `maximizador_milhas`: $4.949$ clientes ($9,90\%$), CLV R\$ 477,32, Churn $22,02\%$, Ticket R\$ 1.144,66.
  - `lazer_premium`: $4.645$ clientes ($9,29\%$), CLV R\$ 831,52, Churn $29,80\%$, Ticket R\$ 259,35.

### 4.3 Honestidade da Reconciliação Pós-Clustering
A atribuição dos nomes comerciais das personas após o agrupamento geométrico não-supervisionado (`map_centroids_to_personas` em `ml/segmentation/cluster.py`) é uma prática padrão de ciência de dados corporativa. Os centróides são associados de forma objetiva pelas dimensões comportamentais dominantes (maior share resgate $\to$ maximizador; maior recência $\to$ promocional; maior frequência $\to$ executivo; maior meta de nível $\to$ ascendente; menor rota troncal $\to$ regional). O processo é determinístico, reprodutível e totalmente documentado.

---

## 5. [B4] Validação da Linha do Tempo (Customer Timeline)

### 5.1 Volume Total e Cobertura por Cliente
- **Total de Eventos Registrados:** $282.507$ eventos.
- **Cobertura de Clientes:**
  - Clientes únicos com pelo menos 1 evento ($\ge 1$ evento): **$30.453$ clientes** ($60,91\%$ da carteira total de $50.000$).
  - Média de eventos por cliente ativo: $9{,}28$ eventos (mediana $8$, desvio padrão $7{,}13$, máximo de $80$ eventos).
  - Clientes sem eventos históricos registrados: $19.547$ clientes ($39,09\%$), coerente com o volume de clientes inativos/dormentes na base.

### 5.2 Distribuição por Tipo de Evento
A composição dos $282.507$ eventos na linha do tempo distribui-se em quatro categorias:
1. **`voo`:** $200.797$ eventos ($71,08\%$) — registros operacionais de trechos voados, pontualidade e atrasos operacionais.
2. **`resgate`:** $40.440$ eventos ($14,31\%$) — emissões de passagens com pontos Azul.
3. **`atrito`:** $34.150$ eventos ($12,09\%$) — interações de clientes com registro de atrito/reclamação por canal.
4. **`tier_change`:** $7.120$ eventos ($2,52\%$) — progressões e transições de categoria (Topázio, Safira, Diamante).

### 5.3 Auditoria Temporal e Verificação do Cutoff (`2025-08-31`)
- **Menor Data Observada (`MIN(data)`):** `2023-09-01`
- **Maior Data Observada (`MAX(data)`):** **`2025-11-29`** ⚠️
- **Contagem de Eventos $\le \text{Cutoff}$ (`2025-08-31`):** $277.705$ eventos ($98,30\%$)
- **Contagem de Eventos $> \text{Cutoff}$ (`2025-08-31`):** **$4.802$ eventos ($1,70\%$)**

#### Diagnóstico Técnico da Causa Raiz:
Ao inspecionar a implementação de `ml/segmentation/timeline.py` (linhas 36-47):
```python
# 1. Voos operados
tx_sub = transactions_df[
    (transactions_df["transaction_date"] <= cutoff_date) & transactions_df["flight_id"].notna()
].copy()

tx_flights = tx_sub.merge(
    flights_df[["flight_id", "origin_airport", "destination_airport", "departure_date", "delay_minutes", "has_delay"]],
    on="flight_id",
    how="inner",
)

for _, f in tx_flights.iterrows():
    dt_str = pd.to_datetime(f["departure_date"]).strftime("%Y-%m-%d")
    ...
    timeline_records.append({..., "data": dt_str, "tipo": "voo", ...})
```
- **Mecanismo:** A filtragem temporal filtrou `transactions_df["transaction_date"] <= cutoff_date` (passagens compradas em ou antes de 31/08/2025). No entanto, para voos futuros cuja partida estava agendada para setembro, outubro ou novembro de 2025 (`departure_date > 2025-08-31`), a data do evento registrada na timeline foi `f["departure_date"]`.
- **Efeito:** Como consequência direta, $4.802$ voos com partida entre `2025-09-01` e `2025-11-29` foram incluídos na timeline com datas futuras em relação ao cutoff. Mais grave: a descrição textual reporta o status operacional realizado do voo (ex.: *"Trecho CNF -> REC com atraso operacional de 25 min."* em `2025-09-13`), um fato que em 31/08/2025 pertencia ao futuro e não poderia ter ocorrido.
- **Classificação:** **Achado [IMPORTANTE]**. Embora `customer_timeline.parquet` não seja consumido pelo retreinamento dos modelos supervisionados (CLV e Churn usam `features_customer.parquet`), o artefato viola o contrato metodológico estrito anunciado no código e na documentação (*"apenas eventos estritamente <= cutoff (2025-08-31)"*).

---

## 6. [B5] Execução e Verificação de Testes de Fairness

### 6.1 Execução da Suíte de Testes
A suíte de testes de equidade foi executada via comando curto no ambiente virtual:
`& .venv\Scripts\python.exe -m pytest tests/test_fairness.py -q`

- **Resultado:** **3 testes executados, 3 aprovados (100% verdes em 0,44s)**.

### 6.2 Análise do Teste de Fixture Controlada (Regra 4/5)
O teste `test_four_fifths_exact_calculation_on_controlled_fixture` em `tests/test_fairness.py` implementa exatamente o cenário canônico para validação da regra dos 4/5:
- **Grupo A (Referência):** 100 clientes, 100 selecionados como alto valor ($\text{taxa} = 1{,}00$).
  - $\text{Razão} = 1{,}00 / 1{,}00 = 1{,}00 \ge 0{,}80 \implies \text{four\_fifths\_compliant} = \text{True}$.
- **Grupo B (Disparidade Adversa):** 100 clientes, 70 selecionados ($\text{taxa} = 0{,}70$).
  - $\text{Razão} = 0{,}70 / 1{,}00 = 0{,}70 < 0{,}80 \implies \text{four\_fifths\_compliant} = \text{False}$.
- **Grupo C (Conforme no Limiar Superior):** 100 clientes, 85 selecionados ($\text{taxa} = 0{,}85$).
  - $\text{Razão} = 0{,}85 / 1{,}00 = 0{,}85 \ge 0{,}80 \implies \text{four\_fifths\_compliant} = \text{True}$.

O teste existe, está implementado com rigor matemático (usando `pytest.approx`), e valida com exatidão tanto as taxas, quanto as razões relativas e os booleanos de conformidade.

### 6.3 Testes Complementares de Governança
- `test_fairness_metrics_parquet_contract`: Valida que o parquet gerado adere integralmente ao contrato formal `schemas/fairness_metrics.yaml`.
- `test_fairness_audit_identifies_disparities_honestly`: Valida que as disparidades reais (não-conformidade de Jovens 18-24 e Região Sul) são de fato expostas como `four_fifths_compliant == False`, impedindo mascaramento acidental ou deliberado.

---

## 7. Quadro Consolidado de Achados

| ID | Bloco | Item Auditado | Severidade | Descrição do Achado | Ação Recomendada |
|:---|:---|:---|:---:|:---|:---|
| **ACH-WS5B-01** | B1 | Fairness: Paridade Parquet vs Doc | **OBSERVAÇÃO** | A auditoria do Lead corrigiu a versão inicial que misturava números de fixture. A tabela persistida `fairness_metrics.parquet` e o relatório `docs/responsible_ai.md` §3 estão em perfeita consonância ($100\%$ das células batem). | Manter governança contínua no CI/CD. |
| **ACH-WS5B-02** | B1 | Fairness: Tratamento de Nulos | **OBSERVAÇÃO** | 609 nulos de faixa etária e 1.917 de gênero foram categorizados com integridade ética como `"não informado"`, sem receber rótulos factuais fictícios e sem contaminar o denominador da regra 4/5. | Nenhuma ação necessária (aderente à LGPD). |
| **ACH-WS5B-03** | B2 | ARI: Ground Truth vs Clusters | **OBSERVAÇÃO** | ARI recalculado exatamente em $0,1642$. A discussão em `docs/segmentation_report.md` §5.3 é cientificamente íntegra e contextualiza a dormência de $57,20\%$ dos clientes sem maquiar métricas. | Nenhuma ação necessária. |
| **ACH-WS5B-04** | B3 | Personas: Playbook vs Clusters | **OBSERVAÇÃO** | As 6 personas coincidem com `config/actions.yaml` e exibem perfis quantitativos coerentes com o domínio de fidelidade aéreo. | Nenhuma ação necessária. |
| **ACH-WS5B-05** | B4 | Timeline: Vazamento Temporal Pós-Cutoff | **IMPORTANTE** | `customer_timeline.parquet` possui **$4.802$ eventos de voo posteriores ao cutoff (`2025-08-31`)**, com data máxima atingindo **`2025-11-29`**. O código filtra `transactions_df["transaction_date"] <= cutoff`, mas utiliza `flights_df["departure_date"]` sem aplicar filtro de teto temporal sobre a data de partida do voo. Além disso, expõe o resultado operacional realizado de voos que ainda não haviam decolado na data de corte. | Em `ml/segmentation/timeline.py`, filtrar explicitamente `flights_df["departure_date"] <= cutoff_date` antes da inclusão na timeline ou utilizar a data da transação como timestamp do evento. |
| **ACH-WS5B-06** | B5 | Testes: Fixture 4/5 | **OBSERVAÇÃO** | Teste de unidade com taxas controladas (A: 100%, B: 70%, C: 85%) existe e valida com precisão a regra dos 80%. Suíte `test_fairness.py` passa integralmente (3/3). | Nenhuma ação necessária. |

---

## 8. Conclusão da Revisão Independente

A modelagem de equidade algorítmica (Fairness B1/B5), a segmentação não-supervisionada (ARI B2) e a parametrização das personas comerciais (B3) foram executadas com excelência técnica, rigor conceitual e integridade analítica exemplar.

Contudo, a regra estrita do protocolo de auditoria veda a emissão de aprovação sumária enquanto houver achado de severidade **IMPORTANTE** em aberto. Pelo fato de `customer_timeline.parquet` violar a asserção temporal de corte ao conter $4.802$ eventos posteriores a `2025-08-31` (atingindo `MAX(data) = 2025-11-29`), o veredito parcial da Parte B é **REPROVADO (B)** até que o Lead aplique o filtro de data de partida em `ml/segmentation/timeline.py` e regenere o artefato da linha do tempo.
