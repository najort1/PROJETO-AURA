# Review WS2 Revisita — MICRO-PARTE B1

**Projeto:** AURA 2.0
**Data:** 2025-01-XX
**Revisor:** Independente

---

## B1a · fail-loud (synthetic/loyalty.py)

### Verificação de código: `_load_rules`
- [ ] Propaga exceção com log (sem bare except silencioso)

### Verificação de código: `_extract_threshold`
- [ ] Aplica null_semantics (None = inelegível)

### Teste injetado (tmp_path)
- [ ] YAML com `qualifying_points: null` → `evaluate_tier` trata como inelegível SEM TypeError
- [ ] YAML malformado → exceção propagada

**Achados B1a:**
- Severidade: [CRÍTICO|IMPORTANTE|MENOR|OBSERVAÇÃO]
- Detalhes:

---

## B1b · Ordenação Canônica (DuckDB)

| Tabela | Chave Canônica | Linhas Fora de Ordem |
|--------|----------------|----------------------|
| transactions | (transaction_date, customer_id) | |
| flights | (scheduled_departure, flight_id) | |
| interactions | (interaction_date, interaction_id) | |
| loyalty_events | (event_date, event_id) | |

**Esperado:** 0 fora de ordem em cada.

**Achados B1b:**
- Severidade: [CRÍTICO|IMPORTANTE|MENOR|OBSERVAÇÃO]
- Detalhes:

---

## B1c · pytest/ruff do Escopo

- [ ] `pytest tests/test_synthetic.py -q` → 13 testes, exit 0
- [ ] `ruff check synthetic --output-format=concise` → limpo

**Achados B1c:**
- Severidade: [CRÍTICO|IMPORTANTE|MENOR|OBSERVAÇÃO]
- Detalhes:

---

## Veredito Parcial: [APROVADO|REPROVADO] (B1)

**Resumo:** Veredito + os 4 números de ordenação + o que encontrou.