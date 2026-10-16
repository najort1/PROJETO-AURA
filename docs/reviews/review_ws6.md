# Relatório de Revisão Independente Adversarial — WS6 (Sentimento e Mapa de Atritos)

> **Projeto Aura 2.0** — Pipeline Reproduzível de Inteligência de Clientes e Retenção do Azul Fidelidade  
> **Frente Auditada:** Workstream 6 (WS6 · Sentimento por Aspecto e Mapa de Atritos)  
> **Revisor:** Revisor Independente Adversarial (`mega-brain`)  
> **Data da Auditoria:** 12 de Outubro de 2026  
> **Protocolo de Referência:** `docs/reviews/README.md`  

---

## 1. Resumo Executivo e Veredito

| Item | Status |
|---|---|
| **Veredito da Frente** | **APROVADO COM RESSALVAS** |
| **Bloqueio de Promoção** | **SIM** (Os achados de severidade IMPORTANTE devem ser saneados antes da promoção para produção pelo Lead) |
| **Total de Achados** | **5** (0 Críticos, 2 Importantes, 2 Menores, 1 Observação) |

### Justificativa Sintética do Veredito
A frente WS6 cumpriu a entrega de todos os artefatos de código, pipelines, modelos estatísticos, geração determinística do corpus sintético de 1.200 avaliações, contratos de dados (`schemas/sentiment_reviews.yaml` e `schemas/friction_map.yaml`), mapa de atritos semestral (42 linhas) e pesos de atrito calibrados (soma = 1,0000000000). A suíte de testes passa integralmente (`9 passed in 3.88s`), a formatação e linting estão sem erros (`ruff check` limpo) e os testes de falha ruidosa (*fail-loud*) reagem adequadamente contra mutações artificiais.

Entretanto, a auditoria adversarial identificou **duas inconsistências metodológicas e documentais de severidade IMPORTANTE**:
1. **Divergência de Métricas Secundárias no Relatório:** Os números de Precisão Geral, Revocação Geral e Cohen's Kappa vs. Ground Truth reportados na Tabela 3.2 e Seção 1 de `docs/sentiment_report.md` divergem em mais de 0,05 dos valores reais gerados pela execução do pipeline e matematicamente derivados das próprias matrizes de confusão exibidas na Seção 3.3.
2. **Omissão de Honestidade Intelectual sobre F1 ≈ 1,0 em Templates:** O relatório atribui a performance quase perfeita da abordagem TF-IDF (F1 = 1,0000 em 4 aspectos, 0,9956 na média) exclusivamente à superioridade dos n-gramas do modelo estatístico, omitindo a ressalva crítica de que o corpus sintético foi montado a partir de um conjunto restrito e finito de 16 templates fixos por aspecto, tornando a discriminação quase-trivial por memorização de vocabulário e padrões frasais.

Adicionalmente, foram identificadas fragilidades menores no tratamento de datas no split temporal (descarte silencioso de `NaT` e colapso de tipo em datetimes com timezone) e fallbacks silenciosos pontuais.

---

## 2. Checklist de Verificações Obrigatórias (12 Itens)

A tabela abaixo registra a execução real e independente de cada uma das 12 verificações previstas no protocolo:

