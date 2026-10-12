# `friction_map`

> **Descrição:** Mapa analítico consolidado de atritos por aspecto, intensidade média e tendência temporal por semestre  
> **Granularidade:** um aspecto por semestre  
> **Produzida por:** ml.sentiment.friction_map  
> **Consumidores:** synthetic.generate, agent.pipeline, app, ml.impact

| Coluna | Tipo | Nulo? | Descrição | Unidade | Fonte | Sensível | Exemplo |
|---|---|---|---|---|---|---|---|
| `friction_id` | string | não | Identificador único da linha (aspecto + semestre) | - | ml/sentiment/friction_map.py | não | `atraso_2024S1` |
| `aspect` | string | não | Aspecto do atrito analisado (atraso, bagagem, atendimento, app_checkin, resgate_milhas, preco, conforto) | - | ml/sentiment/friction_map.py | não | `atraso` |
| `semester` | string | não | Semestre do período de referência (ex: 2024-S1) | - | ml/sentiment/friction_map.py | não | `2024-S1` |
| `mention_count` | int | não | Total de avaliações que mencionaram este aspecto no semestre | contagem | ml/sentiment/friction_map.py | não | `85` |
| `negative_count` | int | não | Quantidade de avaliações com polaridade negativa neste aspecto no semestre | contagem | ml/sentiment/friction_map.py | não | `62` |
| `neutral_count` | int | não | Quantidade de avaliações com polaridade neutra neste aspecto no semestre | contagem | ml/sentiment/friction_map.py | não | `10` |
| `positive_count` | int | não | Quantidade de avaliações com polaridade positiva neste aspecto no semestre | contagem | ml/sentiment/friction_map.py | não | `13` |
| `negative_rate` | float | não | Taxa de menções negativas sobre o total de menções do aspecto no semestre | taxa | ml/sentiment/friction_map.py | não | `0.729` |
| `semester_intensity` | float | não | Intensidade calculada do atrito no semestre (combinação de prevalência e negatividade, 0 a 1) | indice_0_1 | ml/sentiment/friction_map.py | não | `0.684` |
| `mean_intensity` | float | não | Intensidade média global deste aspecto ao longo de toda a janela histórica | indice_0_1 | ml/sentiment/friction_map.py | não | `0.65` |
| `delta_previous` | float | não | Variação da intensidade em relação ao semestre imediatamente anterior | delta | ml/sentiment/friction_map.py | não | `0.042` |
| `trend_direction` | string | não | Direção da tendência temporal do atrito (crescente, decrescente, estavel) | - | ml/sentiment/friction_map.py | não | `crescente` |
| `aspect_weight` | float | não | Peso calibrado do aspecto exportado para friction_weights.json (soma dos pesos = 1.0) | peso_normalizado | ml/sentiment/friction_map.py | não | `0.22` |

## Checagens de contrato

- **unicidade:** `friction_id`
- **não nulo:** `friction_id`
- **não nulo:** `aspect`
- **não nulo:** `semester`
- **não nulo:** `mention_count`
- **não nulo:** `negative_count`
- **não nulo:** `neutral_count`
- **não nulo:** `positive_count`
- **não nulo:** `negative_rate`
- **não nulo:** `semester_intensity`
- **não nulo:** `mean_intensity`
- **não nulo:** `delta_previous`
- **não nulo:** `trend_direction`
- **não nulo:** `aspect_weight`
- **valid_semester_intensity_range**: `MIN(semester_intensity) >= 0.0 AND MAX(semester_intensity) <= 1.0` — Intensidade semestral deve estar entre 0.0 e 1.0
- **valid_aspect_weight_range**: `MIN(aspect_weight) >= 0.0 AND MAX(aspect_weight) <= 1.0` — Peso de atrito deve estar entre 0.0 e 1.0
