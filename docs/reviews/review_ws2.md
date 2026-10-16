# Revisão Independente Adversarial: WS2 · Gerador Sintético Calibrado

> **Data da Revisão:** 12 de outubro de 2026  
> **Revisor Independente:** Subagente Especialista em Auditoria e Qualidade de Dados (`mega-brain`)  
> **Frente Auditada:** Workstream WS2 — Gerador Sintético, Fidelidade Empírica e Isolamento de Ground Truth  
> **Protocolo:** `docs/reviews/README.md` (Ciclo de Qualidade Aura 2.0)  
> **Postura do Revisor:** Adversarial estrita — procura deliberada de falhas, recálculo independente de 100% dos agregados, verificação formal de contratos e análise de código linha por linha, sem confirmação presumida de qualquer alegação do autor.

---

## 1. Veredito Executivo

### **Veredito: REPROVADO**

**Justificativa:**  
A base sintética do WS2 demonstra alto nível de engenharia e modelagem estocástica sofisticada: atinge paridade bit a bit no determinismo com a seed 42, reproduz fielmente as 5 dimensões agregadas de mercado (Pareto top-20% = 74,66%, correlação sazonal r = 0,8958 vs ANAC, MAU/base = 10,44% dentro da tolerância, e pirâmide de tiers restrita no topo), cumpre os contratos de dados YAML e mantém o *ground truth* estritamente segregado.  

No entanto, a auditoria adversarial identificou **2 achados de severidade CRÍTICA** e **4 achados de severidade IMPORTANTE** que comprometem a integridade relacional e a modelagem temporal da fidelidade, violando o protocolo de qualidade:
1. **[CRÍTICO] Vazamento temporal no cálculo de qualificação em janela móvel (`synthetic/generate.py:361`)**: transações de cartão e clube de todo o triênio (2023–2026) são injetadas previamente em `qual_history` antes do loop de voos. A janela móvel filtra apenas o piso (`h[0] >= cutoff_365`), sem teto (`h[0] <= purchase_dt`). Comprovou-se via SQL que **1.009 eventos de fidelidade somaram pontos de transações futuras**.
2. **[CRÍTICO] Inversão semântica de downgrades rotulados como upgrades (`synthetic/generate.py:378`)**: quando um cliente perde pontuação e sofre rebaixamento de nível, o registro é emitido com `event_type = 'tier_upgrade'` (fixo no código) e gatilho `"alternative_spend_reached"`. Dos 14.192 registros da tabela `loyalty_events.parquet`, **100% estão gravados como upgrade**, apesar de **5.049 eventos serem downgrades reais** (ex.: 3.407 de Topázio para Azul, 1.363 de Safira para Topázio, 199 de Diamante para Safira).
3. **[IMPORTANTE] Desconexão relacional de expiração para clientes dormentes (`synthetic/generate.py:458-466`)**: se um cliente atinge um tier em Jan/2025 e cessa viagens, seus pontos expiram em Jan/2026, mas nenhum evento de downgrade é registrado em `loyalty_events.parquet`. No fim da simulação, seu tier é alterado diretamente para `"azul"` em `customers.parquet`, deixando a tabela de eventos sem o registro de rebaixamento.
4. **[IMPORTANTE] Exceção silenciosa em `synthetic/loyalty.py:64`**: bloco `try...except Exception: rules = {}` suprime qualquer erro de carga do YAML sem log, violando a política *fail-loud*.
5. **[IMPORTANTE] Fragilidade a valores nulos em `synthetic/loyalty.py`**: se campos como `qualifying_points` forem declarados como `null` no YAML de regras, a função dispara `TypeError` não tratado (`>=` entre `int` e `NoneType`).
6. **[IMPORTANTE] Ausência de justificativa do efeito de dormência no relatório de fidelidade (`docs/fidelity_report.md`)**: a razão MAU/Base de 10,44% é superior à do RI da Azul (6,97%), mas o relatório não formaliza que a base real de 20,1M carrega dormência acumulada de mais de 15 anos vs uma coorte sintética recente de 3 anos.

Conforme a Seção 4 do protocolo (`docs/reviews/README.md`), achados de severidade **CRÍTICO** e **IMPORTANTE** bloqueiam a aprovação da frente até correção e reavaliação.

---

## 2. Sumário de Achados por Severidade

