# Relatório de Análise de Sentimento por Aspecto e Mapa de Atritos (WS6)

> **Projeto Aura 2.0** — Pipeline Reproduzível de Inteligência de Clientes e Retenção do Azul Fidelidade  
> **Frente:** Workstream 6 (WS6 · Sentimento por Aspecto e Mapa de Atritos)  
> **Status:** Entregue e Validado de Ponta a Ponta  
> **Data:** 12 de Outubro de 2026  

---

## 1. Declaração Central de Honestidade Metodológica

1. **Validação do Pipeline vs. Satisfação Real:** O corpus utilizado é **100% sintético e controlado**, composto por 1.200 avaliações rotuladas por aspecto com ground truth gerado via processo estocástico calibrado. As métricas de desempenho aqui reportadas comprovam a **corretude arquitetural, determinismo, poder discriminativo e capacidade de integração do pipeline de NLP**, **NÃO constituindo medição empírica de satisfação dos clientes reais da Azul**.
2. **Impossibilidade de Coleta Externa em Tempo Real:** Coletas automatizadas em canais públicos de terceiros (como Reclame Aqui e lojas de aplicativos) são estritamente restritas por termos de serviço, barreiras anti-automação (Akamai/Cloudflare/CAPTCHA) e diretrizes de IA responsável.
3. **Declaração de Desvio Metodológico do Kappa Inter-Anotadores:** O critério clássico de inter-anotadores humanos múltiplos (ex.: 2 anotadores independentes humanos rotulando 300 avaliações) é inexequível em ambiente puramente automatizado sem painel de anotadores humanos. O desvio é aqui formalmente declarado e suprido pelo cálculo do **Cohen's Kappa de concordância entre abordagens independentes** (Lexicon vs. TF-IDF + LogReg, obtendo **$\kappa = 0,3804$**), além do Kappa de cada abordagem contra o rótulo de ground truth (Lexicon: **$\kappa = 0,4169$**; TF-IDF: **$\kappa = 0,7924$**).
4. **Viés de Seleção de Plataforma:** Declaramos explicitamente que em dados empíricos reais existiria um severo viés de seleção (ex.: usuários que recorrem a portais de reclamação e redes sociais possuem viés extremo de insatisfação, enquanto canais como pesquisas transacionais de NPS capturam a maioria silenciosa). No corpus sintético, tal dinâmica foi modelada parametricamente por canal para validar a robustez dos modelos a diferentes distribuições a priori de sentimento.

---

## 2. Visão Geral da Arquitetura e Artefatos Produzidos

A frente WS6 atua como o elo perceptivo do Projeto Aura 2.0: traduz textos não estruturados de avaliações em indicadores quantificados de atrito que retroalimentam o gerador de dados sintéticos da WS2 (pesos de hazard de churn) e fornecem o contexto das dores do cliente para o motor de recomendações do Agente LLM (WS7).

```
[Corpus Sintético PT-BR] ─► [Holdout Temporal: Cutoff 2025-08-31]
  (1.200 avaliações,         │
   22 colunas, 7 aspectos)   ├─► Abordagem 1: Lexicon/Regras PT-BR
                             ├─► Abordagem 2: TF-IDF + LogReg OvR (Vencedora)
                             │
                             ▼
                    [Métricas & Comparação]
                             │
                             ▼
                 [Mapa de Atritos Semestral]
                             │
       ┌─────────────────────┴─────────────────────┐
       ▼                                           ▼
[data/analytics/friction_map.parquet]   [data/curated/friction_weights.json]
   (49 linhas: 7 aspectos × 7 semestres)   (pesos normalizados p/ WS2)
```

### Artefatos Entregues

| Artefato | Camada | Formato | Contrato de Schema | Descrição |
|---|---|---|---|---|
| [`sentiment_reviews.parquet`](../data/curated/sentiment_reviews.parquet) | `data/curated/` | Parquet | [`schemas/sentiment_reviews.yaml`](../schemas/sentiment_reviews.yaml) | 1.200 avaliações sintéticas com rótulos ground truth por aspecto |
| [`friction_map.parquet`](../data/analytics/friction_map.parquet) | `data/analytics/` | Parquet | [`schemas/friction_map.yaml`](../schemas/friction_map.yaml) | Mapa aspectos × semestre (2023-S2 a 2026-S2, último parcial — cobre apenas jul-ago/2026) com intensidades e tendências |
| [`friction_weights.json`](../data/curated/friction_weights.json) | `data/curated/` | JSON (`_meta`) | Auto-documentado | Pesos por aspecto para calibração do hazard de evasão na WS2 (soma = 1,0) |

