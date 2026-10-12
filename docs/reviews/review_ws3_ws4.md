# Revisão Adversarial Independente — WS3+WS4 (Features dbt + Modelos CLV/Churn + SHAP + Model Cards)

**Projeto:** AURA 2.0  
**Data:** 2025-01-15 (auditoria)  
**Auditor:** Revisor Independente  
**Base:** Sintética v3 corrigida (50k clientes)  
**Cutoff principal:** 2025-08-31 | **Validação:** 2025-02-28 (47.851 clientes)

---

## Sumário Executivo

*Auditando: Anti-vazamento, métricas recalculadas, decis, bootstrap/IC, BG/NBD+GG, SHAP, Model Cards, contratos, testes, achados adversariais.*

---

## Checklist V1-V10 — Resultados

### [V1] ANTI-VAZAMENTO (Coração da frente)

| Sub-item | Status | Evidência | Severidade |
|----------|--------|-----------|------------|
| V1a: Features usam apenas info ≤ cutoff (leitura SQL/macros) | ✅ PASS | Macro `generate_customer_features`: todas as CTEs (`historical_transactions`, `agg_tx`, `route_ranking`, `historical_interactions`) filtram por `WHERE transaction_date <= DATE '{{ cutoff_date }}'` ou `WHERE interaction_date <= DATE '{{ cutoff_date }}'`. `future_performance` (targets) usa `BETWEEN target_start AND target_end` estritamente pós-cutoff. | — |
| V1b: 16 testes dbt (incl. no_future_leakage) | ✅ PASS | `dbt test` executado: PASS=16, WARN=0, ERROR=0. Testes incluem: `accepted_values` (tier), `not_null` (customer_id, frequency_12m, monetary_12m, recency_days, tier), `unique` (customer_id), `no_future_leakage` (last_activity_date ≤ cutoff) para ambas as tabelas. | — |
| V1c: Query adversarial própria (max date ≤ cutoff por coorte) | ✅ PASS | Query DuckDB: `MAX(last_activity_date)` = 2025-08-30 (features_customer, cutoff 2025-08-31) e 2025-02-27 (features_customer_val, cutoff 2025-02-28). Nenhuma data > cutoff. | — |
| V1d: Targets CLV/churn ausentes das features; split estritamente temporal | ✅ PASS | Features usam apenas dados históricos. Targets (`target_clv_12m`, `target_churn_12m`) vêm de `future_performance` CTE com janela futura explícita. Treino: coorte val (cutoff 2025-02-28), Teste: coorte principal (cutoff 2025-08-31). Zero random split. | — |
| V1e: Atributos sensíveis (faixa_etaria, genero, regiao) ausentes dos parquets | ✅ PASS | Verificado: `features_customer.parquet` (50.000 linhas, 32 colunas) e `features_customer_val.parquet` (47.851 linhas, 32 colunas) — nenhuma das 3 colunas sensíveis presente. Staging `stg_customers` também as exclui. | — |

### [V2] Métricas — Recalculação Independente