| Severidade | Quantidade | Descrição Resumida |
|---|:---:|---|
| 🔴 **CRÍTICO** | **2** | 1. Vazamento temporal em janela móvel de qualificação (1.009 eventos de fidelidade com pontos futuros de cartão/clube).<br>2. Inversão semântica em `loyalty_events`: 5.049 downgrades rotulados como `tier_upgrade` com gatilho `"alternative_spend_reached"`. |
| 🟠 **IMPORTANTE** | **4** | 1. Clientes dormentes perdem tier em `customers` sem emissão de evento em `loyalty_events`.<br>2. `synthetic/loyalty.py:64`: `except Exception` silencioso viola *fail-loud* sem log.<br>3. `synthetic/loyalty.py`: ausência de guard contra `null` em `qualifying_points` e `segments` dispara `TypeError`.<br>4. `docs/fidelity_report.md`: ausência de justificativa explícita de dormência histórica para tolerância do MAU (10,44% vs 6,97%). |
| 🟡 **MENOR** | **3** | 1. 36.215 transações fora de ordem cronológica global em `transactions.parquet`.<br>2. `fidelity_report.md:53` declara missingness global de NPS de 58%, quando a média real ponderada na base é 49,22%.<br>3. Premissa de cancelamento de 1,8% omitida na Seção 3 de limitações do relatório de fidelidade. |
| 🔵 **OBSERVAÇÃO** | **5** | 1. Determinismo estrito de ponta a ponta: hashes SHA-256 dos 6 Parquets 100% idênticos após regeneração.<br>2. Isolamento de `ground_truth.parquet`: consumidores estritamente `evaluation_only`, zero referências em `dbt/`, `ml/`, `agent/`, `app/`.<br>3. Conformidade LGPD: sensíveis restritos a `customers.parquet` com marcação `sensitive: true`.<br>4. Anti-trivialidade comprovada: alta dispersão (CV freq 1,39, spend 1,82), AUC logística realista (0,86 e 0,62).<br>5. Suíte de testes (6/6 pass) e linter Ruff aprovados com 100% de sucesso. |

---

## 3. Checklist de Verificações Obrigatórias (12 Itens com Evidência Real)

### Item 1: Testes Automatizados e Linter
- **Comandos executados pelo revisor:**
  ```powershell
  & .venv\Scripts\python.exe -m pytest tests/test_synthetic.py -v
  & .venv\Scripts\python.exe -m ruff check synthetic
  ```
- **Saída Real Registrada:**
  ```text
  ============================= test session starts =============================
  platform win32 -- Python 3.11.0, pytest-9.1.1, pluggy-1.6.0
  rootdir: C:\Users\najort\Documents\GitHub\PROJETO AURA
  configfile: pyproject.toml
  plugins: anyio-4.15.1, typeguard-4.6.0
  collected 6 items

  tests\test_synthetic.py::test_tier_progression_constructed_cases PASSED   [ 16%]
  tests\test_synthetic.py::test_determinism_bit_by_bit PASSED              [ 33%]
  tests\test_synthetic.py::test_schema_contracts_validation PASSED         [ 50%]
  tests\test_synthetic.py::test_ground_truth_isolation PASSED             [ 66%]
  tests\test_synthetic.py::test_missing_data_mechanisms PASSED             [ 83%]
  tests\test_synthetic.py::test_fidelity_metrics_computation PASSED        [100%]

  ============================== 6 passed in 2.50s ==============================

  All checks passed!
  ```
- **Avaliação:** Conforme. 6 testes passaram e Ruff não apontou nenhuma violação de estilo ou tipagem.

---

### Item 2: Determinismo de Ponta a Ponta (Hashes Antes / Depois de `tasks.py synth`)
- **Procedimento:** Cálculo independente de hash SHA-256 de todos os 6 arquivos Parquet gerados e do marcador `_SUCCESS`, reexecução do pipeline sintético via `& .venv\Scripts\python.exe tasks.py synth` e recálculo dos hashes.
- **Evidência Registrada:**

