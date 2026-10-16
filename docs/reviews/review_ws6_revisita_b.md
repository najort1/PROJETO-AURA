# Revisão Independente — WS6 Parte B: Código e Artefatos

> **Projeto Aura 2.0** — Re-auditoria do Workstream 6 (Sentimento por Aspecto e Mapa de Atritos)
> **Revisor:** Revisor Independente Adversarial
> **Data:** 2026-10-12
> **Foco:** Verificação dos 3 MENORES da revisão original + qualidade de código/artefatos (B1–B5)

---

## Veredito Parcial da Parte B

**Status: ✅ APROVADO** — Todas as verificações B1–B5 concluídas com sucesso. Os 3 MENORES da revisão original estão resolvidos; qualidade de código/artefatos validada; adversarial sem achados ≥ IMPORTANTE.

---

## Tabela de Verificações: Item → Verificação → Evidência → Status

| Item | Verificação | Evidência | Status |
|------|-------------|-----------|--------|
| **B1** | Binning semestral fail-loud + `friction_map.parquet` + `friction_weights.json` | SEMESTERS tem 7 entradas (inclui "2026-S2"); `_assign_semester` lança ValueError para 2023-01-15 e 2027-03-01; parquet: 49 linhas, 7 semestres, friction_id único, aspect_weight constante por aspecto, pesos conferem (atraso 0.1965, atendimento 0.177, bagagem 0.1666, resgate_milhas 0.166, app_checkin 0.1411, preco 0.1026, conforto 0.0502), soma=1.0; JSON bate com parquet | ✅ **APROVADO** |
| **B2** | Split temporal fail-loud em `approaches.py` (`run_evaluation`) | Código (linhas 717-738): (i) `pd.to_datetime(..., errors="raise")` + verifica `NaT` e lança `ValueError` explícito; (ii) normaliza tz-aware→naive via `dt.tz_localize(None)`; (iii) asserção `train_mask.sum() + test_mask.sum() == len(df)` com `AssertionError`; (iv) usa `path("data/curated/sentiment_reviews.parquet")` da `aura_core.paths`. Testes de injeção: NaT lança ValueError ("1 datas nulas (NaT) no corpus — correção obrigatória antes do split."); tz-aware normalizado corretamente (treino=2, teste=1); asserção train+test passa (2+2=4). | ✅ **APROVADO** |
| **B3** | Fallback polaridade 'ausente'→'negativo' emite `logger.warning` | Código em `approaches.py` linhas 551–560 (método `TfidfLogisticApproach.predict`): bloco `if has_val == 1 and pol_val == "ausente":` emite `logger.warning(...)` explícito antes de definir `pol_val = "negativo"`. Confirmado no código. | ✅ **APROVADO** |
| **B4** | Qualidade: `pytest tests/test_sentiment.py -q` (exit code, 9 testes) + `ruff check ml/sentiment` (limpo) + contratos via `schemas.load.validate_or_raise` | `pytest`: 9 passed, exit code 0. `ruff check ml/sentiment`: All checks passed. Contratos: `validate_or_raise` para `friction_map.parquet` e `sentiment_reviews.parquet` → **OK**. | ✅ **APROVADO** |
| **B5** | Adversarial no código `ml/sentiment`: falhas silenciosas, magic numbers, caminhos hardcoded | Encontrados 5 achados (ver detalhes abaixo): 1 MENOR (caminho hardcoded em friction_map.py), 3 MENOR (magic numbers sem justificativa em formulas de intensidade/tendência/pesos), 1 OBSERVAÇÃO (fallback silencioso de semestre em corpus.py). Sem CRÍTICO/IMPORTANTE. | ✅ **APROVADO** (sem achado ≥ IMPORTANTE) |

---

## Achados Novos (Adversarial)

| ID | Severidade | Componente | Resumo |
|----|------------|------------|--------|
| **B5-01** | MENOR | `friction_map.py:279` | Caminho hardcoded com concatenação `+` em vez de `path()` |
| **B5-02** | MENOR | `friction_map.py:94-97,125-130,134` | Magic numbers em fórmula de intensidade (0.70/0.30/3.0), thresholds de tendência (±0.015), expoente de peso (0.5) sem justificativa |
| **B5-03** | MENOR | `corpus.py` (múltiplas linhas) | Magic numbers extensivos no gerador sintético (pesos de canal, probabilidades, ajustes temporais, ruído) sem constantes nomeadas |
| **B5-04** | OBSERVAÇÃO | `corpus.py:395-396` | Fallback silencioso de semestre para "2026-S1" (contraste com fail-loud em `friction_map.py`) |
| **B5-05** | OBSERVAÇÃO | `friction_map.py:78` | `max(1, len(sem_df))` mascara semestre sem dados sem aviso |

