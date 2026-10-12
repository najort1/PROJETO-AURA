# Projeto Aura 2.0 — Relatório Oficial de Calibração com Fontes Públicas

> ⚠️ **ARTEFATO GERADO AUTOMATICAMENTE POR `ingestion/render_calibration.py`**
> **Data de geração:** 2026-10-12 12:48:51 UTC  
> **Contrato de origem:** `config/calibration_map.yaml`  
> **Valores medidos:** `data/curated/calibration_values.json`  
> **Regra de ouro:** nenhum número inventado; limitações de granularidade e cobertura declaradas abertamente.

---

## 1. Visão Geral da Calibração

O pipeline do Projeto Aura 2.0 calibra o ambiente sintético de simulação e retenção do Azul Fidelidade ancorando-se em microdados públicos governamentais (ANAC) e fatos societários auditados da Azul S.A. (RI e SEC). A premissa metodológica fundamental é que agregados macro (demanda por rota, sazonalidade, pontualidade do sistema, escala do programa e geografia) são **medidos diretamente da realidade**, enquanto o comportamento individual é modelado como processo estocástico latente parametrizado.

### Destaques Numéricos Observados (Valores Reais Medidos)

- **Janela temporal analisada de voos:** `2023-09` a `2026-08` (36 meses).
- **Passageiros pagos no mercado doméstico regular:** **7,993,034 passageiros/mês típico** (287,749,212 no período).
- **Passageiros pagos transportados pela Azul:** **2,377,790 passageiros/mês** (85,600,440 no período; market share médio de ~29.75%).
- **Malha aérea doméstica ativa:** **1,771 rotas regulares** observadas, das quais a Azul opera em **1,097 rotas** (61.9% de capilaridade).
- **Aeródromos catalogados e comerciais:** **4,394 aeródromos** no Brasil; **222 aeroportos com tráfego comercial registrado** (regular e não regular — inclui charters/táxi aéreo); com filtro estrito de linha regular (`cd_tipo_linha='N'`, `cd_di in ('0','4')`): **188 aeródromos de origem**.
- **Taxa média de atraso (>15 min) do sistema:** **16.75%** (baseada em 11,663,750 movimentos operacionais de 2019 a 2025).
- **Taxa de cancelamento local:** declarada formalmente como **não computável localmente** (apenas etapas voadas presentes nas bases abertas da ANAC).

---

## 2. Matriz Consolidada de Parâmetros vs. Fontes e Status

| ID do Parâmetro | Descrição | Fonte Primária | Status | Valor / Síntese | Limitação Declarada |
|---|---|---|---|---|---|
| `market.route_inventory` | Malha de rotas domésticas | ANAC voos_basica (local) | `verified_local` | 1771 rotas (1097 Azul) | Apenas rotas regulares com decolagens > 0 |
| `market.volume_by_route_month` | Demanda mensal de passageiros | ANAC voos_basica (local) | `verified_local` | Média 7,993,034 pax/mês | Janela 2023-09 a 2026-08 |
| `market.seasonality_by_route` | Índices sazonais mensais | ANAC voos_basica (local) | `verified_local` | 12 índices (pico jul: 1.077, vale fev: 0.894) | Normalizado com média 1.0 |
| `market.delay_rate_by_route` | Taxa de atraso (>15 min) | ANAC movimentacao (local) | `verified_local` | Média nacional: 16.75% | Granularidade nacional (nr_aeroporto nulo na ANAC); 2026 indisponível |
| `market.cancellation_rate_by_route` | Taxa de cancelamento | ANAC voos_basica / movimentacao | `pending` / não computável | `null` (não disponível localmente) | Bases locais registram apenas etapas voadas e calços executados |
| `market.airport_inventory` | Aeródromos e macrorregiões | ANAC aerodromos + voos_basica | `verified_local` | 4394 pistas (222 com tráfego comercial, 188 estritamente regulares) | Derivação geográfica UF→Região com enriquecimento |
| `pricing.fare_distribution_by_route` | Tarifa por rota e mês | ANAC microdados de tarifas | `pending` | Parametrizada em generator.yaml | Portal ANAC bloqueado por CAPTCHA |
| `program_scale.total_members` | Base de membros cadastrados | Azul RI / SEC Form 20-F (2025) | `verified_research` | 20.100.000 membros (dez/2025) | Fato auditado corporativo |
| `program_scale.monthly_active_members` | Membros ativos por mês | Azul RI (2025) | `verified_research` | ~1.400.000 MAU | Fato auditado corporativo |
| `program_rules.tiers` | Níveis, acúmulo, tetos de resgate | config/program_rules.yaml | `verified_research` | 4 tiers ordinais + Azul One | Captura direta do site bloqueada (HTTP 403) |
| `frictions.aspect_weights` | Pesos de atrito (atraso, bagagem) | ml/sentiment (corpus rotulado) | `derived_synthetic` | 7 aspectos analisados | Validação de pipeline, não prevalência real |
| `behavior.*` | Frequência, sensibilidade a preço | config/generator.yaml | `premise` | Premissas calibradas por Pareto/RFM | Comportamento individual latente |