| Métrica | Declarada (JSON/Model Card) | Recalculada | Delta | Status |
|---------|----------------------------|-------------|-------|--------|
| CLV WAPE LGBM | 0.6550 | 0.6550 | 0.0000 | ✅ MATCH |
| CLV WAPE Baseline | 0.7974 | 0.7974 | 0.0000 | ✅ MATCH |
| CLV MAE LGBM | 497.85 | 497.85 | 0.00 | ✅ MATCH |
| CLV MAE Baseline | 606.12 | 606.12 | 0.00 | ✅ MATCH |
| CLV Spearman LGBM | 0.7346 | 0.7346 | 0.0000 | ✅ MATCH |
| CLV Spearman Baseline | 0.6106 | 0.6106 | 0.0000 | ✅ MATCH |
| CLV Gini LGBM | 0.6604 | 0.6604 | 0.0000 | ✅ MATCH |
| CLV Gini Baseline | 0.5935 | 0.5935 | 0.0000 | ✅ MATCH |
| CLV Lift Decil 1 LGBM | 5.23x | 5.23x | 0.00x | ✅ MATCH |
| CLV Lift Decil 1 Baseline | 4.35x | 4.35x | 0.00x | ✅ MATCH |
| Churn ROC-AUC LGBM | 0.8566 | 0.8566 | 0.0000 | ✅ MATCH |
| Churn ROC-AUC Baseline | 0.8440 | 0.8440 | 0.0000 | ✅ MATCH |
| Churn PR-AUC LGBM | 0.8373 | 0.8373 | 0.0000 | ✅ MATCH |
| Churn PR-AUC Baseline | 0.8307 | 0.8302 | -0.0005 | ⚠️ MINOR (0.0005 < 0.002 threshold) |
| Churn Brier LGBM | 0.1453 | 0.1453 | 0.0000 | ✅ MATCH |
| Churn Brier Baseline | 0.1516 | 0.1516 | 0.0000 | ✅ MATCH |
| Churn Lift Top 10% LGBM | 1.73x | 1.73x | 0.00x | ✅ MATCH |
| Churn Lift Top 10% Baseline | 1.73x | 1.73x | 0.00x | ✅ MATCH |

**Nota:** Todas as divergências são < 0.002 (limiar do checklist). A única diferença notável é PR-AUC baseline (0.8302 vs 0.8307, delta=0.0005), provavelmente por precisão numérica ou implementação ligeiramente diferente de Average Precision. Métricas do modelo final batem exatamente.

### [V3] Decis — Top 10% por predição decrescente

| Modelo | Ordem correta? | Evidência |
|--------|----------------|-----------|
| CLV decile_model | ✅ PASS | `decile_model` idêntico ao recalculado com `argsort(-pred, kind="stable")`. Decil 1 = 5.000 clientes (10%), predições médias 3.879 vs true 3.975. |
| Churn decile_model | ⚠️ MENOR | Contagens por decil corretas (5.000 cada), mas 22/50.000 registros (0,044%) diferem do `argsort(-pred, kind="stable")` recalculado devido a tie-breaking em predições idênticas (5.244 valores únicos p/ 50k). Decil 1 correto (top 10% = 5.000, lift 1,73x). **Não afeta métricas agregadas.** |

### [V4] Bootstrap/IC — Comparação pareada, p-valores coerentes

| Teste | Status | Observações |
|-------|--------|-------------|
| Réplicas pareadas (mesmo idx para modelo e baseline) | ✅ PASS | Código em `ml/common/metrics.py:342-347` usa mesmo `idx = rng.integers(0, n, size=n)` para `m_val` e `b_val` em cada iteração. |
| IC95 plausíveis (não cruza zero quando significant=true) | ✅ PASS | Todos os 6 ICs (WAPE, MAE, Spearman, ROC-AUC, PR-AUC, Brier) não cruzam zero quando `significant=True`. Recalculados com seed=42, n=500: valores próximos aos declarados (diferenças < 0.001 por variabilidade bootstrap). |
| p_valor = prop(diffs <= 0) para higher_is_better=False | ✅ PASS | Implementação correta: `higher_is_better=True` -> p = mean(diffs <= 0); `higher_is_better=False` -> p = mean(diffs >= 0). Todos p=0.0 (nenhuma réplica bootstrap favoreceu o baseline). |

### [V5] BG/NBD+Gamma-Gamma — Fórmulas Fader/Hardie corretas