*Nenhum achado CRÍTICO ou IMPORTANTE.*

---

## Detalhamento por Item

### B1 — Binning semestral fail-loud + Artefatos

**Objetivo:** Confirmar que:
1. `SEMESTERS` em `friction_map.py` tem 7 entradas incluindo `"2026-S2"` (parcial jul-ago)
2. `_assign_semester` lança `ValueError` para datas fora do domínio (sem fallback `"2026-S1"`)
3. `data/analytics/friction_map.parquet`: 49 linhas; 7 semestres; `friction_id` único; para cada aspecto, `aspect_weight` constante; pesos = atraso 0.1965 / atendimento 0.1770 / bagagem 0.1666 / resgate_milhas 0.1660 / app_checkin 0.1411 / preco 0.1026 / conforto 0.0502; soma por aspecto = 1.0
4. `data/curated/friction_weights.json` bate com esses pesos

**Evidência de Código (`ml/sentiment/friction_map.py`):**
- Linhas 31–39: `SEMESTERS` list com 7 entradas, incluindo `"2026-S2"` (comentário: semestre PARCIAL jul-ago/2026)
- Linhas 42–53: `_assign_semester` lança `ValueError` se `label not in SEMESTERS` — **fail-loud confirmado, sem fallback**

**Teste de Provocação de Erro (executado):**
```text
OK 2023-01-15: Data 2023-01-15 00:00:00 fora do dominio de semestres do mapa de atritos (2023-S2 a 2026-S2): rotular '2023-S1' exigiria falha silenciosa. Ajuste SEMESTERS ou a janela do corpus.
OK 2027-03-01: Data 2027-03-01 00:00:00 fora do dominio de semestres do mapa de atritos (2023-S2 a 2026-S2): rotular '2027-S1' exigiria falha silenciosa. Ajuste SEMESTERS ou a janela do corpus.
OK 2024-03-15: 2024-S1
OK 2026-07-15 (2026-S2): 2026-S2
```

**Verificação de Artefatos (executada):**
```text
Linhas: 49
Semestres unicos: 7 - ['2023-S2', '2024-S1', '2024-S2', '2025-S1', '2025-S2', '2026-S1', '2026-S2']
friction_id unico: True
Aspectos: ['app_checkin', 'atendimento', 'atraso', 'bagagem', 'conforto', 'preco', 'resgate_milhas']

Aspect_weight por aspecto (todos constantes):
  atraso: 0.1965 | atendimento: 0.177 | bagagem: 0.1666 | resgate_milhas: 0.166
  app_checkin: 0.1411 | preco: 0.1026 | conforto: 0.0502

Soma pesos (unique aspects): 1.0

JSON weights: {'atraso': 0.1965, 'bagagem': 0.1666, 'atendimento': 0.177, 'app_checkin': 0.1411, 'resgate_milhas': 0.166, 'preco': 0.1026, 'conforto': 0.0502}
Verificação JSON vs Parquet: TODOS MATCH = True
```

**Status B1:** ✅ **APROVADO** — Todos os 4 sub-itens confirmados.

---

### B2 — Split temporal fail-loud (`approaches.py`)

**Objetivo:** Confirmar em `run_evaluation` (linhas 700–778):
1. Rejeita `NaT` com `ValueError` explícito (linhas 719–722)
2. Normaliza tz-aware→naive (linhas 724–726)
3. Asserção de que treino+teste == total de linhas (linhas 733–738)
4. Usa `aura_core.paths.path` (linha 714) sem concatenação de strings

**Evidência de Código:**
- Linha 717: `pd.to_datetime(df["review_date"], errors="raise")`
- Linhas 719–722: Verifica `NaT` e lança `ValueError`
- Linhas 724–726: `dt.tz_localize(None)` se tz-aware
- Linhas 733–738: `AssertionError` se split não cobre 100%
- Linha 714: `path("data/curated/sentiment_reviews.parquet")`

**Teste de Injeção (executados):**

*Teste 1 — NaT:*
```text
OK: ValueError lançado: 1 datas nulas (NaT) no corpus — correção obrigatória antes do split.
```

