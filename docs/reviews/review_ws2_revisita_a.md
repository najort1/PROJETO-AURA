# Revisita WS2 — Parte A: Verificação dos 2 CRÍTICOS + Replay Relacional

> **Data da Revisita:** 2026-10-12
> **Revisor Independente:** Subagente Especialista em Auditoria e Qualidade de Dados
> **Frente Auditada:** Workstream WS2 — Gerador Sintético (v3 regenerada pós-correções)
> **Protocolo:** `docs/reviews/README.md` (Ciclo de Qualidade Aura 2.0)
> **Escopo:** APENAS itens A1–A3 abaixo. Parte B (relatório/fidelidade/determinismo) será feita por outro revisor.

---

## A1 · CRÍTICO 1 — Vazamento Temporal na Qualificação (Janela Móvel)

### Análise de Código (`synthetic/generate.py` ~linha 360–367)

**Código atual (pós-correção):**
```python
# Linha 360-367
eval_dt = purchase_dt
if rng.random() < ancillary_prop:
    eval_dt = purchase_dt + dt.timedelta(minutes=5)

cutoff_365 = eval_dt - dt.timedelta(days=365)
recent_act = [h for h in qual_history if cutoff_365 <= h[0] <= eval_dt]
```

**Veredito do código:** ✅ **CORRIGIDO** — O filtro agora possui teto temporal `h[0] <= eval_dt` onde `eval_dt` = data da compra (ou +5min para ancillary). O vazamento original (`h[0] >= cutoff_365` sem teto superior) foi eliminado.

---

### (a) Query do Revisor Original — Eventos com qualifying_points_at_event > soma de pontos na janela [event_date-365d, event_date]

**SQL Executado:**
```sql
WITH tx_window AS (
    SELECT 
        le.event_id,
        le.customer_id,
        le.event_date,
        le.qualifying_points_at_event,
        SUM(t.pontos_qualificaveis_acumulados) as tx_qp_sum
    FROM loyalty_events le
    LEFT JOIN transactions t
        ON le.customer_id = t.customer_id
        AND t.transaction_date >= le.event_date - INTERVAL 365 DAY
        AND t.transaction_date <= le.event_date
        AND t.transaction_type IN ('compra_passagem', 'acumulo_cartao', 'acumulo_clube', 'servico_ancillary')
    GROUP BY le.event_id, le.customer_id, le.event_date, le.qualifying_points_at_event
)
SELECT event_id, customer_id, event_date, qualifying_points_at_event, tx_qp_sum
FROM tx_window
WHERE qualifying_points_at_event > tx_qp_sum
ORDER BY event_date;
```

**Resultado:** **0 linhas** — Nenhum evento de fidelidade soma pontos de transações fora da janela [event_date-365d, event_date]. O vazamento original (1.009 eventos contaminados) foi **eliminado**.

---

### (b) Variante Própria — Qualquer transação com data > event_date contribuindo

**SQL Executado:**
```sql
WITH tx_all AS (
    SELECT 
        le.event_id,
        le.customer_id,
        le.event_date,
        le.qualifying_points_at_event,
        SUM(CASE WHEN t.transaction_date <= le.event_date THEN t.pontos_qualificaveis_acumulados ELSE 0 END) as qp_in_window,
        SUM(CASE WHEN t.transaction_date > le.event_date THEN t.pontos_qualificaveis_acumulados ELSE 0 END) as qp_future
    FROM loyalty_events le
    LEFT JOIN transactions t
        ON le.customer_id = t.customer_id
        AND t.transaction_date >= le.event_date - INTERVAL 365 DAY
        AND t.transaction_type IN ('compra_passagem', 'acumulo_cartao', 'acumulo_clube', 'servico_ancillary')
    GROUP BY le.event_id, le.customer_id, le.event_date, le.qualifying_points_at_event
)
SELECT event_id, customer_id, event_date, qualifying_points_at_event, qp_in_window, qp_future
FROM tx_all
WHERE qp_future > 0
ORDER BY event_date;
```