| Arquivo | SHA-256 Antes de `tasks.py synth` | SHA-256 Depois de `tasks.py synth` | Status |
|---|---|---|:---:|
| `data/curated/synthetic/customers.parquet` | `9e62251de72fc868c635b308099a21b2ecbdadd252174ab4654839ecc6d669c5` | `9e62251de72fc868c635b308099a21b2ecbdadd252174ab4654839ecc6d669c5` | ✅ IDÊNTICO |
| `data/curated/synthetic/flights.parquet` | `c5c4fc46e51a26ec98cb30bea7a2cb5c814eb6c674d1f03c3cf83e85f614c4e8` | `c5c4fc46e51a26ec98cb30bea7a2cb5c814eb6c674d1f03c3cf83e85f614c4e8` | ✅ IDÊNTICO |
| `data/curated/synthetic/transactions.parquet` | `30e11a808a4d1853e07848363f4ce6726bafbeaeb8e480650243cf82c2fdd69d` | `30e11a808a4d1853e07848363f4ce6726bafbeaeb8e480650243cf82c2fdd69d` | ✅ IDÊNTICO |
| `data/curated/synthetic/loyalty_events.parquet` | `ad0a092dd9c6b68665df3ab611cfccc239dfd80fe9296f1be42c6a5802f0454c` | `ad0a092dd9c6b68665df3ab611cfccc239dfd80fe9296f1be42c6a5802f0454c` | ✅ IDÊNTICO |
| `data/curated/synthetic/interactions.parquet` | `140d5868064e0e89f724a8587695891e80141eb312f955fc8451e58881ddf001` | `140d5868064e0e89f724a8587695891e80141eb312f955fc8451e58881ddf001` | ✅ IDÊNTICO |
| `data/curated/ground_truth.parquet` | `445c1f381b847a36410536d781e65774209789c462404447ae40ce89972c747d` | `445c1f381b847a36410536d781e65774209789c462404447ae40ce89972c747d` | ✅ IDÊNTICO |
| `data/curated/synthetic/_SUCCESS` | `d35ae7e1c9c88fda561e2f221013c8a4ded779eacd81da4d51e92f1707736d2c` | `be6ab783c0f8070d902d67d0564a2a25d308a8925b7dc3d9bf35d50a5faf085b` | ℹ️ Modificado (timestamp UTC gerado no término) |

- **Avaliação:** Conforme. Determinismo bit a bit absoluto comprovado em todos os 6 Parquets do ecossistema.

---

### Item 3: Fidelidade Independente (Recálculo sobre os Parquets)
- **Consulta DuckDB executada pelo revisor:**
  ```python
  import duckdb, json, pandas as pd

  con = duckdb.connect()
  # Contagens, Pareto, Tiers, MAU e Sazonalidade
  ```
- **Confronto Direto entre Reportado pelo Autor vs Recalculado:**

| Dimensão / Métrica | Valor Reportado pelo Autor | Valor Recalculado Independentemente | Divergência | Status |
|---|:---:|:---:|:---:|:---:|
| **Total de Clientes** | 50.000 | 50.000 | 0,00% | ✅ Exato |
| **Total de Voos** | 216.176 | 216.176 | 0,00% | ✅ Exato |
| **Total de Transações** | 317.611 | 317.611 | 0,00% | ✅ Exato |
| **Total de Eventos de Fidelidade** | 14.192 | 14.192 | 0,00% | ✅ Exato |
| **Total de Interações** | 78.727 | 78.727 | 0,00% | ✅ Exato |
| **Total de Ground Truth** | 50.000 | 50.000 | 0,00% | ✅ Exato |
| **Pareto Top-20% (Lifetime)** | 74,66% | **74,6613%** | 0,00% | ✅ Exato |
| **Pareto Top-20% (Janela Alvo 12m)** | Não citado no consolidado | **82,5816%** | — | ℹ️ Concentração alta |
| **Tier: Azul** | 95,59% | **95,5940%** (47.797 clientes) | 0,00% | ✅ Exato |
| **Tier: Topázio** | 3,17% (~3,2%) | **3,1720%** (1.586 clientes) | 0,00% | ✅ Exato |
| **Tier: Safira** | 1,08% (~1,1%) | **1,0800%** (540 clientes) | 0,00% | ✅ Exato |
| **Tier: Diamante** | 0,15% | **0,1500%** (75 clientes) | 0,00% | ✅ Exato |
| **Tier: Diamante Unique** | 0,00% (~0,004%) | **0,0040%** (2 clientes) | 0,00% | ✅ Exato |
| **MAU / Base Mensal Médio** | 10,44% | **10,4383%** (5.219,17 MAU) | 0,00% | ✅ Exato |
| **Correlação Sazonal vs ANAC** | r = 0,8958 | **r = 0,895839** | 0,00% | ✅ Exato |

