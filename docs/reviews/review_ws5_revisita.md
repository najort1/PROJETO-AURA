# Re-Visão Independente WS5 · Verificação das Correções Lead Pós-Revisão A/B

**Data:** 2025-02-18  
**Avaliador:** Re-Visor Independente (Mega-Brain)  
**Status:** Concluído — APROVADO  

---

## 1. Contexto e Escopo
A revisão WS5-B reprovou por 1 apontamento IMPORTANTE:
- **B4-01**: `customer_timeline.parquet` continha 4.802 eventos de voo com `departure_date > cutoff (2025-08-31)`, vazando dados operacionais futuros.

A revisão WS5-A apontou 1 MENOR:
- Divergência de valores nominais BRL na tabela de Pareto em `docs/segmentation_report.md`.

O Lead aplicou correções. Esta auditoria valida de forma independente:
1. **[V1 · timeline]** Filtro de cutoff em `ml/segmentation/timeline.py`, guarda fail-loud e métricas de `data/analytics/customer_timeline.parquet`.
2. **[V2 · Pareto doc]** Recálculo exato da curva de Pareto em `data/analytics/customers_scores.parquet` e confronto linha a linha com `docs/segmentation_report.md`.
3. **[V3 · regressão]** Existência de teste de regressão em `tests/test_segmentation.py` e execução de testes.

---

## 2. V1 · Auditoria da Timeline e Cutoff

### 2.1 Análise de Código (`ml/segmentation/timeline.py`)
- **Filtro de voos aplicado**: Linha 48 contém explicitamente:
  ```python
  tx_flights = tx_flights[pd.to_datetime(tx_flights["departure_date"]) <= pd.Timestamp(cutoff_date)]
  ```
  Garantindo que voos com compra anterior a 2025-08-31, mas partida posterior, sejam descartados da linha do tempo operacional.
- **Guarda Fail-Loud**: Linhas 141–146 contêm:
  ```python
  if not out_df.empty:
      max_data = pd.to_datetime(out_df["data"]).max()
      if max_data > pd.Timestamp(cutoff_date):
          raise ValueError(
              f"Vazamento temporal na timeline: max(data)={max_data.date()} > cutoff {cutoff_date}"
          )
  ```
  Se qualquer evento com `data > cutoff` emergir, o pipeline falha ruidosamente.

### 2.2 Auditoria do Artefato (`data/analytics/customer_timeline.parquet`)
Recálculo via pandas executado diretamente sobre o parquet gerado:
- **Total de eventos**: **277.705** (esperado: 277.705) — **CONFIRMADO**
- **Clientes únicos**: **30.271** (esperado: ~30.271) — **CONFIRMADO**
- **MAX(data)**: **2025-08-31** (esperado: exatamente 2025-08-31) — **CONFIRMADO**
- **Eventos com data > 2025-08-31**: **0** — **CONFIRMADO**
- **Delta vs pré-correção**: Queda de exatamente **4.802** eventos (282.507 → 277.705).
- **Tipos dos eventos descartados**: Todos os 4.802 eventos removidos eram exclusivamente do tipo `voo` (200.797 pré-filtro → 195.995 pós-filtro).

**Conclusão V1**: **APROVADO** (100% em conformidade com as regras de negócio e livre de vazamento temporal).

---

## 3. V2 · Auditoria da Curva de Pareto

### 3.1 Recálculo em `data/analytics/customers_scores.parquet`
Ordenação decrescente por `score_av` e soma cumulativa de `clv_12m_previsto` sobre os 50.000 clientes:
- **Total CLV 12m Previsto**: **R$ 39.554.463,12**
- **Top 5%** (k=2.500): R$ 12.061.692,86 (30,49%), limiar `score_av` = 0,9336
- **Top 10%** (k=5.000): R$ 18.577.090,30 (46,97%), limiar `score_av` = 0,8840
- **Top 15%** (k=7.500): R$ 22.701.826,22 (57,39%), limiar `score_av` = 0,8369
- **Top 20%** (k=10.000): R$ 25.663.633,91 (64,88%), limiar `score_av` = 0,7924

### 3.2 Confronto Linha a Linha com `docs/segmentation_report.md` (§3)
Comparação realizada contra a tabela do relatório corrigido:
- **Receita Total citada**: R$ 39.554.463,12 — **100% Idêntico**
- **Top 5%**: 2.500 clientes | R$ 12.061.692,86 | 30,49% | Limiar 0,9336 — **100% Idêntico**
- **Top 10%**: 5.000 clientes | R$ 18.577.090,30 | 46,97% | Limiar 0,8840 — **100% Idêntico**
- **Top 15%**: 7.500 clientes | R$ 22.701.826,22 | 57,39% | Limiar 0,8369 — **100% Idêntico**
- **Top 20%**: 10.000 clientes | R$ 25.663.633,91 | 64,88% | Limiar 0,7924 — **100% Idêntico**

A nota explicativa sobre os empates no limiar (5.005 clientes classificados com `alto_valor = True` / 10,01%) também foi verificada e documentada com precisão.

**Conclusão V2**: **APROVADO** (100% de paridade entre dados e documentação).

---

## 4. V3 · Auditoria de Regressão e Suíte de Testes

### 4.1 Existência de Teste de Regressão
- **Status**: **NÃO EXISTE** teste unitário de regressão dedicado em `tests/test_segmentation.py` para o cutoff da timeline (`departure_date <= cutoff` / `max(data) <= cutoff`).
- **Classificação**: **MENOR**.
- **Mitigação Atual**: A função `build_customer_timeline` em `ml/segmentation/timeline.py` implementa uma guarda fail-loud (`ValueError` se `max(data) > cutoff`), e `test_real_artifacts_contracts_validation` valida o schema do contrato. Contudo, recomenda-se adicionar futuramente um teste unitário explícito na suíte para blindagem permanente.

### 4.2 Execução da Suíte de Testes
Comando executado:
```powershell
& .venv\Scripts\python.exe -m pytest tests/test_segmentation.py -q
```
**Resultado**:
- `7 passed in 5.91s` (100% verde).

**Conclusão V3**: Suíte 100% verde; ausência de teste específico classificada como MENOR (não impeditivo).

---

## 5. Veredito Final

| Item | Descrição | Status | Detalhes |
|---|---|:---:|---|
| **V1** | Correção Cutoff Timeline | **OK** | 277.705 eventos, 30.271 clientes, MAX(data)=2025-08-31, 0 eventos futuros, -4.802 voos |
| **V2** | Paridade Pareto doc §3 | **OK** | 100% de paridade linha a linha (Top 5%, 10%, 15%, 20% e total BRL) |
| **V3** | Teste Regressão Cutoff | **MENOR** | Teste dedicado ausente (guarda fail-loud ativa no código); pytest 7/7 verde |

**VEREDITO GLOBAL:** **APROVADO**
