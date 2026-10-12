# `customer_timeline`

> **Descrição:** Linha do tempo de eventos de relacionamento (voos, atritos, resgates, mudanças de categoria)  
> **Granularidade:** um evento por cliente  
> **Produzida por:** ml.segmentation.score_av  
> **Consumidores:** app.views.03_cliente_360

| Coluna | Tipo | Nulo? | Descrição | Unidade | Fonte | Sensível | Exemplo |
|---|---|---|---|---|---|---|---|
| `customer_id` | string | não | Identificador único do cliente | - | data/analytics/features_customer.parquet | não | `C000001` |
| `data` | string | não | Data do evento no formato ISO (YYYY-MM-DD) | - | data/curated/synthetic/ | não | `2025-08-15` |
| `tipo` | string | não | Tipo do evento de relacionamento | - | data/curated/synthetic/ | não | `voo` |
| `titulo` | string | não | Título resumido do evento para exibição no card da timeline | - | ml/segmentation/timeline.py | não | `Voo VCP-SDU` |
| `detalhe` | string | não | Descrição detalhada do evento ocorrido | - | ml/segmentation/timeline.py | não | `Trecho operado pontualmente em classe Executiva` |
| `impacto` | string | não | Impacto percebido na experiência do cliente (positivo, negativo, neutro) | - | ml/segmentation/timeline.py | não | `positivo` |

## Checagens de contrato

- **não nulo:** `customer_id`
- **não nulo:** `data`
- **não nulo:** `tipo`
- **não nulo:** `titulo`
- **não nulo:** `detalhe`
- **não nulo:** `impacto`
