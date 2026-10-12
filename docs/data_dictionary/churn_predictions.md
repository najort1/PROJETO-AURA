# `churn_predictions`

> **Descrição:** Predições individuais de probabilidade de evasão (Churn 12m) comparando Baseline Regressão Logística vs LightGBM  
> **Granularidade:** um cliente na coorte de teste/avaliação  
> **Produzida por:** ml.churn.train  
> **Consumidores:** ml.segmentation, agent.pipeline, app, docs.model_cards

| Coluna | Tipo | Nulo? | Descrição | Unidade | Fonte | Sensível | Exemplo |
|---|---|---|---|---|---|---|---|
| `customer_id` | string | não | Identificador único do cliente | - | data/analytics/features_customer.parquet | não | `C000001` |
| `churn_prob_baseline` | float | não | Probabilidade prevista de evasão em 12 meses pelo modelo baseline de Regressão Logística (0.0 a 1.0) | probabilidade | ml/churn/train.py | não | `0.42` |
| `churn_prob_model` | float | não | Probabilidade prevista de evasão em 12 meses pelo modelo final LightGBM (0.0 a 1.0) | probabilidade | ml/churn/train.py | não | `0.68` |
| `target_churn_12m` | int | não | Rótulo real observado de evasão (inatividade > 2x intervalo individual e >= 180 dias) | binario | data/analytics/features_customer.parquet | não | `1` |
| `decile_model` | int | não | Decil de classificação de risco do modelo final (1 = top 10% maior probabilidade de churn) | decil | ml/churn/train.py | não | `1` |

## Checagens de contrato

- **unicidade:** `customer_id`
- **não nulo:** `customer_id`
- **não nulo:** `churn_prob_baseline`
- **não nulo:** `churn_prob_model`
- **não nulo:** `target_churn_12m`
- **não nulo:** `decile_model`
- **valid_probabilities**: `MIN(churn_prob_model) >= 0.0 AND MAX(churn_prob_model) <= 1.0` — Probabilidade de evasão fora do intervalo válido [0, 1]
