# `customers_scores`

> **Descrição:** Visão analítica integrada de clientes, predições (CLV/Churn), ScoreAV, persona e atributos operacionais  
> **Granularidade:** um registro por cliente na coorte de análise  
> **Produzida por:** ml.segmentation.score_av  
> **Consumidores:** app.views.01_carteira, app.views.03_cliente_360, app.views.04_agente, app.views.06_simulador

| Coluna | Tipo | Nulo? | Descrição | Unidade | Fonte | Sensível | Exemplo |
|---|---|---|---|---|---|---|---|
| `customer_id` | string | não | Identificador único do cliente | - | data/analytics/features_customer.parquet | não | `C000001` |
| `tier` | string | não | Nível no programa Azul Fidelidade | - | data/analytics/features_customer.parquet | não | `safira` |
| `persona` | string | não | Persona comportamental identificada | - | ml/segmentation/personas.py | não | `maximizador_milhas` |
| `clv_12m_previsto` | float | não | CLV previsto em 12 meses (BRL) | BRL | data/analytics/clv_predictions.parquet | não | `6200.0` |
| `churn_prob` | float | não | Probabilidade prevista de churn em 12 meses | probabilidade | data/analytics/churn_predictions.parquet | não | `0.35` |
| `valor_em_risco` | float | não | Valor financeiro em risco = CLV × P(churn) | BRL | ml/segmentation/score_av.py | não | `2170.0` |
| `score_av` | float | não | Score de Alto Valor consolidado | score | ml/segmentation/score_av.py | não | `0.78` |
| `alto_valor` | bool | não | Flag de cliente pertencente à faixa de alto valor | - | ml/segmentation/score_av.py | não | `True` |
| `risk_state` | string | não | Estado conjunto de risco e valor | - | ml/segmentation/score_av.py | não | `risco_alto_valor_alto` |
| `gastos_12m_brl` | float | não | Gastos totais do cliente nos últimos 12 meses (BRL) | BRL | data/analytics/features_customer.parquet | não | `5400.0` |
| `recencia_dias` | int | não | Dias desde a última atividade até o cutoff | dias | data/analytics/features_customer.parquet | não | `25` |
| `frequencia_voos` | int | não | Frequência total de voos no período de 12 meses | voos | data/analytics/features_customer.parquet | não | `12` |
| `trechos_12m` | int | não | Número de trechos voados nos últimos 12 meses | trechos | data/analytics/features_customer.parquet | não | `12` |
| `saldo_pontos` | int | não | Saldo de Pontos Azul acumulados | pontos | data/analytics/features_customer.parquet | não | `45000` |
| `pontos_expirando_30d` | int | não | Pontos com expiração prevista nos próximos 30 dias | pontos | data/analytics/features_customer.parquet | não | `5000` |
| `pontos_qualificaveis_12m` | int | não | Pontos qualificáveis acumulados em 12 meses | pontos | data/analytics/features_customer.parquet | não | `9500` |
| `meta_proximo_nivel_pct` | float | não | Proporção atingida da meta para o próximo nível | ratio | data/analytics/features_customer.parquet | não | `0.85` |
| `faixa_etaria` | string | não | Faixa etária do cliente (utilizada apenas na auditoria e visualização) | - | data/curated/synthetic/customers.parquet | 🔴 sim | `30-49` |
| `genero` | string | não | Gênero do cliente (utilizado apenas na auditoria e visualização) | - | data/curated/synthetic/customers.parquet | 🔴 sim | `Feminino` |
| `regiao` | string | não | Região geográfica de residência | - | data/curated/synthetic/customers.parquet | 🔴 sim | `Sudeste` |
| `rota_favorita` | string | não | Rota mais frequente voada pelo cliente | - | data/analytics/features_customer.parquet | não | `VCP-SDU` |
| `atritos_dominantes` | string | não | Atrito predominante nas interações do cliente | - | data/analytics/features_customer.parquet | não | `atraso` |
| `beneficio_nao_utilizado` | string | sim | Benefício contratual do nível que o cliente ainda não usufruiu | - | data/analytics/features_customer.parquet | não | `espaco_azul` |
| `shap_top3` | string | não | JSON array com os 3 principais fatores explicativos SHAP | - | data/analytics/clv_shap.parquet | não | `[{"factor": "queda_frequencia_voos", "shap_value": 0.25}]` |

## Checagens de contrato

- **unicidade:** `customer_id`
- **não nulo:** `customer_id`
- **não nulo:** `tier`
- **não nulo:** `persona`
- **não nulo:** `clv_12m_previsto`
- **não nulo:** `churn_prob`
- **não nulo:** `valor_em_risco`
- **não nulo:** `score_av`
- **não nulo:** `alto_valor`
- **não nulo:** `risk_state`