---

## 3. Detalhamento dos Parâmetros Locais Computados (ANAC)

### 3.1 `market.route_inventory` (Inventário de Rotas)
- **Regra de extração:** Registros de `voos_basica` na janela 2023-09 a 2026-08 com classificador `cd_tipo_linha = 'N'` (doméstica mista de passageiros) e `cd_di IN ('0', '4')` (voos regulares planejados e inclusões autorizadas em HOTRAN).
- **Total de rotas ativas:** 1,771.
- **Rotas com presença da Azul (`sg_empresa_icao = 'AZU'`):** 1,097.

#### Top 10 Rotas por Demanda de Passageiros no Período
| Rota (Origem-Destino) | Aeródromos | Total Passageiros Pagos | Passageiros Azul | Market Share Azul | Decolagens Totais |
|---|---|---|---|---|---|
| `SBSP-SBRJ` | SBSP → SBRJ | 5,830,992 | 939,621 | 16.1% | 54,067 |
| `SBRJ-SBSP` | SBRJ → SBSP | 5,824,857 | 922,084 | 15.8% | 53,909 |
| `SBBR-SBSP` | SBBR → SBSP | 3,462,593 | 511,191 | 14.8% | 26,292 |
| `SBSP-SBBR` | SBSP → SBBR | 3,417,057 | 497,603 | 14.6% | 26,486 |
| `SBCF-SBSP` | SBCF → SBSP | 3,035,760 | 837,263 | 27.6% | 24,759 |
| `SBSP-SBCF` | SBSP → SBCF | 3,000,051 | 809,893 | 27.0% | 24,825 |
| `SBGR-SBRF` | SBGR → SBRF | 2,744,197 | 1,062,059 | 38.7% | 16,002 |
| `SBRF-SBGR` | SBRF → SBGR | 2,739,728 | 1,063,327 | 38.8% | 15,944 |
| `SBPA-SBSP` | SBPA → SBSP | 2,596,523 | 484,547 | 18.7% | 19,562 |
| `SBSP-SBPA` | SBSP → SBPA | 2,573,682 | 465,634 | 18.1% | 19,738 |

### 3.2 `market.volume_by_route_month` (Demanda Mensal)
- **Volume total de passageiros regulares:** 287,749,212 passageiros.
- **Volume total Azul:** 85,600,440 passageiros.
- **Média mensal de mercado:** 7,993,034 pax/mês.
- **Média mensal Azul:** 2,377,790 pax/mês.

### 3.3 `market.seasonality_by_route` (Sazonalidade Mensal)
A sazonalidade do tráfego aéreo brasileiro reflete as férias de inverno (julho), pico de verão e festas (dezembro/janeiro) e a queda pós-carnaval (fevereiro):

| Mês Calendário | Nome | Índice de Sazonalidade | Comportamento Típico |
|---|---|---|---|
| 01 | Janeiro | **1.036** | Alta temporada (verão) |
| 02 | Fevereiro | **0.894** | Mês de menor movimento |
| 03 | Março | **0.988** | Média de baixa/média temporada |
| 04 | Abril | **0.960** | Média de baixa/média temporada |
| 05 | Maio | **0.983** | Média de baixa/média temporada |
| 06 | Junho | **0.979** | Média de baixa/média temporada |
| 07 | Julho | **1.077** | Pico anual (férias escolares) |
| 08 | Agosto | **1.058** | Média de baixa/média temporada |
| 09 | Setembro | **0.983** | Média de baixa/média temporada |
| 10 | Outubro | **1.018** | Média de baixa/média temporada |
| 11 | Novembro | **0.996** | Média de baixa/média temporada |
| 12 | Dezembro | **1.029** | Alta temporada (verão) |

### 3.4 `market.delay_rate_by_route` (Taxa de Atraso Operacional)
- **Fonte:** Série histórica `movimentacao` da ANAC (11.737.280 registros avaliados).
- **Critério de atraso:** `(dt_calco || hh_calco) - (dt_previsto || hh_previsto) > 15 minutos` (900 segundos).
- **Taxa de atraso média global do sistema:** **16.75%**.
- **Janela de cobertura disponível:** 2019-03 a 2025-12 (82 meses).
- **Limitações e transparência metodológica:**
  1. **Ausência de identificador de aeroporto:** na base pública bruta de `movimentacao` da ANAC, a coluna `nr_aeroporto_referencia` está **100% nula** (zero registros preenchidos em todos os 82 arquivos). Portanto, a taxa foi computada e calibrada para o sistema aéreo nacional por mês, sem fabricação sintética de códigos de aeroportos inexistentes na fonte.
  2. **Ausência do ano de 2026 em movimentação:** enquanto `voos_basica` possui registros até 2026-08, os microdados operacionais de `movimentacao` encerram-se em dezembro de 2025. O gerador sintético utiliza a média sazonal mensal observada para projetar 2026.

