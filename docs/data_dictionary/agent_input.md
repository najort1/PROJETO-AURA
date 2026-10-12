# `agent_input`

> **Descrição:** Contrato de entrada para o motor de recomendação e redação do agente (WS7)  
> **Granularidade:** um registro por cliente na coorte de retenção  
> **Produzida por:** ml (features, clv, churn, segmentation/personas, sentiment)  
> **Consumidores:** agent.pipeline, agent.eligibility, agent.composer, app

| Coluna | Tipo | Nulo? | Descrição | Unidade | Fonte | Sensível | Exemplo |
|---|---|---|---|---|---|---|---|
| `customer_id` | string | não | Identificador único do cliente | - | data/curated/synthetic/customers.parquet | não | `C000001` |
| `tier` | string | não | Nível atual no Azul Fidelidade (azul, topazio, safira, diamante, diamante_unique) | - | data/analytics/features_customer.parquet | não | `safira` |
| `persona` | string | não | Persona atribuída pelo modelo de segmentação | - | data/analytics/customer_personas.parquet | não | `maximizador_milhas` |
| `risk_state` | string | não | Estado de risco e valor (risco_alto_valor_alto, risco_medio_valor_alto, risco_baixo_potencial_alto, risco_baixo_estavel) | - | data/analytics/customer_scores.parquet | não | `risco_alto_valor_alto` |
| `pontos_qualificaveis_12m` | int | não | Pontos qualificáveis acumulados nos últimos 12 meses | pontos | data/analytics/features_customer.parquet | não | `9500` |
| `trechos_12m` | int | não | Trechos voados nos últimos 12 meses | trechos | data/analytics/features_customer.parquet | não | `9` |
| `gastos_12m_brl` | float | não | Gastos aéreos em passagens e serviços elegíveis nos últimos 12 meses (BRL) | BRL | data/analytics/features_customer.parquet | não | `4500.0` |
| `saldo_pontos` | int | não | Saldo atual de Pontos Azul disponíveis para resgate | pontos | data/analytics/features_customer.parquet | não | `75000` |
| `pontos_expirando_30d` | int | não | Pontos a expirar nos próximos 30 dias | pontos | data/analytics/features_customer.parquet | não | `12000` |
| `meta_proximo_nivel_pct` | float | não | Percentual atingido da meta de qualificação para o próximo nível (0.0 a 1.0+) | ratio | data/analytics/features_customer.parquet | não | `0.85` |
| `churn_prob` | float | não | Probabilidade prevista de evasão (churn) no horizonte de 12 meses | probabilidade | data/analytics/customer_scores.parquet | não | `0.72` |
| `clv_12m_previsto` | float | não | Customer Lifetime Value previsto para os próximos 12 meses (BRL) | BRL | data/analytics/customer_scores.parquet | não | `5400.0` |
| `alto_valor` | bool | não | Indicador binário de cliente de alto valor (definido pelo limiar de Pareto/ScoreAV) | - | data/analytics/customer_scores.parquet | não | `True` |
| `atritos_dominantes` | string | sim | Atritos dominantes detectados (ex.: 'resgate', 'atraso', 'bagagem', 'atendimento') | - | data/analytics/sentiment_aspects.parquet | não | `resgate` |
| `rota_favorita` | string | sim | Trecho mais frequente voado pelo cliente (ex.: 'VCP-SDU') | - | data/analytics/features_customer.parquet | não | `VCP-SDU` |
| `beneficio_nao_utilizado` | string | sim | Benefício contratual do nível vigente não utilizado pelo cliente | - | data/analytics/features_customer.parquet | não | `espaco_azul` |
| `shap_top3` | string | sim | JSON array com os 3 principais fatores de risco/CLV explicados por SHAP | - | data/analytics/customer_scores.parquet | não | `["queda_frequencia_voos", "atrito_resgate", "inatividade_recente"]` |

## Checagens de contrato

- **unicidade:** `customer_id`
- **não nulo:** `customer_id`
- **não nulo:** `tier`
- **não nulo:** `persona`
- **não nulo:** `risk_state`
- **não nulo:** `saldo_pontos`
- **não nulo:** `churn_prob`
- **não nulo:** `clv_12m_previsto`
- **não nulo:** `alto_valor`