**Resultado:** **12.711 eventos** têm transações posteriores à data do evento dentro da janela de 365 dias — **MAS** em todos os casos `qualifying_points_at_event == qp_in_window` (ex.: EV0003571: 6.154 QP no evento = 6.154 QP na janela ≤ event_date; 39.268 QP em transações futuras **não** contabilizados). Os pontos futuros existem na base mas **não vazam** para o evento. Comportamento correto.

---

### (c) Busca de Outros Usos de Informação Futura no Loop de Simulação

**Análise do `generate.py` completo (linhas 150–510):**
- **Linhas 224–247:** Transações de cartão/clube geradas *antes* do loop de voos, mas com datas aleatórias no período inteiro (2023–2026). O filtro da janela móvel (linha 367) **exclui corretamente** as futuras via `h[0] <= eval_dt`.
- **Linhas 266–268:** `purchase_dt` calculada com antecedência baseada em `dep_date_d` (voo futuro) — isso é **modelagem de antecedência de compra**, não vazamento: a decisão de compra ocorre *antes* do voo, consistente com o mundo real.
- **Linhas 361–363:** `eval_dt = purchase_dt` (+5min se ancillary) — teto temporal correto.
- **Linhas 398–463:** Interações geradas *após* a avaliação de tier, baseadas no voo atual — sem influência reversa.
- **Linhas 465–507:** Avaliação final no encerramento usa `qual_history` completo com teto `exp_date` — correto.
- **Nenhum uso de voos/interações futuras influenciando decisões passadas detectado.**

**Veredito A1(c):** ✅ **LIMPO** — Nenhum outro vazamento temporal identificado.

---

## A2 · CRÍTICO 2 — Downgrades Rotulados como Upgrades

### SQL: Distribuição event_type × trigger_reason

**Esperado (após correção):**
- ~9.077 `tier_upgrade`
- ~6.091 `tier_downgrade` com `qualification_cycle_expired`
- Total: 15.168 eventos

**SQL Executado:**
```sql
SELECT event_type, trigger_reason, COUNT(*) as cnt
FROM loyalty_events
GROUP BY event_type, trigger_reason
ORDER BY event_type, trigger_reason;
```

**Resultado Obtido:**
| event_type | trigger_reason | cnt |
|---|---|---|
| tier_downgrade | qualification_cycle_expired | 6.091 |
| tier_upgrade | alternative_spend_reached | 4 |
| tier_upgrade | qualifying_points_reached | 3.055 |
| tier_upgrade | segments_reached | 6.018 |
| **Total** | | **15.168** |

✅ **CONFORME** — Distribuição idêntica ao esperado. Downgrades agora existem e são rotulados corretamente.

---

### Coerência dos Pares: new_tier vs previous_tier

**SQL Executado:**
```sql
-- Verificar: nenhum tier_downgrade com new_tier SUPERIOR a previous_tier
-- Ordem canônica: azul(1) < topazio(2) < safira(3) < diamante(4) < diamante_unique(5)
SELECT event_id, customer_id, event_date, event_type, previous_tier, new_tier, trigger_reason
FROM loyalty_events
WHERE event_type = 'tier_downgrade';
```
**Downgrades incoerentes (new_tier > previous_tier): 0**

```sql
-- Verificar: nenhum tier_upgrade com new_tier INFERIOR a previous_tier
SELECT event_id, customer_id, event_date, event_type, previous_tier, new_tier, trigger_reason
FROM loyalty_events
WHERE event_type = 'tier_upgrade';
```
**Upgrades que são downgrades reais (new_tier < previous_tier): 0**

✅ **COERÊNCIA TOTAL** — Todos os 6.091 downgrades têm new_tier < previous_tier; todos os 9.077 upgrades têm new_tier > previous_tier. A inversão semântica original (5.049 downgrades rotulados como upgrade) foi **totalmente corrigida**.