- **Avaliação:** Conforme. Divergência de 0,00% em todos os números analíticos reportados.

---

### Item 4: Regras do Programa de Fidelidade (Casos Construídos e Recência)
- **Script executado para teste de limites de `evaluate_tier`:**
  ```python
  from synthetic.loyalty import evaluate_tier

  assert evaluate_tier(6000, 6, 0.0) == "topazio"
  assert (
      evaluate_tier(12000, 11, 24000.0) == "safira"
  )  # NÃO Diamante (exige 12 trechos E 12k QP ou R$ 25k)
  assert evaluate_tier(0, 0, 25000.0) == "diamante"  # Gasto alternativo
  assert evaluate_tier(26000, 25, 49000.0) == "diamante"  # NÃO Unique (falta 1 trecho)
  assert evaluate_tier(26000, 26, 0.0) == "diamante_unique"  # Unique por trechos + QP
  assert evaluate_tier(0, 0, 50000.0) == "diamante_unique"  # Unique por gasto direto
  ```
- **Resultados e Vulnerabilidades Detectadas:**
  1. **Casos construídos:** A lógica pura de `evaluate_tier()` implementa corretamente as condições OR (Topázio, Safira) e AND com gasto alternativo (Diamante, Unique).
  2. **Vulnerabilidade a Nulos (`null fail-safe`):** Caso um atributo do YAML contenha `null` (como `qualifying_points: null`), a linha `du_qual.get("qualifying_points", 26000)` retorna `None`, disparando `TypeError: '>=' not supported between instances of 'int' and 'NoneType'`.
  3. **Vazamento Temporal e Inversão de Downgrades:** A auditoria em `synthetic/generate.py:361-388` revelou que a emissão de eventos em janela móvel vaza pontos futuros de cartão e rotula 5.049 downgrades como `tier_upgrade`.
  4. **Expiração em Clientes Dormentes:** Clientes que param de voar perdem o status ao final da simulação em `customers.parquet`, mas nenhum evento de rebaixamento ou expiração é registrado em `loyalty_events.parquet`.
- **Avaliação:** **NÃO CONFORME**. (Achados Críticos e Importantes detalhados na Seção 4).

---

### Item 5: Segregação Estrita do Ground Truth
- **Auditoria de Contrato:**
  `schemas/ground_truth.yaml` linha 5:
  ```yaml
  consumers: [evaluation_only]
  ```
- **Auditoria Estática de Código (Grep de Consumo):**
  - Pastas `ml/`, `dbt/`, `agent/`, `app/` foram inspecionadas à procura de referências a `ground_truth.parquet`.
  - Nenhuma leitura direta encontrada. A única ocorrência em `ml/` foi uma chave de dicionário `"kappa_vs_ground_truth"` em `ml/sentiment/approaches.py:632` comparando anotações manuais.
- **Auditoria de dbt Staging:**
  `dbt/models/staging/sources.yml` declara apenas:
  - `customers`
  - `flights`
  - `transactions`
  - `interactions`
  - **`ground_truth` está ausente do dbt**, comprovando isolamento analítico.
- **Avaliação:** Conforme. Isolamento do ground truth cumpre 100% o plano mestre.

---

### Item 6: Anti-Trivialidade e Heterogeneidade da População
- **Métricas Estatísticas Computadas pelo Revisor (DuckDB + Scipy + Scikit-Learn):**
  - **Frequência de voos (Passagens voadas por cliente):**
    - Média: 4,32 voos | Desvio Padrão: 6,01 voos | **Coeficiente de Variação (CV): 1,39**
    - Mediana: 3,0 voos | Percentil 75: 6,0 | Percentil 95: 15,0 | Máximo: 57 voos.
  - **Gasto monetário acumulado (BRL):**
    - Média: R$ 2.061,33 | Desvio Padrão: R$ 3.759,93 | **Coeficiente de Variação (CV): 1,82**
    - Mediana: R$ 595,52 | Percentil 75: R$ 2.420,57 | Percentil 95: R$ 9.125,71 | Máximo: R$ 64.827,71.
  - **Correlação Latente Frequência × Gasto:**
    - Correlação empírica entre os efeitos aleatórios latentes: **r = 0,5174** (premissa de configuração: `0,52`).
    - Correlação linear observada freq × gasto total: **r = 0,8828** (esperado pelo efeito aditivo de passagens).
    - Correlação freq × ticket médio por voo: **r = 0,1635**.
  - **Dinâmica e Separabilidade de Churn:**
    - Taxa de churn observado (inatividade > 180d e > 2x intervalo típico no alvo 12m): **41,42%**.
    - Taxa de disparo estocástico do hazard latente (Cox process): **20,68%**.
    - Teste de separabilidade ingênua (Regressão Logística in-sample nas variáveis base):
      - AUC para Churn Observado: **0,8639** (Brier Score: 0,1526).
      - AUC para Churn Latente: **0,6163**.
