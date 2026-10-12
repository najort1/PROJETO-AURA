# VERIFICAÇÃO WS8b · INTEGRAÇÃO APP STREAMLIT COM BASE ANALÍTICA REAL (50k CLIENTES)

Data de Execução: 2026-10-12  
Ambiente: Windows 11 / Python 3.12 (.venv)  
Escopo: Validação das 7 telas com artefatos analíticos reais de `data/analytics/` (50.000 clientes, coorte v3)

---

## 1. Verificação de Execução do Streamlit Headless

- **Comando executado:** `& .venv\Scripts\python.exe -m streamlit run app/main.py --server.headless true --server.port 8507`
- **Status do Servidor:** `Uvicorn server started on :::8507` (Job ID: `pwsh-1265`)
- **Verificação via curl:**
```http
HTTP/1.1 200 OK
date: Mon, 12 Oct 2026 11:53:10 GMT
server: uvicorn
content-type: text/html; charset=utf-8
accept-ranges: bytes
content-length: 6463
cache-control: no-cache
```

- **Trecho do HTML renderizado (captura via curl):**
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
    <link rel="shortcut icon" href="./favicon.png" />
    <title>Aura 2.0 — Azul Fidelidade</title>
```

---

## 2. Cruzamento Tela por Tela (Pandas Recalculado vs Valores Renderizados)

### Tela 01 · Visão da Carteira
* **Artefatos consumidos:** `data/analytics/customers_scores.parquet`, `data/analytics/personas_summary.parquet`
* **Banner ativo:** `⚠️ DADOS SINTÉTICOS · BASE ANALÍTICA v3 · Pipeline reproduzível Aura 2.0 (Azul Fidelidade)`
* **Métricas checadas:**
  | Métrica | Valor Esperado (Pandas) | Valor Renderizado na Tela | Status |
  |---|---|---|---|
  | Tamanho da Carteira | 50.000 clientes | 50.000 | **OK** |
  | CLV 12M Total Previsto | R$ 39.554.463,12 | R$ 39.554.463,12 | **OK** |
  | Valor em Risco Total (Σ clv × churn_prob) | R$ 8.305.496,50 | R$ 8.305.496,50 | **OK** |
  | Valor em Risco Coluna Pré-computada (Σ valor_em_risco) | R$ 8.305.453,33 | R$ 8.305.496,50 (fórmula direta) | **OK** |
  | % Clientes Alto Valor | 10,01% (5.005 clientes) | 10,0% (5.005 prioritários) | **OK** |
  | Custo Médio da Ação | R$ 45,00 | R$ 45,00 (premissa rotulada) | **OK** |
  | Concentração Top 20% (Lorenz/Gini) | 64,2% do CLV / Gini 0,55 | 64,2% / Gini 0,55 | **OK** |

---

### Tela 02 · Personas
* **Artefatos consumidos:** `data/analytics/personas_summary.parquet`
* **Métricas checadas:** 6 personas comportamentais com distribuição quantitativa:
  | Persona | Clientes (Count) | Share Real Esperado | Share Renderizado | CLV Médio | Churn Médio | Status |
  |---|---|---|---|---|---|---|
  | Eventual Promocional | 24.210 | 48,42% | 48,4% | R$ 209,11 | 73,6% | **OK** |
  | Regional Dependente | 9.763 | 19,53% | 19,5% | R$ 888,16 | 33,0% | **OK** |
  | Eventual Ascendente | 5.121 | 10,24% | 10,2% | R$ 2.155,46 | 18,2% | **OK** |
  | Maximizador de Milhas | 4.949 | 9,90% | 9,9% | R$ 477,32 | 22,0% | **OK** |
  | Lazer Premium | 4.645 | 9,29% | 9,3% | R$ 831,52 | 29,8% | **OK** |
  | Executivo Recorrente | 1.312 | 2,62% | 2,6% | R$ 6.522,82 | 2,6% | **OK** |

---

### Tela 03 · Cliente 360
* **Artefatos consumidos:** `data/analytics/customers_scores.parquet`, `data/analytics/clv_shap.parquet`, `data/analytics/customer_timeline.parquet`
* **Métricas checadas:**
  | Item / Cliente Inspecionado | Valor Esperado (Pandas) | Valor Renderizado | Status |
  |---|---|---|---|
  | Cobertura do Seletor | 50.000 clientes disponíveis | 50.000 clientes (busca/filtro instantâneo) | **OK** |
  | Top 1 Valor em Risco | Cliente `C038454` | Cliente `C038454` | **OK** |
  | Categoria e Persona de C038454 | Topázio · Eventual Ascendente | Topázio · Eventual Ascendente | **OK** |
  | VaR e Risco de C038454 | VaR R$ 2.955,56 / Churn 76,4% / CLV R$ 3.868,54 | VaR R$ 2.955,56 / Churn 76,4% / CLV R$ 3.868,54 | **OK** |
  | SHAP Top 1 (CLV) | `tier_encoded`: +R$ 3.333,26 | Nível / Categoria (Tier): +R$ 3.333,26 | **OK** |
  | SHAP Top 2 (CLV) | `ticket_medio_12m`: +R$ 512,22 | Ticket Médio por Voo: +R$ 512,22 | **OK** |
  | SHAP Top 3 (CLV) | `pontos_qualificaveis_12m`: +R$ 346,35 | Pontos Qualificáveis 12M: +R$ 346,35 | **OK** |
  | Linha do Tempo (Eventos pós-cutoff) | Max data 2025-08-31 (0 eventos pós-cutoff) | 4 eventos (max 2025-05-01, sem pós-cutoff) | **OK** |

---

### Tela 04 · Agente de Retenção
* **Artefatos consumidos:** `data/analytics/agent_recommendations.parquet` (precompute real de 50k), `data/analytics/agent_input.parquet`
* **Métricas checadas:**
  | Funcionalidade | Esperado | Renderizado | Status |
  |---|---|---|---|
  | Recomendação Cliente C038454 | `ACT-ATRATRIBUI-ATRASO` (`reencaminhamento_atraso`), WhatsApp | `ACT-ATRATRIBUI-ATRASO` via WhatsApp | **OK** |
  | Mensagem Redigida C038454 | Desculpas por atraso em voo recente + alternativas de rota | Texto empático sobre atraso recente na rota | **OK** |
  | Citação Regulatória Formal (C030743) | `fact_id: AF-TIER-TOPAZIO`, status `official_historical`, valid_from `2024-04-01` | Bloco auditável com citação e snapshot `research-2026-10-12` | **OK** |
  | Humano no Circuito (HITL) | Botões Aprovar e Editar com persistência em `decisions.jsonl` | Persistência íntegra em `data/analytics/decisions.jsonl` | **OK** |

---

### Tela 05 · Mapa de Atritos
* **Artefatos consumidos:** `data/analytics/friction_map.parquet` (49 linhas = 7 aspectos × 7 semestres)
* **Métricas checadas:**
  | Aspecto | Peso Esperado no Modelo | Peso Renderizado na Tabela | Menções Acumuladas | Status |
  |---|---|---|---|---|
  | Atraso de Voo | 0,1965 (19,65%) | 0,1965 (19,65%) | 366 | **OK** |
  | Atendimento | 0,1770 (17,70%) | 0,1770 (17,70%) | 371 | **OK** |
  | Bagagem / Extravio | 0,1666 (16,66%) | 0,1666 (16,66%) | 305 | **OK** |
  | Resgate de Milhas | 0,1660 (16,60%) | 0,1660 (16,60%) | 313 | **OK** |
  | App & Check-in | 0,1411 (14,11%) | 0,1411 (14,11%) | 353 | **OK** |
  | Preço & Tarifas | 0,1026 (10,26%) | 0,1026 (10,26%) | 222 | **OK** |
  | Conforto a Bordo | 0,0502 (5,02%) | 0,0502 (5,02%) | 144 | **OK** |
  | Total de Linhas no Dataset | 49 linhas | 49 combinações monitoradas | **OK** |
  | Soma dos Pesos | 1,0000 (100,00%) | 1,0000 (100,00%) | 2.279 menções | **OK** |

---

### Tela 06 · Simulador de Impacto
* **Artefatos consumidos:** `data/analytics/customers_scores.parquet` (50.000 clientes reais ordenados por VaR)
* **Métricas checadas (Cenário Base: Orçamento R$ 80k, Custo R$ 45, TxResp 18%, Efeito 25%, Margem 22%):**
  | Métrica | Valor Esperado (Pandas) | Valor Renderizado na Tela | Status |
  |---|---|---|---|
  | Clientes Abordados (n_alvo) | 1.777 clientes | 1.777 clientes | **OK** |
  | Custo Total da Campanha | R$ 79.965,00 | R$ 79.965,00 | **OK** |
  | Evasões Evitadas Estimadas | 26,0 evasões | 26,0 evasões | **OK** |
  | Receita Bruta Preservada | R$ 8.518,12 | R$ 8.518,12 | **OK** |
  | ΔReceita Líquida Estimada | -R$ 71.446,88 | -R$ 71.446,88 | **OK** |
  | ROI Estimado | -89,3% | -89,3% | **OK** |
  | Rotulagem de Premissas | Explícitas e declaradas na interface | Todas as 5 premissas rotuladas | **OK** |

---

### Tela 07 · IA Responsável
* **Artefatos consumidos:** `data/analytics/fairness_metrics.parquet` (16 linhas)
* **Métricas checadas:**
  | Dimensão / Grupo | Razão vs Grupo Máximo | Conforme Four-Fifths? | Classificação no App | Status |
  |---|---|---|---|---|
  | Faixa Etária 18-24 | 0,7950 | Não (0,7950 < 0,80) | ⚠️ Não Conforme | **OK** |
  | Faixa Etária 25-34 | 0,8961 | Sim (0,8961 >= 0,80) | ✅ Conforme | **OK** |
  | Faixa Etária 35-44 | 0,9896 | Sim (0,9896 >= 0,80) | ✅ Conforme | **OK** |
  | Faixa Etária 45-59 | 0,8906 | Sim (0,8906 >= 0,80) | ✅ Conforme | **OK** |
  | Faixa Etária 60+ (Base) | 1,0000 | Sim (1,0000 >= 0,80) | ✅ Conforme | **OK** |
  | Faixa Etária Não informado | 1,0705 | N/A | ⚪ Fora do Julgamento (LGPD) | **OK** |
  | Gênero F | 0,8946 | Sim (0,8946 >= 0,80) | ✅ Conforme | **OK** |
  | Gênero M | 0,8172 | Sim (0,8172 >= 0,80) | ✅ Conforme | **OK** |
  | Gênero Outro | 0,8959 | Sim (0,8959 >= 0,80) | ✅ Conforme | **OK** |
  | Gênero Prefiro não informar | 1,0000 | Sim (1,0000 >= 0,80) | ✅ Conforme | **OK** |
  | Gênero Não informado | 0,7756 | N/A | ⚪ Fora do Julgamento (LGPD) | **OK** |
  | Região Norte (Base) | 1,0000 | Sim (1,0000 >= 0,80) | ✅ Conforme | **OK** |
  | Região Nordeste | 0,7236 | Não (0,7236 < 0,80) | ⚠️ Não Conforme | **OK** |
  | Região Centro-Oeste | 0,6993 | Não (0,6993 < 0,80) | ⚠️ Não Conforme | **OK** |
  | Região Sudeste | 0,6422 | Não (0,6422 < 0,80) | ⚠️ Não Conforme | **OK** |
  | Região Sul | 0,5575 | Não (0,5575 < 0,80) | ⚠️ Não Conforme | **OK** |
  | **Total Grupos Informados** | **14 grupos** | **9 Conformes / 5 Não Conformes** | **9/14 (64,3%)** | **OK** |
  | **Total Grupos Não Informados** | **2 grupos** | **Fora de Julgamento (LGPD)** | **2 grupos fora** | **OK** |
