# `sentiment_reviews`

> **Descrição:** Corpus sintético rotulado de avaliações em PT-BR por aspecto e polaridade (100% sintético para validação do pipeline de WS6 do Projeto Aura 2.0)  
> **Granularidade:** uma avaliação  
> **Produzida por:** ml.sentiment.corpus  
> **Consumidores:** ml.sentiment.approaches, ml.sentiment.friction_map, ml.sentiment.pipeline

| Coluna | Tipo | Nulo? | Descrição | Unidade | Fonte | Sensível | Exemplo |
|---|---|---|---|---|---|---|---|
| `review_id` | string | não | Identificador único da avaliação sintética | - | ml/sentiment/corpus.py | não | `REV-000001` |
| `review_date` | datetime | não | Data e hora simuladas da avaliação (janela 2023-09-01 a 2026-08-31) | - | ml/sentiment/corpus.py | não | `2024-05-10 14:30:00` |
| `channel` | string | não | Canal genérico de origem da avaliação (sem uso de marcas reais) | - | ml/sentiment/corpus.py | não | `portal_reclamacoes` |
| `text` | string | não | Texto em português brasileiro da avaliação, com ruído, gírias ou ironia | - | ml/sentiment/corpus.py | não | `Voo atrasou mais de 2 horas e o atendimento no balcão foi péssimo.` |
| `aspects_mentioned` | string | não | Lista de aspectos mencionados no texto, separados por vírgula | - | ml/sentiment/corpus.py | não | `atraso,atendimento` |
| `overall_sentiment` | string | não | Sentimento geral consolidado da avaliação | - | ml/sentiment/corpus.py | não | `negativo` |
| `has_atraso` | int | não | Indicador binário de menção ao aspecto atraso de voo | binario | ml/sentiment/corpus.py | não | `1` |
| `has_bagagem` | int | não | Indicador binário de menção ao aspecto bagagem / extravio / danos | binario | ml/sentiment/corpus.py | não | `0` |
| `has_atendimento` | int | não | Indicador binário de menção ao aspecto atendimento (bordo, solo, SAC) | binario | ml/sentiment/corpus.py | não | `1` |
| `has_app_checkin` | int | não | Indicador binário de menção ao aspecto app móvel / check-in digital | binario | ml/sentiment/corpus.py | não | `0` |
| `has_resgate_milhas` | int | não | Indicador binário de menção ao aspecto resgate de pontos e milhas | binario | ml/sentiment/corpus.py | não | `0` |
| `has_preco` | int | não | Indicador binário de menção ao aspecto preço de passagens e taxas | binario | ml/sentiment/corpus.py | não | `0` |
| `has_conforto` | int | não | Indicador binário de menção ao aspecto conforto a bordo e poltronas | binario | ml/sentiment/corpus.py | não | `0` |
| `polarity_atraso` | string | não | Polaridade atribuída ao aspecto atraso | - | ml/sentiment/corpus.py | não | `negativo` |
| `polarity_bagagem` | string | não | Polaridade atribuída ao aspecto bagagem | - | ml/sentiment/corpus.py | não | `ausente` |
| `polarity_atendimento` | string | não | Polaridade atribuída ao aspecto atendimento | - | ml/sentiment/corpus.py | não | `negativo` |
| `polarity_app_checkin` | string | não | Polaridade atribuída ao aspecto app / check-in | - | ml/sentiment/corpus.py | não | `ausente` |
| `polarity_resgate_milhas` | string | não | Polaridade atribuída ao aspecto resgate de milhas | - | ml/sentiment/corpus.py | não | `ausente` |
| `polarity_preco` | string | não | Polaridade atribuída ao aspecto preço | - | ml/sentiment/corpus.py | não | `ausente` |
| `polarity_conforto` | string | não | Polaridade atribuída ao aspecto conforto | - | ml/sentiment/corpus.py | não | `ausente` |
| `is_ironic` | bool | não | Indica se o texto contém ironia ou sarcasmo deliberado | booleano | ml/sentiment/corpus.py | não | `False` |
| `noise_level` | string | não | Grau de ruído textual (baixo, medio, alto) decorrente de gírias e pontuação | - | ml/sentiment/corpus.py | não | `baixo` |

## Checagens de contrato

- **unicidade:** `review_id`
- **não nulo:** `review_id`
- **não nulo:** `review_date`
- **não nulo:** `channel`
- **não nulo:** `text`
- **não nulo:** `aspects_mentioned`
- **não nulo:** `overall_sentiment`
- **não nulo:** `has_atraso`
- **não nulo:** `has_bagagem`
- **não nulo:** `has_atendimento`
- **não nulo:** `has_app_checkin`
- **não nulo:** `has_resgate_milhas`
- **não nulo:** `has_preco`
- **não nulo:** `has_conforto`
- **não nulo:** `polarity_atraso`
- **não nulo:** `polarity_bagagem`
- **não nulo:** `polarity_atendimento`
- **não nulo:** `polarity_app_checkin`
- **não nulo:** `polarity_resgate_milhas`
- **não nulo:** `polarity_preco`
- **não nulo:** `polarity_conforto`
- **não nulo:** `is_ironic`
- **não nulo:** `noise_level`
- **min_corpus_size**: `COUNT(*) >= 1000` — O corpus deve conter pelo menos 1.000 avaliações sintéticas rotuladas
- **date_within_synthetic_window**: `MIN(review_date) >= TIMESTAMP '2023-09-01' AND MAX(review_date) <= TIMESTAMP '2026-08-31 23:59:59'` — Avaliações com datas fora da janela sintética de 36 meses (2023-09-01 a 2026-08-31)