| # | Verificação | Comando / Procedimento Executado | Resultado Real Obtido | Status |
|---|---|---|---|:---:|
| **1** | Suíte de Testes e Linter | `& .venv\Scripts\python.exe -m pytest tests/test_sentiment.py -v`<br>`& .venv\Scripts\python.exe -m ruff check ml/sentiment tests/test_sentiment.py` | `9 passed in 3.88s`<br>`All checks passed!` | **CONFORME** |
| **2** | Split Temporal e Anti-Vazamento | Inspeção de `approaches.py` (linhas 712-721); injeção de `NaT` e timestamps com timezone | Split temporal rigoroso (cutoff 2025-08-31 23:59:59; 802 treino / 398 teste; sem shuffle). Porém, `NaT` é descartado silenciosamente e tz quebra em `TypeError`. | **RESSALVA** |
| **3** | Recálculo Independente de Métricas | Execução de `run_evaluation()` e verificação sklearn sobre `sentiment_reviews.parquet` | Macro-F1 por aspecto (0,8729 vs 0,9956) e Macro-F1 geral (0,5938 vs 0,8450) conferem exatamente ($\Delta = 0,0000$). Precisão/Revocação/Kappa divergem em > 0,05. | **RESSALVA** |
| **4** | Honestidade sobre F1 ≈ 1,0 | Análise textual da Seção 1 e Seção 3.1 de `docs/sentiment_report.md` | Relatório declara que o corpus é sintético, mas NÃO explicita que o F1 ≈ 1,00 decorre da memorização do vocabulário dos 16 templates por aspecto. | **RESSALVA** |
| **5** | Cohen's Kappa Proxy | Cálculo de Cohen's Kappa entre abordagens e contra Ground Truth | Kappa inter-abordagens = `0,3804` (conferido). Kappa vs GT Lexicon = `0,4169` (reportado `0,3340`); TF-IDF = `0,7924` (reportado `0,7297`). | **RESSALVA** |
| **6** | Inspeção do Corpus Sintético | Amostragem de 20 avaliações via pandas; busca por marcas de terceiros e referências da cia | Multi-aspecto real (1 a 3 aspectos), ironia (81 casos) e ruído presentes. Sem marcas reais (Reclame Aqui, Google Play, etc.). Cia referida genericamente ("companhia", "aerea"). | **CONFORME** |
| **7** | Contratos de Dados e Fail-Loud | Validação dos arquivos oficiais e de cópias com mutações via `schemas.load.validate_or_raise` | Tabelas oficiais passam sem violações. Mutações (coluna renomeada, domínio inválido, intensidade > 1,0) disparam `RuntimeError` imediato. | **CONFORME** |
| **8** | Pesos de Atrito (`friction_weights.json`) | Verificação de estrutura, campos `_meta`, soma dos pesos e consistência com `aspect_stats` | Soma exata = `1,0000000000` ($\Delta < 10^{-6}$). Estrutura completa. Atraso lidera (`0,1953`), conforto é mínimo (`0,0498`), semanticamente coerente. | **CONFORME** |
| **9** | Mapa de Atritos (`friction_map.parquet`) | Verificação de linhas (7 × 6 = 42), tendências e intensidades semestrais via pandas | Exatamente 42 linhas. Resgate crescente ($0,6643 \to 0,8064$), app decrescente ($0,8174 \to 0,5821$). Valores idênticos aos reportados. | **CONFORME** |
| **10** | Detecção de Fail-Loud / Excepts | Grep por `except` em `ml/sentiment`; inspeção de branches condicionais | Apenas um bloco `except` no `main()` de `pipeline.py` (com log e re-emissão de código de saída 1). Fallbacks silenciosos menores identificados em branches pontuais. | **CONFORME** |
| **11** | LGPD e Declarações de Honestidade | Verificação de sensibilidade de colunas no schema e leitura da Seção 1 do relatório | Nenhuma coluna sensível (sem CPF, nome, contato). Declaração formal de corpus sintético, desvio do kappa humano por proxy e viés de plataforma presentes. | **CONFORME** |
| **12** | Cruzamento Reportado vs. Real | Comparação exaustiva de todas as tabelas e dados numéricos do relatório | Tabelas 3.1, 3.3 e 4 conferem 100%. Tabela 3.2 e Seção 1 apresentam números desalinhados com a saída real executada. | **RESSALVA** |

---

## 3. Evidências Detalhadas por Verificação

### Verificação 1: Testes e Linter
```powershell
# Execução dos testes unitários e de integração
& .venv\Scripts\python.exe -m pytest tests/test_sentiment.py -v
```
*Saída real capturada:*
```text
============================= test session starts =============================
platform win32 -- Python 3.11.0, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\najort\Documents\GitHub\PROJETO AURA
configfile: pyproject.toml
plugins: anyio-4.15.1, typeguard-4.6.0
collected 9 items

tests\test_sentiment.py .........                                        [100%]

============================== 9 passed in 3.88s ==============================
```