*Teste 2 — Timezone-aware (UTC):*
```text
Holdout temporal aplicado: Treino (2 amostras até 2025-08-31) | Teste (1 amostras pós 2025-08-31)
OK: timezone-aware normalizado, treino=2 teste=1
```

*Teste 3 — Asserção train+test == total:*
```text
Holdout temporal aplicado: Treino (2 amostras até 2025-08-31) | Teste (2 amostras pós 2025-08-31)
OK: treino=2 teste=2 total=4
```

**Status B2:** ✅ **APROVADO** — Todos os 4 sub-itens confirmados via código e execução.

---

### B3 — Fallback polaridade 'ausente'→'negativo' com `logger.warning`

**Objetivo:** Confirmar que em `approaches.py` (classe `TfidfLogisticApproach.predict`, linhas 551–560) o fallback emite `logger.warning`.

**Evidência de Código (linhas 551–560):**
```python
# Harmonização: se pres_val == 1 mas pol_val == 'ausente', seleciona a polaridade
# dominante de atrito (negativo) — com WARNING explícito (nunca silencioso).
if has_val == 1 and pol_val == "ausente":
    logger.warning(
        "Polaridade 'ausente' com presença=1 para aspecto '%s' (amostra %d): "
        "aplicando fallback 'negativo' de atrito.",
        aspect,
        i,
    )
    pol_val = "negativo"  # fallback de polaridade mais provável para atrito
elif has_val == 0:
    pol_val = "ausente"
```

**Status B3:** ✅ **APROVADO** — Código confirmado com `logger.warning` explícito (não silencioso). A execução que evidencia os 3 warnings em conforto é da Parte A; aqui basta o código.

---

### B4 — Qualidade: Testes, Linting, Contratos

**Objetivo:**
1. `pytest tests/test_sentiment.py -q` → exit code 0, 9 testes
2. `ruff check ml/sentiment` → limpo
3. Script curto validando `friction_map.parquet` e `sentiment_reviews.parquet` via `schemas.load.validate_or_raise` → imprime só "OK"/erro

**Execução:**
```powershell
& .venv\Scripts\python.exe -m pytest tests/test_sentiment.py -q
& .venv\Scripts\python.exe -m ruff check ml/sentiment
```

**Resultados:**
```text
# pytest
.........                                                                [100%]
Exit code: 0

# ruff
All checks passed!
```

**Script de Validação de Contratos (executado):**
```python
import sys

sys.path.insert(0, ".")
from schemas.load import validate_or_raise, load_contract

try:
    validate_or_raise(load_contract("friction_map"), "data/analytics/friction_map.parquet")
    validate_or_raise(load_contract("sentiment_reviews"), "data/curated/sentiment_reviews.parquet")
    print("OK")
except Exception as e:
    print(f"ERRO: {e}")
    sys.exit(1)
```
**Saída:** `OK`

**Status B4:** ✅ **APROVADO** — Testes (9 passed, exit 0), Linting (limpo), Contratos (válidos).

---

### B5 — Adversarial no código `ml/sentiment`

**Objetivo:** Procurar outros problemas:
- Falhas silenciosas
- Magic numbers sem justificativa
- Caminhos hardcoded
- Outras inconsistências

**Análise Detalhada (arquivos: `corpus.py`, `approaches.py`, `friction_map.py`, `pipeline.py`):**

#### Achados Registrados