---

## 3. Comparação Rigorosa das Abordagens de NLP

A avaliação foi realizada em **Holdout Temporal Estratificado**:
- **Janela de Treino:** 2023-09-01 a 2025-08-31 (**802 avaliações**, 67,1% dos dados)
- **Janela de Teste:** 2025-09-01 a 2026-08-31 (**398 avaliações**, 32,9% dos dados)
- **Critério Anti-Vazamento:** Separação estritamente cronológica, sem qualquer embaralhamento léxico entre passado e futuro.

### 3.1 Tabela Comparativa de Desempenho por Aspecto (Presença)

| Aspecto | Lexicon / Regras (F1) | TF-IDF + LogReg (F1) | Delta ($\Delta$) | Vencedor | Análise de Causa |
|---|:---:|:---:|:---:|:---:|---|
| **atraso** | 0,7864 | **1,0000** | +0,2136 | **TF-IDF + LogReg** | O classificador estatístico capturou n-gramas contextuais de horários e esperas sem falsos positivos |
| **bagagem** | 0,9023 | **1,0000** | +0,0977 | **TF-IDF + LogReg** | Regras sofrem falsos positivos com menções acidentais a "malas de mão" em outros contextos |
| **atendimento** | 0,9680 | **1,0000** | +0,0320 | **TF-IDF + LogReg** | TF-IDF discriminou perfeitamente menções a comissários/equipe de bordo e solo |
| **app_checkin** | 0,9675 | **1,0000** | +0,0325 | **TF-IDF + LogReg** | Captura exata de termos compostos ("check-in digital", "cartão de embarque", "login") |
| **resgate_milhas** | 0,9906 | **0,9952** | +0,0046 | **TF-IDF + LogReg** | Vocabulário altamente específico de fidelidade facilitou ambas as abordagens |
| **preco** | 0,6537 | **0,9925** | +0,3388 | **TF-IDF + LogReg** | Lexicon sofreu com termos polissêmicos de valor/custo e expressões informais de tarifas |
| **conforto** | 0,8421 | **0,9818** | +0,1397 | **TF-IDF + LogReg** | N-gramas de caracteres (char_wb 3-5) foram cruciais para capturar variações anatômicas e de cabine |
| **MÉDIA GLOBAL (Macro-F1)** | **0,8729** | **0,9956** | **+0,1227** | **TF-IDF + LogReg** | **Superação consistente em todos os 7 aspectos avaliados** |

> **Nota de Honestidade sobre a Magnitude do F1:** o corpus sintético é gerado a partir de famílias limitadas de *templates* por aspecto (~16 variações léxicas por aspecto). Nesse regime, um F1 de presença próximo de $1{,}0$ (TF-IDF) é um resultado **quase-trivial esperado** — a métrica valida a corretude mecânica do pipeline (tokenização, vetorização, treino, inferência e avaliação), **não** a habilidade de NLP em linguagem natural espontânea. Em avaliações reais (reviews orgânicas), espera-se queda substancial desses números; o gap Lexicon→TF-IDF, porém, é um achado estrutural que deve se manter.

### 3.2 Desempenho em Sentimento Geral e Polaridade

| Métrica | Lexicon / Regras | TF-IDF + Logistic Regression | Vencedor |
|---|:---:|:---:|:---:|
| **Macro-F1 Geral** | 0,5938 | **0,8450** | **TF-IDF + LogReg (+0,2512)** |
| **Precisão Geral (macro)** | 0,6071 | **0,8236** | **TF-IDF + LogReg (+0,2165)** |
| **Revocação Geral (macro)** | 0,6315 | **0,8747** | **TF-IDF + LogReg (+0,2432)** |
| **Cohen's Kappa vs. Ground Truth** | 0,4169 | **0,7924** | **TF-IDF + LogReg (Concordância Substancial)** |

- **Cohen's Kappa Inter-Abordagens:** **0,3804** (concordância moderada entre o modelo de regras e o modelo estatístico, refletindo a divergência de fronteira quando ironias e expressões ambíguas entram em cena).

### 3.3 Matrizes de Confusão Reais (Conjunto de Teste: 398 Amostras)

#### A. Sentimento Geral Consolidado

**1. Lexicon / Regras PT-BR:**
```
                     Predito Negativo   Predito Neutro   Predito Positivo
Real Negativo [258]        161                91                6
Real Neutro   [ 61]         12                25               24
Real Positivo [ 79]          0                11               68
```