```powershell
# Verificação de linting
& .venv\Scripts\python.exe -m ruff check ml/sentiment tests/test_sentiment.py
```
*Saída real capturada:*
```text
All checks passed!
```

---

### Verificação 2: Holdout Temporal e Contraexemplos
Inspeção do arquivo `ml/sentiment/approaches.py` (linhas 712–728):
```python
df["review_date"] = pd.to_datetime(df["review_date"])

# Holdout temporal: treino <= cutoff, teste > cutoff
cutoff_ts = pd.to_datetime(f"{cutoff_date} 23:59:59")
train_mask = df["review_date"] <= cutoff_ts
test_mask = df["review_date"] > cutoff_ts

train_df = df[train_mask].copy().reset_index(drop=True)
test_df = df[test_mask].copy().reset_index(drop=True)
```
- **Conformidade de vazamento:** O corte temporal é puramente cronológico (802 amostras em treino de 2023-09-01 a 2025-08-31; 398 em teste de 2025-09-03 a 2026-08-31). O vetorizador `TfidfVectorizer` é ajustado exclusivamente em `train_df["text"]` (linha 482/743) e apenas transforma `test_df["text"]` (linha 528).
- **Contraexemplo 1 (Valores Nulos / NaT):** Quando uma avaliação possui `review_date = pd.NaT`, tanto `NaT <= cutoff_ts` quanto `NaT > cutoff_ts` avaliam como `False`. Como consequência, a linha é silenciosamente descartada sem erro:
  ```text
  Original rows: 1200 | Sum train+test: 1199 (1 linha descartada sem asserção ou alerta)
  ```
- **Contraexemplo 2 (Timezone-Aware Datetime):** Caso o DataFrame contenha datas com timezone (ex.: `UTC` vindo de Parquet gerado por outro sistema), a comparação contra `cutoff_ts` (naive) falha:
  ```text
  TypeError: Invalid comparison between dtype=datetime64[ns, UTC] and Timestamp
  ```

---

### Verificações 3 e 5: Recálculo Independente de Métricas e Cohen's Kappa
Executado script independente via Python com `sklearn.metrics` sobre `data/curated/sentiment_reviews.parquet` após holdout temporal (802 treino, 398 teste):

#### A. Métricas por Aspecto (Presença) — Conferência Exata
| Aspecto | Lexicon F1 (Real) | Lexicon F1 (Doc) | TF-IDF F1 (Real) | TF-IDF F1 (Doc) | Vencedor | Status |
|---|:---:|:---:|:---:|:---:|---|:---:|
| `atraso` | 0,7864 | 0,7864 | 1,0000 | 1,0000 | TF-IDF + LogReg | Confere |
| `bagagem` | 0,9023 | 0,9023 | 1,0000 | 1,0000 | TF-IDF + LogReg | Confere |
| `atendimento` | 0,9680 | 0,9680 | 1,0000 | 1,0000 | TF-IDF + LogReg | Confere |
| `app_checkin` | 0,9675 | 0,9675 | 1,0000 | 1,0000 | TF-IDF + LogReg | Confere |
| `resgate_milhas` | 0,9906 | 0,9906 | 0,9952 | 0,9952 | TF-IDF + LogReg | Confere |
| `preco` | 0,6537 | 0,6537 | 0,9925 | 0,9925 | TF-IDF + LogReg | Confere |
| `conforto` | 0,8421 | 0,8421 | 0,9818 | 0,9818 | TF-IDF + LogReg | Confere |
| **Média Global** | **0,8729** | **0,8729** | **0,9956** | **0,9956** | **TF-IDF + LogReg** | **Confere ($\Delta = 0,0000$)** |