---

### Schema: allowed_values inclui tier_downgrade + qualification_cycle_expired

**Verificação:** ✅ **CONFORME** — Schema `schemas/synthetic_loyalty_events.yaml` linhas 91–100 incluem ambos os valores em `allowed_values`.

---

## A3 · IMPORTANTE — Replay Relacional Completo nos 50k

### SQL: Último evento por cliente vs customers.parquet current_tier

**SQL Executado:**
```sql
WITH last_events AS (
    SELECT 
        customer_id,
        new_tier,
        ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY event_date DESC, event_id DESC) as rn
    FROM loyalty_events
)
SELECT 
    c.customer_id,
    c.current_tier as customers_tier,
    le.new_tier as last_event_tier,
    CASE WHEN c.current_tier = le.new_tier THEN 'OK' ELSE 'DIVERGÊNCIA' END as status
FROM customers c
LEFT JOIN last_events le ON c.customer_id = le.customer_id AND le.rn = 1
WHERE c.current_tier != le.new_tier OR le.new_tier IS NULL;
```

**Resultado:** 
- **45.016 clientes sem nenhum evento de fidelidade** (permaneceram `azul` durante toda a simulação) → divergência esperada (last_event_tier = NULL).
- **0 divergências entre os 4.984 clientes que TÊM eventos** — para todo cliente com pelo menos um evento, o `new_tier` do último evento bate exatamente com `customers.current_tier`.

✅ **REPLAY PERFEITO** — Integridade relacional garantida para 100% dos clientes com histórico de fidelidade.

---

### Honestidade dos "Eventos de Correção" (generate.py ~519–560)

**Código analisado:** O fixer emite eventos de correção quando `replay_tier != final_tier` na data de fim da simulação (2026-08-31 23:59:59).

**SQL Executado:**
```sql
SELECT COUNT(*) as cnt, event_type, trigger_reason
FROM loyalty_events
WHERE event_date = '2026-08-31 23:59:59'
GROUP BY event_type, trigger_reason;
```

**Resultado:**
| cnt | event_type | trigger_reason |
|---|---|---|
| 1.063 | tier_downgrade | qualification_cycle_expired |
| 7 | tier_upgrade | segments_reached |
| 11 | tier_upgrade | qualifying_points_reached |
| **1.081** | **Total** | |

**Análise detalhada dos 1.081 eventos de correção:**

| Categoria | Quantidade | Natureza | Honestidade |
|---|---|---|---|
| **Downgrades legítimos** | 1.063 | Clientes que qualificaram tier (tinham QP > 0 no evento) mas pararam de voar; pontos expiraram no ciclo. O último evento logado era upgrade; a correção registra a expiração real. | ✅ **Honestos** — `qualifying_points_at_event > 0` (ex.: 1.709, 4.819, 9.791), `trigger_reason = qualification_cycle_expired`. Representam transições reais não logadas (dormentes que decaíram). |
| **Upgrades legítimos** | 12 | Clientes que re-qualificaram via transações de cartão/clube/compras *após* o último voo (sem voo = sem trigger de avaliação). Têm QP/segmentos reais no evento. | ✅ **Honestos** — Ex.: C009705: 6.488 QP, 6 seg; C011037: 12.733 QP, 14 seg. |
| **Upgrades "remendo" (0 pontos)** | **6** | Clientes cujo último evento foi downgrade, mas final_tier > last_event_tier. O fixer usa placeholders `qualifying_points=0, segments=0, spend_brl=0.0` e emite `trigger_reason = qualifying_points_reached` ou `segments_reached` **falso**. | ⚠️ **REMENDO** — 6 eventos (EV0015160, EV0015162, EV0015164, EV0015166, EV0015167, EV0015168) têm `qualifying_points_at_event=0, segments_at_event=0, spend_brl_at_event=0.0` mas declaram upgrade por pontos/segmentos. Embora esses clientes *tenham* re-qualificado na vida real (QP no último ano: 2.511–7.595), o evento de correção **não registra os valores reais**. |