- **Avaliação:** Conforme. A base possui heterogeneidade severa e sobreposição realista. Não há separação trivial (AUC longe de 1,000), garantindo desafio metodológico crível para os modelos de ML em WS4/WS5.

---

### Item 7: Mecanismos Formais de Dados Faltantes (MAR e MCAR)
- **Recálculo Independente de Missingness:**
  - **NPS em Interações (MAR):**
    - Total de interações: 78.727
    - Sem atrito (`has_friction = 0`, N=24.291): Taxa de Missing NPS = **69,82%**
    - Com atrito (`has_friction = 1`, N=54.436): Taxa de Missing NPS = **40,03%**
    - Diferencial de resposta por atrito: **+29,79 p.p.**
    - Teste Qui-Quadrado de Independência: $\chi^2 = 5962,49$, **$p < 0,000001$**.
  - **Dados Demográficos Cadastrais (MCAR):**
    - `faixa_etaria`: Taxa de Missing = **1,22%** (config: 1,2% / 0,012). Teste vs arquétipo: $\chi^2 = 2,79, p = 0,5939$ (não correlacionado com arquétipo $\rightarrow$ MCAR suportado).
    - `genero`: Taxa de Missing = **3,83%** (config: 3,8% / 0,038). Teste vs arquétipo: $\chi^2 = 4,49, p = 0,3434$ (não correlacionado com arquétipo $\rightarrow$ MCAR suportado).
- **Avaliação:** Conforme. Os mecanismos estocásticos MAR e MCAR estão implementados com rigor matemático comprovado.

---

### Item 8: Contratos de Dados e Validação Adversarial
- **Validação Oficial dos 6 Parquets com `validate_or_raise`:**
  - `synthetic_customers`: 0 violações (Aprovado).
  - `synthetic_flights`: 0 violações (Aprovado).
  - `synthetic_transactions`: 0 violações (Aprovado).
  - `synthetic_loyalty_events`: 0 violações (Aprovado).
  - `synthetic_interactions`: 0 violações (Aprovado).
  - `ground_truth`: 0 violações (Aprovado).
- **Injeção Adversarial de Anomalias em Cópias Temporárias:**
  - Injeção 1 (valor fora de domínio em `current_tier = 'super_ouro_invalido'`): Capturado com sucesso (`allowed_values`).
  - Injeção 2 (nulo injetado em `customer_id`): Capturado com sucesso (`nullable: false` e `non_null`).
  - Injeção 3 (dtype `string` injetado na coluna `clv_real_12m` em `ground_truth`): Capturado com sucesso (`dtype float`).
- **Verificação do Marcador `_SUCCESS`:**
  - Arquivo: `data/curated/synthetic/_SUCCESS`
  - Conteúdo verificado:
    ```json
    {
      "timestamp": "2026-10-12T07:03:02.394512+00:00",
      "seed": 42,
      "n_customers": 50000,
      "status": "ready"
    }
    ```
- **Avaliação:** Conforme.

---

### Item 9: Atividade × Relações com Investidores (RI da Azul)
- **Métricas:**
  - Escala real do Azul Fidelidade (RI 2025): 20,1 milhões de cadastrados e 1,4 milhão de MAU $\rightarrow$ **6,97%**.
  - Observado na População Sintética: **10,44%** de MAU / Base Total.
  - Intervalo de Tolerância Declarado: `[4,5%, 11,0%]`.
- **Análise Crítica:**  
  O valor observado de 10,44% situa-se dentro da faixa de tolerância declarada. Contudo, a explicação técnica para o desvio positivo em relação aos 6,97% reside no fato de que os 20,1M de cadastros reais da Azul representam mais de 15 anos de história acumulada (incluindo milhões de cadastros dormentes que nunca voaram recentemente), enquanto a amostra sintética de 50.000 clientes simula uma coorte ativa/recente (adesões entre 2018 e 2025). Essa justificativa é perfeitamente plausível, mas **não foi explicitada formalmente em `docs/fidelity_report.md`**, figurando como achado IMPORTANTE de documentação.