#### B. Métricas de Sentimento Geral e Kappa — Discrepâncias Encontradas
| Métrica | Abordagem | Valor Real Executado | Valor Reportado no Doc | Divergência | Severidade |
|---|---|:---:|:---:|:---:|:---:|
| **Macro-F1 Geral** | Lexicon | 0,5938 | 0,5938 | 0,0000 | Confere |
| **Macro-F1 Geral** | TF-IDF | 0,8450 | 0,8450 | 0,0000 | Confere |
| **Precisão Geral** | Lexicon | **0,6071** | **0,6669** | -0,0598 | **IMPORTANTE** |
| **Precisão Geral** | TF-IDF | **0,8236** | **0,8807** | -0,0571 | **IMPORTANTE** |
| **Revocação Geral** | Lexicon | **0,6315** | **0,6424** | -0,0109 | **IMPORTANTE** |
| **Revocação Geral** | TF-IDF | **0,8747** | **0,8272** | +0,0475 | **IMPORTANTE** |
| **Kappa vs. Ground Truth** | Lexicon | **0,4169** | **0,3340** | +0,0829 | **IMPORTANTE** |
| **Kappa vs. Ground Truth** | TF-IDF | **0,7924** | **0,7297** | +0,0627 | **IMPORTANTE** |
| **Kappa Inter-Abordagens** | Ambas | **0,3804** | **0,3804** | 0,0000 | Confere |

*Nota Crítica:* As matrizes de confusão exibidas na Seção 3.3 A do relatório estão matematicamente corretas e batem aos inteiros com a execução real (`[[161, 91, 6], [12, 25, 24], [0, 11, 68]]` e `[[230, 26, 2], [5, 47, 9], [0, 3, 76]]`). Contudo, o cálculo de precisão, revocação e kappa derivado dessas exatas matrizes produz `P=0,6071`, `R=0,6315`, `κ=0,4169` para Lexicon e `P=0,8236`, `R=0,8747`, `κ=0,7924` para TF-IDF, evidenciando que os números da Tabela 3.2 do relatório foram digitados a partir de rascunhos desatualizados.

---

### Verificação 6: Inspeção Textual do Corpus e Marcas
Amostragem de 20 avaliações de `data/curated/sentiment_reviews.parquet`:
- **PT-BR e Multi-Aspecto:** O corpus apresenta construções idiomáticas reais em PT-BR (ex.: *"App intuitivo, rapido e com notificacoes pontuais sobre o portao de embarque. e alem disso Otimo valor pago pela passagem, valeu muito a pena"*), combinando até 3 aspectos com conectores sintáticos de mesma polaridade e polaridade inversa.
- **Ironia e Ruído:** 81 avaliações (6,75% do corpus) possuem flag `is_ironic = True` com marcadores verossímeis (*"Que maravilha de experiencia..."*, *"Parabens aos envolvidos sqn..."*, *"Muito obrigado pelo estresse gratuito!"*). Ruído textual inclui gírias (*"perrengue chique"*, *"pura dor de cabeca"*), abreviações (*"q"*, *"vc"*, *"tb"*, *"pra"*) e pontuação excessiva (*"...!!!"*).
- **Ausência de Marcas Comerciais:** Busca global (`grep` / `str.contains`) por `reclame aqui`, `reclameaqui`, `google play`, `app store`, `trustpilot`, `tripadvisor`, `twitter`, `instagram`, `facebook`, `consumidor.gov` retornou **0 ocorrências**.
- **Menção à Companhia:** A palavra "azul" ocorre **0 vezes** no texto das avaliações; menções ocorrem de forma genérica como "companhia" (12 ocorrências) ou "aerea/aereas" (10 ocorrências), respeitando a especificação de neutralidade de canal e ausência de difamação de marca.

---

