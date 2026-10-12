# `score_av`

> **Descrição:** Score de Alto Valor canônico composto (CLV 60%, RFM 20%, Potencial 20%)  
> **Granularidade:** um registro por cliente na coorte de análise  
> **Produzida por:** ml.segmentation.score_av  
> **Consumidores:** ml.segmentation, agent.pipeline, app

| Coluna | Tipo | Nulo? | Descrição | Unidade | Fonte | Sensível | Exemplo |
|---|---|---|---|---|---|---|---|
| `customer_id` | string | não | Identificador único do cliente | - | data/analytics/features_customer.parquet | não | `C000001` |
| `pct_clv` | float | não | Posto percentilar da predição de CLV 12m (0.0 a 1.0) | percentil | ml/segmentation/score_av.py | não | `0.85` |
| `pct_rfm` | float | não | Posto percentilar do escore composto RFM padronizado (0.0 a 1.0) | percentil | ml/segmentation/score_av.py | não | `0.72` |
| `pct_potential` | float | não | Posto percentilar do indicador de potencial/headroom de crescimento (0.0 a 1.0) | percentil | ml/segmentation/score_av.py | não | `0.68` |
| `score_av` | float | não | Score de Alto Valor consolidado (0.60*pct_clv + 0.20*pct_rfm + 0.20*pct_potential) | score | ml/segmentation/score_av.py | não | `0.79` |
| `alto_valor` | bool | não | Indicador booleano de cliente pertencente ao segmento de alto valor | - | ml/segmentation/score_av.py | não | `True` |
| `percentile_rank` | float | não | Rank percentilar final do score_av na base | percentil | ml/segmentation/score_av.py | não | `0.92` |

## Checagens de contrato

- **unicidade:** `customer_id`
- **não nulo:** `customer_id`
- **não nulo:** `pct_clv`
- **não nulo:** `pct_rfm`
- **não nulo:** `pct_potential`
- **não nulo:** `score_av`
- **não nulo:** `alto_valor`
- **não nulo:** `percentile_rank`
- **score_av_bounds**: `MIN(score_av) >= 0.0 AND MAX(score_av) <= 1.0` — ScoreAV deve estar delimitado no intervalo [0, 1]