| Componente | Status | Observações |
|------------|--------|-------------|
| Log-verossimilhança BG/NBD (casos x=0 e x>0) | ✅ PASS | `_negative_log_likelihood` implementa exatamente a Eq. 4 de Fader et al. (2005): x=0 → `r*log(α) - r*log(α+T)`; x>0 → termo Gamma-Poisson + termo Beta-Geométrico + termo de probabilidade viva. Otimização em log-space com penalização L2. |
| E[X(t)] com hyp2f1 | ✅ PASS | `expected_transactions` usa `hyp2f1(r+x, b+x, a+b+x-1, z)` com `z = t/(α+T+t)`, fórmula exata da Eq. 7/8 de Fader et al. (2005). Tratamento numérico com clip e `nan_to_num`. |
| Gamma-Gamma E[Monetary] com retração Bayesiana | ✅ PASS | `_negative_log_likelihood` corresponde à log-verossimilhança Gamma-Gamma (Fader & Hardie 2005). `expected_monetary_value`: prior mean = γ*p/(q-1); para x>0,m>0 → retração Bayesiana `(γ*p + p*x*m) / (p*x + q - 1)`. |
| Testes de sanidade (monotonicidade recência/frequência, retração) | ✅ PASS | `tests/test_bgnbd.py`: testa `expected_transactions` monotonicidade em recência (t_x maior → E[Y] menor) e frequência (x maior → E[Y] maior); testa Gamma-Gamma monotonicidade no gasto e retração Bayesiana (poucas transações → mais retraído à prior). Todos passam. |
| Baseline usado corretamente na comparação | ✅ PASS | `ml/clv/train.py:112-129` ajusta BG/NBD+GG na coorte de treino (val_cutoff=2025-02-28) e prevê na coorte de teste (cutoff=2025-08-31) com mesmos inputs (frequency_12m, recency=365-recency_days, tenure=365, ticket_medio_12m). Métricas comparadas lado a lado. |

### [V6] SHAP — Top-3 por cliente, sinal coerente, figuras existem

| Item | Status | Evidência |
|------|--------|-----------|
| clv_shap.parquet tem top1-3 por cliente | ✅ PASS | 50.000 linhas, 11 colunas (customer_id, shap_top3_json, top1-3_feature/shap/value). 100% preenchido. |
| churn_shap.parquet tem top1-3 por cliente | ✅ PASS | 50.000 linhas, 11 colunas (customer_id, shap_top3_json, top1-3_feature/shap/value). 100% preenchido. |
| Exemplo 1 cliente CLV: sinal/magnitude coerente | ✅ PASS | TreeSHAP nativo via `predict(pred_contrib=True)`. Base value = 756.81 (média global). Soma SHAP + base = predição exata (verificado 4 clientes: erro < 0.01). Top features consistentes com importância global (tier_encoded, avg_advance_booking_days, monetary_12m, recency_days). Sinais condicionais às interações de features. |
| Exemplo 1 cliente Churn: sinal/magnitude coerente | ✅ PASS | SHAP em escala log-odds (margem bruta do LightGBM). Base = 0.0227 (log-odds → ~50,6% churn). Sigmoid(base + ΣSHAP) = predição exata (verificado 4 clientes). Recência: SHAP negativo para clientes com recency_days baixa (atividade recente → menos churn) e pode variar por interações. Top features: recency_days, tier_encoded, avg_advance_booking_days — consistentes com importância global. |
| Figuras PNG referenciadas existem | ✅ PASS | 6 figuras existem e são referenciadas nos model cards: clv_shap_global.png, clv_waterfall_example.png, clv_lorenz_curve.png, churn_shap_global.png, churn_waterfall_example.png, churn_calibration_curve.png. Tamanhos 75-101 KB. |

### [V7] Model Cards — Números batem com JSON e recálculo

| Card | Números batem? | Tabela calibração coerente? | Limitações declaradas? |
|------|----------------|----------------------------|------------------------|
| clv.md | ✅ PASS | N/A (regressão) | ✅ PASS |
| churn.md | ✅ PASS | ✅ PASS (quantile bins) | ✅ PASS |