### Verificação 7: Contratos de Dados e Comportamento Fail-Loud
Validação formal executada contra os contratos YAML em `schemas/`:
```python
# 1. Dados reais
validate_or_raise(
    load_contract("sentiment_reviews"), "data/curated/sentiment_reviews.parquet"
)  # PASSED
validate_or_raise(load_contract("friction_map"), "data/analytics/friction_map.parquet")  # PASSED

# 2. Injeção de violações artificiais em arquivo temporário:
# A. Coluna renomeada ('review_id' -> 'id_invalido'):
# RuntimeError: Contrato de dados violado: [sentiment_reviews] coluna declarada ausente: review_id
# B. Canal com marca real / valor fora do domínio ('canal_proibido_marca_real'):
# RuntimeError: Contrato de dados violado: [sentiment_reviews] valores fora do domínio em channel
# C. Intensidade semestral fora da faixa (> 1.0):
# RuntimeError: Contrato de dados violado: [friction_map] check custom falhou: valid_semester_intensity_range
```
Ambos os contratos disparam falhas altas explícitas (*fail-loud* com `RuntimeError`), sem engolir inconsistências.

---

### Verificações 8 e 9: Pesos de Atrito e Mapa de Fricção Semestral
Inspeção de `data/curated/friction_weights.json` e `data/analytics/friction_map.parquet`:
- **Soma dos Pesos:** $\sum w_i = 0,1953 + 0,1647 + 0,1773 + 0,1451 + 0,1645 + 0,1033 + 0,0498 = \mathbf{1,0000000000}$ (diferença absoluta para 1,0 = `0.0`, estritamente inferior a $10^{-6}$).
- **Metadados:** Objeto `_meta` contém documentação completa, metodologia, declaração de dados sintéticos e campos de consumo para WS2.
- **Hierarquia Semântica:** Atraso (`0,1953`) e Atendimento (`0,1773`) lideram os atritos por causarem disrupção operacional severa e frustração direta; Conforto (`0,0498`) apresenta menor volume de queixas e taxa de negatividade reduzida (43,75%), coerente com a malha doméstica da aviação civil.
- **Granularidade do Mapa:** Exatamente 42 registros (7 aspectos × 6 semestres de `2023-S2` a `2026-S1`).
- **Tendências Semestrais Reais:**
  - `resgate_milhas`: Intensidade semestral sobe monotonicamente de $0,6643$ em 2023-S2 para $0,8064$ em 2026-S1 (tendência `crescente`).
  - `app_checkin`: Intensidade recua de $0,8174$ no pico de 2024-S1 para $0,5821$ em 2026-S1 (tendência `decrescente`).

---

### Verificações 10 e 11: Fail-Loud e LGPD
- **Excepts no Código:** Apenas um bloco `except` no ponto de entrada de linha de comando (`ml/sentiment/pipeline.py:92-95`), o qual emite log com stack trace completo e retorna código de saída `1`. Nenhum bloco `except: pass` existe no repositório.
- **LGPD:** Todos os campos em `schemas/sentiment_reviews.yaml` estão anotados com `sensitive: false`. Não existem nomes, e-mails, números de bilhete, localizadores (PNR), documentos de identidade ou dados pessoais sensíveis no corpus.
- **Declarações de Honestidade:** `docs/sentiment_report.md` declara explicitamente na Seção 1 que os dados são sintéticos, que as métricas validam a integridade arquitetural do pipeline e não a satisfação empírica de passageiros reais, e formaliza a substituição do Kappa inter-anotadores humanos pelo proxy inter-modelos e contra ground truth.

---

## 4. Tabela de Achados da Auditoria

