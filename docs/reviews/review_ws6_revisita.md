# Relatório de Revisita (Re-auditoria) — WS6 (Sentimento/Mapa de Atritos)

> **Projeto Aura 2.0** — Pós-correção da frente WS6  
> **Revisor:** Revisor Independente Adversarial  
> **Data da Revisita:** 2026-10-12  
> **Protocolo:** `docs/reviews/README.md`  
> **Auditoria Original:** `docs/reviews/review_ws6.md` (APROVADO COM RESSALVAS — 2 IMPORTANTE + 3 MENORES)

---

## 1. Veredito Executivo (Pendente — será preenchido ao final)

| Item | Status |
|---|---|
| **Veredito Final** | *PENDENTE* |
| **Bloqueio de Promoção** | *PENDENTE* |

---

## 2. Tabela de Acompanhamento: Achados Originais → Verificação → Evidência Real → Status

| ID Original | Classificação | Achado Resumo | Verificação Realizada | Evidência Real | Status |
|---|---|---|---|---|---|
| WS6-01 | IMPORTANTE | Métricas secundárias divergentes no relatório (Precisão, Revocação, Kappa) | [A] Recálculo via `run_evaluation()` vs §3.2 | *A preencher* | *PENDENTE* |
| WS6-02 | IMPORTANTE | Omissão de honestidade sobre F1 ≈ 1,0 em templates | [B] Leitura §3.1 | *A preencher* | *PENDENTE* |
| WS6-03 | MENOR | Descarte silencioso de NaT e colapso tz no split temporal | [C/D] Código + injeção NaT/fora domínio | *A preencher* | *PENDENTE* |
| WS6-04 | MENOR | Fallbacks silenciosos (polaridade, semestre) | [E] Logger.warning + ValueError | *A preencher* | *PENDENTE* |
| WS6-05 | OBSERVAÇÃO | Concatenação direta de caminho vs `aura_core.paths.path` | [D/F/G] Leitura código | *A preencher* | *PENDENTE* |

---

## 3. Verificações de Revisita (Checklist [A]–[H])

### [A] Métricas do relatório vs execução real
*Status: PENDENTE — Executar `run_evaluation()` e conferir contra §3.2*

**Evidência:**
```
[A ser preenchido após execução]
```

### [B] Nota de honestidade F1 quase-trivial em §3.1
*Status: PENDENTE — Ler relatório e julgar adequação*

**Evidência:**
```
[A ser preenchido após leitura]
```

### [C] Binning semestral: SEMESTERS (7 entradas, "2026-S2" parcial) + ValueError fora domínio
*Status: PENDENTE — Ler `friction_map.py`, conferir parquet, provocar ValueError*

**Evidência:**
```
[A ser preencher após verificação]
```

### [D] Split temporal fail-loud: rejeita NaT, normaliza tz-aware→naive, asserção treino+teste==total, usa `aura_core.paths.path`
*Status: PENDENTE — Ler `approaches.py` + injeção NaT*

**Evidência:**
```
[A ser preencher após verificação]
```

### [E] Fallback de polaridade emite `logger.warning` (3 casos reais em conforto)
*Status: PENDENTE — Confirmar no código e nos logs da execução [A]*

**Evidência:**
```
[A ser preencher após verificação]
```

### [F] Coerência relatório↔parquet (§4): intensidades, tendências, série, totais (2.074 menções; 1.386 negativas; 66,83%)
*Status: PENDENTE — Recalcular slope de tendência*

**Evidência:**
```
[A ser preencher após verificação]
```

### [G] Qualidade: pytest, ruff, schemas validate
*Status: PENDENTE — Rodar suíte completa*

**Evidência:**
```
[A ser preencher após execução]
```

### [H] Adversarial: problemas NOVOS no escopo
*Status: PENDENTE — Busca ativa*

**Achados Novos:**
```
[A ser preencher]
```

---

## 4. Achados Novos (Severidade: CRÍTICO | IMPORTANTE | MENOR | OBSERVAÇÃO)

*A preencher durante [H]*

---

## 5. Veredito Final (será preenchido após completar [A]–[H])

**Veredito:** *PENDENTE*  
**Justificativa:** *A ser preenchida*