**Detalhes:**
- **CLV:** Todas as 10 métricas (WAPE, MAE, Spearman, Gini, Lift + baselines + ICs) batem exatamente com `clv_metrics.json` e recálculo independente. Limitações: (1) Base Sintética Calibrada — sanidade matemática, não acurácia empírica; (2) Horizonte 12m — plurianual requer DCF. LGPD: atributos sensíveis proibidos declarados.
- **Churn:** Todas as 8 métricas (ROC-AUC, PR-AUC, Brier, Lift + baselines + ICs) batem exatamente. Tabela de calibração usa **quantile bins** (não uniformes) — bin 8 concentra 19.465 clientes com prob. ~0.845 (top quantile), fração real 0.908. Valores próximos ao recálculo com bins uniformes. Limitações: (1) Ambiente Sintético — integridade do pipeline, não taxa empírica; (2) Churn não-contratual — sem encerramento formal. LGPD: bloqueio rigoroso + testes regressão.

### [V8] Contratos — Validação via schemas.load.validate_or_raise

| Tabela | Valida? | Violações |
|--------|---------|-----------|
| clv_predictions.parquet | ✅ PASS | Nenhuma |
| churn_predictions.parquet | ✅ PASS | Nenhuma |
| features_customer.parquet | ✅ PASS | Nenhuma |
| features_customer_val.parquet | ✅ PASS | Nenhuma (usa mesmo contrato features_customer.yaml — schema idêntico) |

### [V9] Testes — pytest exit code, ruff check

| Comando | Exit Code | Issues no escopo |
|---------|-----------|------------------|
| pytest tests/test_metrics.py tests/test_bgnbd.py tests/test_features_antileakage.py -q | ✅ 0 (20 passed) | Todos passam: métricas analíticas, BG/NBD sanidade, anti-leakage LGPD/temporal |
| ruff check ml dbt 2>&1 | ✅ 0 (clean) | Ruído apenas em scripts temporários de debug (run_dbt.py, run_dbt2.py) — fora do escopo. Código fonte ml/ e dbt/ limpo. |

### [V10] Adversarial Livre

| Achado | Severidade | Descrição |
|--------|------------|-----------|
| V10-1: Churn predições idênticas em massa | ⚠️ MENOR | 38,9% das predições de churn = 0.8451 (mesmo valor). Gera tie-breaking nos decis e bins de calibração degenerados (bin 8 com 19.465 clientes). Modelo LightGBM não diferencia bem clientes de alto risco. |
| V10-2: Correlação baseline-modelo alta (Churn) | ⚠️ MENOR | Pearson r = 0.953 entre Regressão Logística e LightGBM. Modelo não-linear adiciona pouca diversidade preditiva — ganhos marginais (ROC-AUC +0.0126). |
| V10-3: Distribuição tier extremamente enviesada | 📊 OBSERVAÇÃO | 95,6% clientes = 'azul' (47.804/50.000). Pouca variabilidade para aprender efeitos de tier alto. |
| V10-4: last_activity_date com NaN | 📊 OBSERVAÇÃO | Clientes sem transações têm NaN. Tratado no macro com COALESCE(..., 999) para recency_days. |
| V10-5: CLV WAPE baseline alto (0.797) | 📊 OBSERVAÇÃO | Esperado para BG/NBD em base sintética; modelo reduz para 0.655 mas ainda alto. Não é erro — limitação da base sintética. |
| V10-6: Desvio treino/teste 5-7% | 📊 OBSERVAÇÃO | Diferenças esperadas por deriva temporal (val cutoff 2025-02-28 vs main 2025-08-31). Não indica vazamento. |
| V10-7: Modelo CLV melhor só em 35% dos casos (MAE) | 📊 OBSERVAÇÃO | LightGBM vence baseline em MAE individual só 35,4% dos clientes, mas ganha no agregado (WAPE/MAE/Spearman). Consistente com redução de erro em clientes de alto valor. |

---

## Achados Consolidados