| ID | Classificação | Componente / Arquivo | Linhas | Descrição do Achado e Evidência |
|---|---|---|---|---|
| **WS6-01** | **IMPORTANTE** | `docs/sentiment_report.md` | L14, L76-L78 | **Discrepância numérica entre relatório e execução real:** Na Tabela 3.2 e na Seção 1, o Kappa vs. GT do Lexicon é reportado como 0,3340 (real = 0,4169; erro de +0,0829) e do TF-IDF como 0,7297 (real = 0,7924; erro de +0,0627). A Precisão Geral do Lexicon é reportada como 0,6669 (real = 0,6071) e do TF-IDF como 0,8807 (real = 0,8236). A Revocação Geral do Lexicon é reportada como 0,6424 (real = 0,6315) e do TF-IDF como 0,8272 (real = 0,8747). Embora o Macro-F1 (0,5938 / 0,8450) e as matrizes de confusão estejam corretos, essas métricas secundárias no texto não têm respaldo na execução real. |
| **WS6-02** | **IMPORTANTE** | `docs/sentiment_report.md` | L60-L70, L114 | **Omissão de ressalva metodológica sobre F1 ≈ 1,00 em corpus template-based:** O relatório comemora F1 de 1,0000 em 4 aspectos e média de 0,9956 atribuindo o resultado unicamente à capacidade dos n-gramas do modelo. No entanto, o corpus é gerado a partir de um pool finito de apenas 16 frases fixas por aspecto (`ml/sentiment/corpus.py:43-212`). O modelo de TF-IDF essencialmente memoriza as assinaturas lexicais dos templates geradores. O relatório deve explicitar essa limitação para manter a honestidade científica do projeto. |
| **WS6-03** | **MENOR** | `ml/sentiment/approaches.py` | L715-728 | **Descarte silencioso de NaT e colapso em Datetimes com Timezone:** O particionamento temporal filtra via boolean indexing (`<= cutoff` e `> cutoff`). Valores `NaT` resultam em `False` em ambas as máscaras e são descartados silenciosamente sem `assert len(train_df) + len(test_df) == len(df)`. Além disso, se a série de datas possuir fuso horário (ex. `datetime64[ns, UTC]`), a comparação com `cutoff_ts` naive quebra com `TypeError`. |
| **WS6-04** | **MENOR** | `ml/sentiment/approaches.py`<br>`ml/sentiment/friction_map.py` | L550-552<br>L46 | **Fallbacks silenciosos em regras de harmonização e semestre:** Em `approaches.py`, se a presença for 1 mas a polaridade for predita como 'ausente', o código força silenciosamente para 'negativo' sem registrar log de aviso. Em `friction_map.py:46`, se o semestre não constar na lista esperada, ocorre fallback silencioso para `'2026-S1'`. |
| **WS6-05** | **OBSERVAÇÃO** | `ml/sentiment/approaches.py` | L707-710 | **Concatenação direta de caminho de arquivo:** Utilização de `+ "/sentiment_reviews.parquet"` sobre string de configuração em vez do resolvedor padronizado `path()` do núcleo (`aura_core.paths.path`), gerando inconsistência de convenção de paths do projeto. |

---

## 5. Plano de Ação Recomendado para o Lead

Para converter o status de **APROVADO COM RESSALVAS** em **APROVADO DEFINITIVO**:

1. **Atualizar `docs/sentiment_report.md` (Tabela 3.2 e Seção 1):**
   - Corrigir a Precisão Geral: Lexicon $\to 0,6071$; TF-IDF $\to 0,8236$.
   - Corrigir a Revocação Geral: Lexicon $\to 0,6315$; TF-IDF $\to 0,8747$.
   - Corrigir o Cohen's Kappa vs. Ground Truth: Lexicon $\to 0,4169$; TF-IDF $\to 0,7924$.
2. **Incluir Nota Metodológica sobre F1 ≈ 1,0 em `docs/sentiment_report.md` (Seção 3.1):**
   - Adicionar parágrafo formal reconhecendo que a quase perfeição do F1 ($0,9956$) reflete a natureza finita dos templates do gerador estocástico (16 templates por aspecto), sendo uma validação da integridade do fluxo de vetorização e inferência, e não evidência de generalização sobre linguagem natural livre e não-estruturada.
3. **Reforçar Asserção Temporal em `ml/sentiment/approaches.py`:**
   - Adicionar verificação explícita `assert len(train_df) + len(test_df) == len(df)` logo após o split e normalizar fuso horário (`dt.tz_localize(None)`).

---
*Relatório emitido pelo Revisor Independente Adversarial — Projeto Aura 2.0.*