### 3.5 `market.cancellation_rate_by_route` (Taxa de Cancelamento)
- **Status:** `not_computable_local` (`value: null`).
- **Limitação declarada:**
  - A tabela `voos_basica` é composta exclusivamente por **etapas voadas** (`nr_decolagem = 1.0`). Os únicos registros com `nr_decolagem = 0.0` são artefatos técnicos de perna duplicada (`cd_di = 'D'`). Não existem campos de status de cancelamento, código de cancelamento ou justificativa.
  - A tabela `movimentacao` registra apenas aeronaves que efetivamente tocaram solo ou calçaram nos aeroportos.
  - O histórico de cancelamentos de voos (VRA da ANAC) é publicado em repositório distinto protegido por CAPTCHA. Em conformidade estrita com o princípio da **honestidade e anti-adulteração**, essa métrica não é inventada localmente.

### 3.6 `market.airport_inventory` (Aeródromos e Distribuição Regional)
- **Total de aeródromos catalogados:** 4,394.
- **Aeroportos com tráfego comercial registrado:** 222 (inclui operação não regular, ex.: charters/táxi aéreo; com filtro estrito de linha regular: 188 aeródromos de origem).
- **Distribuição de aeródromos comerciais por macrorregião:**
  - **Sudeste:** 60 aeroportos
  - **Norte:** 55 aeroportos
  - **Nordeste:** 49 aeroportos
  - **Sul:** 36 aeroportos
  - **Centro-Oeste:** 22 aeroportos

---

## 4. Parâmetros Externos Verificados por Pesquisa

### 4.1 Escala do Programa (`program_scale.*`)
- **Total de membros cadastrados:** **20.100.000 membros** em 31/12/2025 (Fonte: Demonstrações Financeiras e Form 20-F da Azul S.A. arquivado na SEC em 2026).
- **Membros ativos por mês (MAU):** **~1.400.000 membros ativos/mês** (Fonte: Apresentações de Relações com Investidores da Azul, 2025).
- **Uso no projeto:** calibra o tamanho da amostragem do gerador sintético (50.000 membros) como representação fiel e proporcional da carteira real.

### 4.2 Regras do Azul Fidelidade (`program_rules.tiers`)
- Snapshot versionado em `config/program_rules.yaml` (`snapshot_version: research-2026-10-12`).
- Estrutura oficial confirmada: **4 níveis ordinais** (`Azul`, `Topázio`, `Safira`, `Diamante`) + grupo de convite (`Azul One`).
- Regras de acúmulo (1, 2, 3 e 4 pontos por R$ gasto em tarifa), validade de pontos (2, 3, 4 anos e ilimitada), tetos de resgate e cotas de beneficiários (5, 6, 8, 10) plenamente incorporadas ao motor de elegibilidade e RAG.

---

## 5. Parâmetros com Bloqueio Externo e Fallback Declarado

### 5.1 `pricing.fare_distribution_by_route`
- **Status:** `pending` (Bloqueio externo).
- **Evidência do bloqueio:** O Portal de Dados Abertos da ANAC para tarifas comercializadas implementou CAPTCHA de segurança (Cloudflare/reCAPTCHA), inviabilizando download automatizado via script durante a sessão.
- **Fallback seguro:** O gerador sintético utiliza a premissa de pricing em `config/generator.yaml`, calculando tarifa base em função da distância em km da rota (extraída de `voos_basica`) com dispersão log-normal declarada.

---

## 6. Trilha de Auditoria e Conformidade Legal

1. **Licenciamento de dados da ANAC:**
   - Portal institucional declara licença **Creative Commons Atribuição-SemDerivações 3.0 Não Adaptada (CC BY-ND 3.0)**.
   - Fundamento jurídico federal: **Decreto nº 8.777/2016** (Política de Dados Abertos do Poder Executivo federal) e **Lei nº 12.527/2011** (Lei de Acesso à Informação).
   - O Projeto Aura utiliza os microdados para cálculo de agregados analíticos estatísticos e calibração de modelos, sem redistribuição de bases adulteradas.
2. **Privacidade e LGPD:**
   - Nenhuma tabela ANAC utilizada contém CPF, nome de passageiro ou dados pessoais (apenas prefixos de aeronaves e códigos operacionais de voos).
   - A base analítica do Projeto Aura 2.0 é **100% sintética**, garantindo conformidade irrestrita com a Lei Geral de Proteção de Dados (Lei nº 13.709/2018).