**2. TF-IDF + Logistic Regression (One-vs-Rest):**
```
                     Predito Negativo   Predito Neutro   Predito Positivo
Real Negativo [258]        230                26                2
Real Neutro   [ 61]          5                47                9
Real Positivo [ 79]          0                 3               76
```

#### B. Matrizes de Confusão por Aspecto (Presença: 0 = Ausente, 1 = Presente)

| Aspecto | Matriz Lexicon `[[TN, FP], [FN, TP]]` | Matriz TF-IDF `[[TN, FP], [FN, TP]]` |
|---|:---:|:---:|
| `atraso` | `[[219, 63], [0, 116]]` | `[[282, 0], [0, 116]]` |
| `bagagem` | `[[280, 21], [0, 97]]` | `[[301, 0], [0, 97]]` |
| `atendimento` | `[[269, 8], [0, 121]]` | `[[277, 0], [0, 121]]` |
| `app_checkin` | `[[271, 8], [0, 119]]` | `[[279, 0], [0, 119]]` |
| `resgate_milhas` | `[[291, 2], [0, 105]]` | `[[293, 0], [1, 104]]` |
| `preco` | `[[260, 71], [0, 67]]` | `[[331, 0], [1, 66]]` |
| `conforto` | `[[321, 21], [0, 56]]` | `[[342, 0], [2, 54]]` |

*Interpretação técnica:* O modelo de Lexicon apresentou revocação perfeita ($1,000$), pois qualquer menção acionava o aspecto, porém gerou um volume expressivo de falsos positivos em contextos marginais (ex.: 71 falsos positivos em `preco`, 63 em `atraso`). A abordagem TF-IDF (composta por n-gramas de palavras e caracteres char_wb) eliminou virtualmente os falsos positivos mantendo revocação superior a $0,98$, resultando na vitória inequívoca do modelo de Machine Learning.

---

## 4. Mapa Analítico de Atritos e Tendências Semestrais

O mapa gerado em [`data/analytics/friction_map.parquet`](../data/analytics/friction_map.parquet) consolida a intensidade do atrito ao longo dos 7 semestres da janela sintética (2023-S2 a 2026-S2 — o último é **parcial**, cobrindo apenas julho-agosto/2026):

| Aspecto | Menções Totais | Menções Negativas | Taxa de Negatividade | Intensidade Média Global | Tendência Temporal | Peso Calibrado (WS2) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **atraso** | 366 | 274 | 74,86% | 0,8022 | **estável** | **0,1965** |
| **atendimento** | 371 | 253 | 68,19% | 0,7518 | **estável** | **0,1770** |
| **bagagem** | 305 | 226 | 74,10% | 0,7488 | **estável** | **0,1666** |
| **resgate_milhas** | 313 | 228 | 72,84% | 0,7427 | **crescente** | **0,1660** |
| **app_checkin** | 353 | 207 | 58,64% | 0,6629 | **decrescente** | **0,1411** |
| **preco** | 222 | 135 | 60,81% | 0,5967 | **estável** | **0,1026** |
| **conforto** | 144 | 63 | 43,75% | 0,4275 | **estável** | **0,0502** |
| **TOTAL** | **2.074** | **1.386** | **66,83%** | - | - | **1,0000** |

### Dinâmica Temporal Observada

1. **Resgate de Milhas (Tendência Crescente):** A intensidade do atrito subiu de $0,6643$ (2023-S2) para $0,8190$ (2026-S1), recuando levemente para $0,7694$ no semestre parcial 2026-S2 (jul-ago). Este comportamento simula a percepção de inflação de tabelas de pontos e escassez de assentos promocionais em programas de fidelidade ao longo do ciclo de vida dos associados.
2. **App & Check-in (Tendência Decrescente):** A intensidade do atrito recuou de $0,8174$ (pico em 2024-S1) para $0,5991$ (2026-S1) e $0,5322$ no parcial 2026-S2, reproduzindo a estabilização técnica e maturação das versões do aplicativo móvel após correções de bugs.
3. **Atraso de Voo (Severidade Dominante):** Mantém o maior peso de atrito global ($0,1965$) e a maior intensidade média ($0,8022$), com comportamento estável na janela. Os picos ocorreram em 2023-S2 ($0,8810$) e 2024-S2 ($0,8625$), com recuo atípico em 2025-S2 ($0,6844$) — a série não exibe sazonalidade estritamente regular, refletindo a estocasticidade calibrada do gerador.

---

## 5. Integração com as Demais Frentes do Projeto Aura 2.0

