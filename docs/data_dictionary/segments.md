# `segments`

> **Descrição:** Atribuição de clusters não-supervisionados (KMeans, GMM) e mapeamento em segmentos  
> **Granularidade:** um registro por cliente na coorte de análise  
> **Produzida por:** ml.segmentation.cluster  
> **Consumidores:** ml.segmentation.personas, agent.pipeline, app

| Coluna | Tipo | Nulo? | Descrição | Unidade | Fonte | Sensível | Exemplo |
|---|---|---|---|---|---|---|---|
| `customer_id` | string | não | Identificador único do cliente | - | data/analytics/features_customer.parquet | não | `C000001` |
| `cluster_kmeans` | int | não | Identificador do cluster atribuído pelo algoritmo KMeans | id | ml/segmentation/cluster.py | não | `0` |
| `cluster_gmm` | int | não | Identificador do componente gaussiano atribuído pelo GMM | id | ml/segmentation/cluster.py | não | `0` |
| `segment_id` | int | não | Identificador do segmento consolidado | id | ml/segmentation/cluster.py | não | `0` |
| `segment_name` | string | não | Nome semântico do segmento / persona correspondente | - | ml/segmentation/cluster.py | não | `executivo_recorrente` |

## Checagens de contrato

- **unicidade:** `customer_id`
- **não nulo:** `customer_id`
- **não nulo:** `cluster_kmeans`
- **não nulo:** `cluster_gmm`
- **não nulo:** `segment_id`
- **não nulo:** `segment_name`