| ID | Severidade | Arquivo / Linha | Descrição |
|----|------------|-----------------|-----------|
| **B5-01** | **MENOR** | `friction_map.py:279` | **Caminho hardcoded com concatenação de string**: `settings().get("paths", {}).get("data_curated", "data/curated") + "/sentiment_reviews.parquet"` usa `+` em vez do resolvedor padronizado `path()` do núcleo (`aura_core.paths.path`). Inconsistência de convenção (demais arquivos usam `path()`). |
| **B5-02** | **MENOR** | `friction_map.py:94-97, 125-130, 134` | **Magic numbers em fórmula de intensidade e pesos**: Intensidade usa pesos fixos `0.70` (neg_rate) e `0.30` (prevalence) com fator de escala `3.0` e `np.clip(0.0, 1.0)`. Tendência usa thresholds `±0.015` para classificar crescente/decrescente/estável. Peso bruto usa expoente `0.5` (raiz quadrada de `total_neg`). Não há comentário justificando a escolha desses valores específicos (por que 70/30? por que 3.0? por que 0.015? por que sqrt?). |
| **B5-03** | **MENOR** | `corpus.py:296-301, 317-341, 414, 417, 277-288` | **Magic numbers extensivos no gerador de corpus**: Pesos por canal (`channel_weights`), probabilidade de n-aspectos (`[0.40, 0.45, 0.15]`), negatividade base por canal (`0.88, 0.65, 0.55, 0.35, default 0.60`), ajustes temporais (`+0.08, +0.10, -0.12, +0.10`), clipping (`0.15, 0.95`), probabilidade neutro fixa (`0.10`), piso positivo (`0.02`), distribuição de canais (`[0.30, 0.35, 0.20, 0.15]`), ironia (`0.07`), ruído (`[0.55, 0.30, 0.15]`), ruído textual (`0.35, 0.40, 0.30, 0.25`). Embora aceitável em gerador sintético controlado, a ausência de constantes nomeadas ou configuração externa reduz auditabilidade e reprodutibilidade parametrizada. |
| **B5-04** | **OBSERVAÇÃO** | `corpus.py:395-396` | **Fallback silencioso de semestre**: Se `semester_label not in semesters` (lista só vai até `2026-S1`), faz fallback silencioso para `"2026-S1"` sem log/aviso. Contraste com `friction_map.py:_assign_semester` que falha alto (fail-loud). Como a janela de geração (2023-09 a 2026-08) só produz semestres válidos, o branch nunca é atingido em execução normal, mas permanece como código morto/defesa imperfeita. |
| **B5-05** | **OBSERVAÇÃO** | `friction_map.py:78` | **`n_sem = max(1, len(sem_df))`**: Evita divisão por zero em `prevalence = n_mentions / n_sem` quando semestre sem dados, mas mascara silenciosamente a ausência de dados no semestre (prevalence vira 0 em vez de sinalizar). Aceitável como proteção, mas poderia emitir `logger.debug` ou `warning` se `len(sem_df) == 0`. |

#### Verificações Negativas (Ausência de Problemas Graves)
- ✅ **Nenhum `except: pass` ou `except:` bare**: Único `except` em `pipeline.py:92-95` loga stack trace completo e retorna exit code 1.
- ✅ **Nenhum `print` de debug em código de produção**: Apenas em `main()` para CLI.
- ✅ **Type hints consistentes** em assinaturas públicas.
- ✅ **Contratos de dados validados** em todos os pontos de gravação (`save_corpus`, `save_friction_outputs`).
- ✅ **Uso de `path()`** em `approaches.py:714`, `corpus.py:506`, `friction_map.py:252-253` — apenas `friction_map.py:279` foge ao padrão.
- ✅ **Fail-loud implementado** nos pontos críticos (NaT, tz-aware, split temporal, semestre fora do domínio em `friction_map.py`).

**Status B5:** ✅ **APROVADO** — 5 achados (1 MENOR de caminho, 3 MENOR de magic numbers, 1 OBSERVAÇÃO de fallback, 1 OBSERVAÇÃO de proteção silenciosa). **Nenhum achado CRÍTICO ou IMPORTANTE**.

---

## Veredito Final da Parte B

**VEREDITO: ✅ APROVADO (Parte B)**

### Critérios Atendidos
- ✅ **B1** — Binning semestral fail-loud + artefatos (`friction_map.parquet`, `friction_weights.json`) conferidos integralmente
- ✅ **B2** — Split temporal fail-loud em `approaches.py` (`run_evaluation`): NaT rejeitado, tz-aware normalizado, asserção train+test, usa `path()`
- ✅ **B3** — Fallback polaridade 'ausente'→'negativo' emite `logger.warning` explícito (não silencioso)
- ✅ **B4** — Qualidade: `pytest` (9 passed, exit 0), `ruff check ml/sentiment` (limpo), contratos validados (OK)
- ✅ **B5** — Adversarial: 5 achados (1 MENOR caminho, 3 MENOR magic numbers, 2 OBSERVAÇÃO), **nenhum ≥ IMPORTANTE**

### Resumo
A Parte B da re-auditoria WS6 confirma que os **3 MENORES da revisão original foram resolvidos** (fail-loud no binning semestral, split temporal robusto, warning no fallback de polaridade) e a **qualidade de código/artefatos está adequada** (testes, linting, contratos). A análise adversarial do código não revelou problemas de severidade CRÍTICA ou IMPORTANTE — apenas melhorias incrementais (constantes nomeadas, padronização de `path()`, logging de proteções silenciosas).

A Parte B está **APROVADA** e não bloqueia a promoção da frente WS6.