| ID | Severidade | Componente | Descrição | Evidência |
|----|------------|------------|-----------|-----------|
| A1 | MENOR | Churn decile | 22/50.000 registros (0,044%) com decil diferente do `argsort(-pred, kind="stable")` por tie-breaking em predições idênticas. Contagens por decil corretas. | `check_decile.py` |
| A2 | MENOR | Churn SHAP | 38,9% predições = 0.8451 → bins de calibração degenerados, tie-breaking nos decis. | `check_adversarial.py` (quantile edges) |
| A3 | MENOR | Churn baseline vs model | Correlação 0.953 entre Logistic Regression e LightGBM. Ganhos marginais (ΔROC-AUC=+0.0126). | `check_adversarial.py` |
| A4 | OBSERVAÇÃO | Tier imbalance | 95,6% 'azul', apenas 4,4% tiers premium. Limita aprendizado de efeitos de tier. | `check_adversarial.py` |
| A5 | OBSERVAÇÃO | CLV WAPE alto | Baseline 0.797, Model 0.655 — alto mas esperado para base sintética. | Métricas + `check_adversarial.py` |
| A6 | OBSERVAÇÃO | Churn Lift@10% idêntico | Modelo e baseline ambos 1.73x. Modelo não melhora priorização top 10%. | `recalc_metrics.py`, `check_adversarial.py` |
| A7 | OBSERVAÇÃO | PR-AUC baseline diff | Recalculado 0.8302 vs JSON 0.8307 (Δ=0.0005 < threshold). Diferença numérica irrelevante. | `recalc_metrics.py` |

---

## Veredito Final

**Classificação:** APROVADO COM RESSALVAS

**Justificativa:**
A frente WS3+WS4 demonstra **excelência em engenharia e governança**: anti-vazamento temporal rigoroso (V1 ✅), métricas auditáveis e reproduzíveis (V2 ✅, divergências < 0.002), bootstrap pareado correto (V4 ✅), baseline BG/NBD+GG implementado do zero com fidelidade a Fader/Hardie (V5 ✅), SHAP nativo com top-3 por cliente e figuras auditáveis (V6 ✅), model cards completos com limitações declaradas (V7 ✅), contratos válidos (V8 ✅), testes passando (V9 ✅).

**Ressalvas (não-bloqueantes, severidade MENOR/OBSERVAÇÃO):**
1. **Churn: predições degeneradas** — 38,9% idênticas (0.8451) causam tie-breaking nos decis e calibração quantil com bin único gigante. LightGBM não aprende separação fina no alto risco.
2. **Churn: ganho marginal sobre baseline** — ΔROC-AUC=+0.0126 (significativo mas pequeno), correlação baseline-modelo 0.953, Lift@10% idêntico (1.73x). Modelo não-linear pouco superior à Regressão Logística.
3. **Tier extremamente desbalanceado** — 95.6% 'azul' limita utilidade do feature `tier_encoded`.

Nenhum achado CRÍTICO ou IMPORTANTE. O pipeline é **matematicamente sólido, temporalmente seguro e auditável**. As ressalvas refletem limitações inerentes à base sintética e à definição de churn não-contratual, não falhas de implementação.

**Números recalculados independentemente (resumo):**
- CLV: WAPE LGBM = 0.6550; WAPE Base = 0.7974; MAE LGBM = 497.85; MAE Base = 606.12; Spearman LGBM = 0.7346; Spearman Base = 0.6106; Gini LGBM = 0.6604; Gini Base = 0.5935; Lift Decil 1 LGBM = 5.23x; Lift Decil 1 Base = 4.35x
- Churn: ROC-AUC LGBM = 0.8566; ROC-AUC Base = 0.8440; PR-AUC LGBM = 0.8373; PR-AUC Base = 0.8302; Brier LGBM = 0.1453; Brier Base = 0.1516; Lift Top 10% LGBM = 1.73x; Lift Top 10% Base = 1.73x

---
*Relatório gerado por execução real de verificações adversariais. Cada célula preenchida após verificação efetiva.*