- **Avaliação:** Conforme nos dados, com ressalva documental.

---

### Item 10: Honestidade Metodológica e Rotulagem de Premissas
- **Conferência de Premissas em `config/generator.yaml`:**
  - 16 blocos comportamentais explicitamente rotulados com a tag `# premise: ...` (arquétipos, elasticidades, covariâncias latentes, sazonalidade, missingness MAR/MNAR, yield de tarifa, atenuação de churn).
- **Declaração de Limitações em `docs/fidelity_report.md`:**
  - Declarado: bloqueio CAPTCHA para tarifas da ANAC e uso de yield parametrizado (R$ 0,48/km).
  - Declarado: validação de pipeline vs verdade de mundo real.
  - Declarado: viés de auto-seleção MAR em NPS.
  - **Omissão identificada:** A premissa de cancelamento de voos em 1,8% (necessária porque a base bruta local da ANAC não traz voos cancelados) consta em `calibration_values.json` e `limitations.md`, mas foi omitida no texto de limitações do `fidelity_report.md`.
- **Avaliação:** Parcialmente conforme (Achado MENOR de documentação).

---

### Item 11: Governança LGPD e Atributos Sensíveis
- **Verificação de Isolamento:**
  - Atributos demográficos (`faixa_etaria`, `genero`, `regiao`) existem unicamente em `customers.parquet`.
  - Schema `schemas/synthetic_customers.yaml` marca formalmente as 3 colunas com `sensitive: true`.
  - Tabelas operacionais e transacionais (`flights`, `transactions`, `interactions`, `loyalty_events`, `ground_truth`) **NÃO carregam nenhum desses atributos**.
  - Nenhuma coluna sensível foi propagada indevidamente para a camada analítica ou de modelagem.
- **Avaliação:** Conforme.

---

### Item 12: Princípio Fail-Loud e Tratamento de Exceções
- **Grep de `except` em todo o módulo `synthetic/`:**
  - Ocorrência 1 (`synthetic/generate.py:70`):
    ```python
    except Exception as e:
        log.warning("Falha ao decodificar calibration_values.json: %s", e)
    ```
    Emite warning e cai para default catalog. Aceitável.
  - Ocorrência 2 (`synthetic/churn.py:33`):
    ```python
    except Exception as e:
        log.warning("Falha ao ler friction_weights.json (%s); recorrendo à premissa", e)
    ```
    Emite warning e loga utilização de premissa. Aceitável.
  - Ocorrência 3 (`synthetic/loyalty.py:64`):
    ```python
    if rules is None:
        try:
            rules = program_rules()
        except Exception:
            rules = {}
    ```
    **Silêncio absoluto:** não há log, warning ou re-raise. Se `program_rules.yaml` falhar na leitura, o código cai silenciosamente para dicionário vazio e usa fallbacks fixos.
- **Avaliação:** **NÃO CONFORME**. (Achado IMPORTANTE).

---

## 4. Detalhamento dos Achados

### 🔴 ACHADO CRÍTICO 1: Vazamento Temporal em Janela Móvel de Qualificação
- **Arquivo / Linha:** `synthetic/generate.py:361` (originado em `synthetic/generate.py:220-246`)
- **Evidência:**  
  No arquivo `synthetic/generate.py`, as transações de acúmulo de cartão/clube são sorteadas previamente para todo o período da simulação (2023 a 2026) e adicionadas à lista `qual_history`:
  ```python
  # Linhas 223-246
  partner_offsets = np.sort(rng.integers(0, avail_days, size=n_partner_events))
  for p_off in partner_offsets:
      p_date = dt.datetime.combine(...)
      pts_card = ...
      qp_card = ...
      qual_history.append((p_date, qp_card, 0, 0.0))
  ```
  Posteriormente, dentro do loop de voos do cliente, ao comprar uma passagem na data `purchase_dt`, a janela móvel de 365 dias é calculada na linha 361:
  ```python
  # Linha 360-361
  cutoff_365 = purchase_dt - dt.timedelta(days=365)
  recent_act = [h for h in qual_history if h[0] >= cutoff_365]
  ```
  **Falha:** O filtro impõe apenas `h[0] >= cutoff_365`, omitindo a restrição superior `and h[0] <= purchase_dt`. Como `qual_history` já continha transações de cartão que só ocorreriam no futuro (até 2026), essas transações futuras foram somadas retroativamente no cálculo de qualificação na data `purchase_dt`.