**Veredito A3:** O mecanismo de correção é **maioritariamente honesto** (1.075/1.081 = 99,4% representam transições reais com métricas reais), mas **6 eventos (0,6%) são remendos com métricas zeradas e gatilhos falsos**. Isso não quebra o replay (o replay usa `new_tier`, que está correto), mas introduz ruído semântico na tabela de eventos.

---

## Tabela Resumo A1–A3

| Item | Status | Evidência Principal | Severidade Residual |
|------|--------|---------------------|---------------------|
| A1(a) | ✅ PASS | 0 linhas com qualifying_points_at_event > soma na janela [event_date-365d, event_date] | — |
| A1(b) | ✅ PASS | 12.711 eventos têm transações futuras na janela, mas **qualifying_points_at_event == qp_in_window** em todos | — |
| A1(c) | ✅ PASS | Análise completa do generate.py: nenhum outro vazamento temporal detectado | — |
| A2 (distribuição) | ✅ PASS | 9.077 upgrades (4 alt_spend + 3.055 QP + 6.018 seg) + 6.091 downgrades (qual_cycle_expired) = 15.168 | — |
| A2 (coerência) | ✅ PASS | 0 downgrades incoerentes; 0 upgrades que são downgrades reais | — |
| A2 (schema) | ✅ CONFORME | Schema permite tier_downgrade + qualification_cycle_expired | — |
| A3 (replay) | ✅ PASS | 0 divergências entre 4.984 clientes com eventos; 45.016 sem eventos (azul perpétuo) | — |
| A3 (correções) | ⚠️ PARCIAL | 1.081 correções: 1.075 honestos (métricas reais), **6 remendos (métricas 0, gatilhos falsos)** | **MENOR** |

---

## Achados Novos (além dos originais)

| ID | Descrição | Severidade | Evidência |
|----|-----------|------------|-----------|
| **A3-N1** | 6 eventos de correção "upgrade" em 2026-08-31 23:59:59 têm `qualifying_points_at_event=0, segments_at_event=0, spend_brl_at_event=0.0` mas `trigger_reason` = `qualifying_points_reached`/`segments_reached`. O fixer usa placeholders zerados em vez dos valores reais que o cliente acumulou no último ano (2.511–7.595 QP). | **MENOR** | 6 eventos (EV0015160, EV0015162, EV0015164, EV0015166, EV0015167, EV0015168); clientes C014386, C022068, C030377, C043889, C044391, C046349 re-qualificaram de fato (QP_last_year > 0) mas correção não reflete isso. |

---

## Veredito Parcial da Parte A

**Veredito:** **APROVADO (parte A)**

**Condição:** APROVADO se A1-A3 OK sem CRÍTICO/IMPORTANTE aberto.

**Justificativa:**
- **A1 (CRÍTICO 1):** Totalmente corrigido — vazamento temporal eliminado (0 eventos contaminados vs 1.009 originais).
- **A2 (CRÍTICO 2):** Totalmente corrigido — downgrades existem (6.091), rotulados corretamente, coerentes com a ordem canônica de tiers.
- **A3 (IMPORTANTE):** Replay relacional **perfeito** (0 divergências para clientes com eventos). Eventos de correção são 99,4% honestos; os 6 remendos (0,6%) são **MENOR**, não IMPORTANTE/CRÍTICO.

Nenhum CRÍTICO ou IMPORTANTE permanece aberto na Parte A.

---

## Mensagem Final

> **Veredito Parcial: APROVADO (Parte A)** — A1: 0 vazamentos (vs 1.009 originais); A2: 6.091 downgrades corretos + 9.077 upgrades coerentes (vs 5.049 downgrades rotulados como upgrade); A3: Replay 100% consistente (4.984/4.984 clientes com eventos), 1.081 correções (1.075 honestas, 6 remendos MENOR).