### 5.1 Calibração da Base Sintética (WS2 · `frictions.aspect_weights`)
O arquivo [`data/curated/friction_weights.json`](../data/curated/friction_weights.json) é a interface canônica com o gerador sintético de WS2:
- No modelo de risco de evasão (*churn hazard*), cada evento de voo que sofre atraso ou extravio de bagagem eleva o hazard individual proporcionalmente ao peso do aspecto calibrado.
- Exemplo: uma experiência negativa com atraso eleva o hazard basal com peso $0,1965$, enquanto um desconforto de assento contribui com peso $0,0502$.

### 5.2 Contexto para o Agente LLM (WS7 · Recomendação & RAG)
O histórico de atritos por aspecto detectado para cada cliente é injetado diretamente no prompt estruturado do Agente:
- Clientes com atrito dominante em `resgate_milhas` têm prioridade em ofertas de conversão bonificada ou desbloqueio de teto de emissão.
- Clientes com histórico recente de `atraso` ou `bagagem` recebem vouchers de compensação ou cortesias no Espaço Azul, acompanhados de justificativa embasada no regulamento.

### 5.3 Painel Executivo Streamlit (WS8)
A tabela analítica [`friction_map.parquet`](../data/analytics/friction_map.parquet) é lida diretamente na aba de Sentimento do aplicativo, alimentando gráficos de evolução temporal de atrito e matriz de priorização de melhorias operacionais.

---

## 6. Verificação de Qualidade e Conformidade

- **Testes Unitários e de Integração:** 9 testes em [`tests/test_sentiment.py`](../tests/test_sentiment.py), todos aprovados (saída `pytest` verde, exit code 0); suíte completa do repositório: **102 testes aprovados**.
- **Linter & Formatação:** 0 erros no `ruff check` (escopo `ml/sentiment`) e código estritamente formatado com `ruff format`.
- **Contratos YAML:** Validação de 100% das tabelas geradas contra [`schemas/sentiment_reviews.yaml`](../schemas/sentiment_reviews.yaml) e [`schemas/friction_map.yaml`](../schemas/friction_map.yaml) via `schemas.load.validate_or_raise`.
- **Comando Unificado:** Execução integral reproduzível via `python tasks.py sentiment`.

### 6.1 Registro de Correções Pós-Revisão Independente (Auditoria WS6)

A revisão adversarial independente (`docs/reviews/review_ws6.md`) aprovou a frente com ressalvas; as seguintes correções foram aplicadas e verificadas com execução real:

1. **Métricas secundárias corrigidas no relatório:** Precisão, Revocação e Kappa vs. Ground Truth da Seção 3.2 e da Seção 1 foram recalculados por execução direta de `run_evaluation()` e divergiam dos valores publicados originalmente (0,3340/0,7297 de kappa eram inexatos; os valores corretos são 0,4169/0,7924, derivados das próprias matrizes de confusão publicadas — que estavam corretas). As matrizes de confusão da Seção 3.3 foram reconferidas por execução independente: **idênticas**.
2. **Nota de honestidade sobre F1 quase-trivial** adicionada à Seção 3.1 (corpus de templates limitado valida mecânica do pipeline, não habilidade de NLP em linguagem natural).
3. **Correção de binning semestral (elevada de MENOR a correção real):** 72 avaliações de jul-ago/2026 caíam no semestre `2026-S2` (fora do domínio mapeado) e eram **silenciosamente rotuladas como 2026-S1**, distorcendo a tendência do último semestre. O semestre parcial `2026-S2` foi incluído explicitamente e `_assign_semester` passou a **falhar alto** (ValueError) para qualquer data fora do domínio. O mapa passou de 42 para 49 linhas; intensidades médias, tendências e pesos foram recalculados (baseline → novo: atraso 0,1953→0,1965; atendimento 0,1773→0,1770; bagagem 0,1647→0,1666; resgate_milhas 0,1645→0,1660; app_checkin 0,1451→0,1411 — desvio máximo, $-0{,}0040$; preco 0,1033→0,1026; conforto 0,0498→0,0502). A base sintética da WS2 gerada com os pesos antigos foi marcada para regeneração coerente pela cadeia `tasks.py synth` → `features` → `train`.
4. **Fail-loud no split temporal:** `run_temporal_validation` agora rejeita datas `NaT` (exceção explícita), normaliza fusos horários (tz-aware → naive) e **assevera que treino + teste = 100% das linhas** (zero perda silenciosa).
5. **Fallback de polaridade instrumentado:** o fallback `ausente → negativo` (presença=1) continua fail-safe, mas agora emite `logger.warning` por ocorrência (identificou 3 casos reais no corpus, todos em `conforto`).
6. **Caminhos de arquivo:** concatenação manual de strings substituída pelo helper canônico `aura_core.paths.path`.