- **Impacto Comprovado via SQL:**  
  Consulta direta sobre `loyalty_events.parquet` cruzando com transações posteriores de cartão revelou **1.009 eventos de fidelidade contaminados por transações futuras**:
  ```sql
  -- Exemplo detectado: Evento EV0000525 (Cliente C001845) em 2025-10-07 12:18:00
  -- Contabilizou 200 QP de cartão que só foram acumulados após essa data.
  ```
- **Recomendação de Correção:**  
  Corrigir a linha 361 para:
  ```python
  recent_act = [h for h in qual_history if cutoff_365 <= h[0] <= purchase_dt]
  ```

---

### 🔴 ACHADO CRÍTICO 2: Inversão Semântica de Downgrades Rotulados como Upgrades
- **Arquivo / Linha:** `synthetic/generate.py:366-388`
- **Evidência:**  
  No bloco de avaliação de tier durante o voo:
  ```python
  new_tier = evaluate_tier(qp_rolling, segs_rolling, spend_rolling, rules_cfg)
  if new_tier != current_tier:
      trigger = "qualifying_points_reached" if qp_rolling >= 6000 else "alternative_spend_reached"
      events_records.append(
          create_loyalty_event(
              event_seq,
              cid,
              purchase_dt,
              "tier_upgrade",  # <--- HARDCODED COMO UPGRADE INCONDICIONALMENTE!
              current_tier,
              new_tier,
              trigger,
              qp_rolling,
              segs_rolling,
              spend_rolling,
          )
      )
  ```
- **Impacto Comprovado via SQL:**  
  Ao auditar `data/curated/synthetic/loyalty_events.parquet`:
  1. `SELECT event_type, COUNT(*) FROM loyalty_events` retornou unicamente `[('tier_upgrade', 14192)]`.
  2. No entanto, o cruzamento de transição de tiers comprovou que **5.049 eventos são rebaixamentos (downgrades)**:
     - `topazio` $\rightarrow$ `azul`: 3.407 eventos
     - `safira` $\rightarrow$ `topazio`: 1.363 eventos
     - `diamante` $\rightarrow$ `safira`: 199 eventos
     - `safira` $\rightarrow$ `azul`: 65 eventos
     - `diamante` $\rightarrow$ `topazio`: 14 eventos
     - `diamante` $\rightarrow$ `azul`: 1 evento
  3. Além disso, quando ocorre rebaixamento, como `qp_rolling < 6000`, a linha 371 rotula o gatilho como `"alternative_spend_reached"`, gerando uma mentira semântica na base de dados (o cliente caiu de categoria e o log diz que ele alcançou gasto alternativo).
- **Recomendação de Correção:**  
  Comparar `TIER_ORDER[new_tier]` com `TIER_ORDER[current_tier]`. Se for menor, gravar `event_type = "tier_downgrade"` e `trigger_reason = "qualification_cycle_expired"`. Se for maior, gravar `event_type = "tier_upgrade"`.

---

### 🟠 ACHADO IMPORTANTE 1: Clientes Dormentes sem Registro de Expiração em `loyalty_events`
- **Arquivo / Linha:** `synthetic/generate.py:458-466`
- **Evidência:**  
  O gerador avalia alterações de tier apenas dentro do loop de voos do cliente (`for dep_date_d in flight_dates_sampled:`). Se um cliente viaja e qualifica Safira em Jan/2025, mas depois para completamente de voar, os 365 dias passam e nenhuma linha de código é executada para ele. Na finalização da simulação (linhas 458-466), o tier do cliente é reavaliado e atualizado diretamente para `"azul"` em `customers.parquet`, mas **nenhum evento de fidelidade é emitido em `loyalty_events.parquet`**.
- **Impacto:** Desconexão relacional: existem clientes que terminaram a simulação como `"azul"` em `customers`, mas cujo histórico em `loyalty_events` encerrou com upgrade para `"safira"`, sem nenhum registro informando quando ou por que o cliente perdeu a categoria.
- **Recomendação:** Ao atualizar os tiers finais no encerramento da simulação, emitir eventos de `"tier_downgrade"` com data de expiração para clientes que decaíram de categoria durante a dormência.

---

