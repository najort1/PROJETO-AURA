# `clv_predictions`

> **Descrição:** Predições individuais de Customer Lifetime Value (CLV 12m) comparando Baseline BG/NBD+GG vs LightGBM  
> **Granularidade:** um cliente na coorte de teste/avaliação  
> **Produzida por:** ml.clv.train  
> **Consumidores:** ml.segmentation, agent.pipeline, app, docs.model_cards

| Coluna | Tipo | Nulo? | Descrição | Unidade | Fonte | Sensível | Exemplo |
|---|---|---|---|---|---|---|---|
| `customer_id` | string | não | Identificador único do cliente | - | data/analytics/features_customer.parquet | não | `C000001` |
| `clv_baseline_12m` | float | não | Valor monetário previsto em 12 meses pelo modelo probabilístico Baseline BG/NBD + Gamma-Gamma (BRL) | BRL | ml/clv/train.py | não | `4120.5` |
| `clv_predicted_12m` | float | não | Valor monetário previsto em 12 meses pelo modelo Gradient Boosting LightGBM (BRL) | BRL | ml/clv/train.py | não | `4680.0` |
| `target_clv_12m` | float | não | Valor realizado de receita no horizonte futuro de 12 meses (target legítimo da coorte) | BRL | data/analytics/features_customer.parquet | não | `4950.0` |
| `error_baseline` | float | não | Erro absoluto do baseline (\|target - baseline\|) | BRL | ml/clv/train.py | não | `829.5` |
| `error_model` | float | não | Erro absoluto do modelo final LightGBM (\|target - model\|) | BRL | ml/clv/train.py | não | `270.0` |
| `decile_model` | int | não | Decil de classificação preditiva do modelo final (1 = top 10% maior valor previsto) | decil | ml/clv/train.py | não | `1` |

## Checagens de contrato

- **unicidade:** `customer_id`
- **não nulo:** `customer_id`
- **não nulo:** `clv_baseline_12m`
- **não nulo:** `clv_predicted_12m`
- **não nulo:** `target_clv_12m`
- **não nulo:** `decile_model`
- **non_negative_clv**: `MIN(clv_predicted_12m) >= 0.0` — Predição de CLV não pode conter valores negativos