### 🟠 ACHADO IMPORTANTE 2: Captura Silenciosa de Exceção em `synthetic/loyalty.py`
- **Arquivo / Linha:** `synthetic/loyalty.py:62-66`
- **Evidência:**  
  ```python
  if rules is None:
      try:
          rules = program_rules()
      except Exception:
          rules = {}
  ```
- **Impacto:** Violação direta da diretriz de engenharia *fail-loud*. Se o arquivo `program_rules.yaml` estiver corrompido ou ausente, a função silencia a falha sem emitir aviso e recorre aos valores padrão embutidos no código.
- **Recomendação:** Adicionar `log.warning("Falha ao carregar program_rules: %s. Utilizando defaults", e)` ou permitir que a exceção suba caso as regras sejam mandatórias.

---

### 🟠 ACHADO IMPORTANTE 3: Fragilidade a Valores Nulos em Critérios de Pontos
- **Arquivo / Linha:** `synthetic/loyalty.py:72, 83, 94, 102`
- **Evidência:**  
  A verificação de `alternative_spend_brl` checa explicitamente `du_alt is not None`. No entanto, para `qualifying_points` e `segments`, o código faz `du_qp = du_qual.get("qualifying_points", 26000)`. Se a chave existir no YAML com valor nulo (`qualifying_points: null`), o `.get()` retorna `None`. Ao avaliar `qualifying_points >= du_qp`, o Python dispara `TypeError`.
- **Recomendação:** Utilizar operador de coalescência ou guard `du_qp is not None and qualifying_points >= du_qp`.

---

### 🟠 ACHADO IMPORTANTE 4: Ausência de Justificativa de Dormência no Relatório de Fidelidade
- **Arquivo / Linha:** `docs/fidelity_report.md:24-28`
- **Evidência:**  
  O relatório indica que o MAU observado foi de 10,44% vs 6,97% do RI da Azul (tolerância `[4,5%, 11,0%]`). Porém, não explica por que o valor observado é ~3,5 p.p. superior à referência pública.
- **Recomendação:** Incluir parágrafo formal explicando que a base real de 20,1M do RI acumula cadastros dormentes desde a fundação da companhia em 2008, enquanto a base sintética reflete um recorte recente de 36 meses, justificando tecnicamente a tolerância até 11,0%.

---

### 🟡 ACHADOS MENORES E OBSERVAÇÕES
- **Menor 1 (`synthetic/generate.py:507`):** Transações não estão ordenadas globalmente por data (36.215 transações fora de sequência temporal global). Recomenda-se ordenar `transactions_df = transactions_df.sort_values("transaction_date").reset_index(drop=True)` antes de salvar.
- **Menor 2 (`docs/fidelity_report.md:53`):** Citação textual de "omissão intencional de 58% em NPS", enquanto o percentual medido no parquet foi de 49,22% devido à predominância de interações com atrito na base gerada.
- **Menor 3 (`docs/fidelity_report.md:49-53`):** Seção de limitações omitiu a premissa de cancelamento de 1,8%.

---

## 5. Recomendações e Plano de Ação para o Lead

Para que a frente WS2 seja aprovada em reavaliação, o Lead deve aplicar as seguintes correções pontuais:

1. **Corrigir o filtro de janela móvel em `synthetic/generate.py:361`:**  
   Assegurar que `recent_act = [h for h in qual_history if cutoff_365 <= h[0] <= purchase_dt]`, eliminando o vazamento temporal de transações futuras de cartão/clube.
2. **Implementar semântica correta de `tier_downgrade` em `synthetic/generate.py:366-388`:**  
   Distinguir se `TIER_ORDER[new_tier] < TIER_ORDER[current_tier]` para emitir `"tier_downgrade"` e rotular o gatilho como `"qualification_cycle_expired"`.
3. **Emitir eventos de downgrade para clientes dormentes em `synthetic/generate.py:458-466`:**  
   Garantir integridade relacional entre `customers.parquet` e `loyalty_events.parquet`.
4. **Ordenar `transactions_df` por `transaction_date` antes da gravação Parquet.**
5. **Remover o bare except silencioso em `synthetic/loyalty.py:64` e adicionar guard de nulo.**
6. **Atualizar `docs/fidelity_report.md`** alinhando o texto de dormência e a taxa exata de missingness de NPS.
7. **Regenerar a base via `python tasks.py synth` e submeter para reavaliação.**
