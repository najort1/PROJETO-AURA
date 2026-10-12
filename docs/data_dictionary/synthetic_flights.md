# `synthetic_flights`

> **Descrição:** Voos individuais operados pela Azul na malha doméstica na janela de simulação (2023-09-01 a 2026-08-31)  
> **Granularidade:** um voo por trecho operado  
> **Produzida por:** synthetic.generate  
> **Consumidores:** dbt: curated -> analytics, synthetic.fidelity_report

| Coluna | Tipo | Nulo? | Descrição | Unidade | Fonte | Sensível | Exemplo |
|---|---|---|---|---|---|---|---|
| `flight_id` | string | não | Identificador único do voo sintético | - | synthetic.generate | não | `FL0000001` |
| `flight_number` | string | não | Número de voo com prefixo AD (Azul Linhas Aéreas) | - | synthetic.generate | não | `AD4102` |
| `origin_airport` | string | não | Código IATA do aeroporto de origem | - | synthetic.generate | não | `VCP` |
| `destination_airport` | string | não | Código IATA do aeroporto de destino | - | synthetic.generate | não | `SDU` |
| `departure_date` | datetime | não | Data e horário programados de partida | - | synthetic.generate | não | `2024-03-15 08:30:00` |
| `distance_km` | float | não | Distância ortodrômica do trecho em quilômetros | km | synthetic.generate | não | `410.0` |
| `scheduled_departure` | datetime | não | Horário previsto de partida | - | synthetic.generate | não | `2024-03-15 08:30:00` |
| `actual_departure` | datetime | não | Horário real observado de partida | - | synthetic.generate | não | `2024-03-15 08:42:00` |
| `delay_minutes` | int | não | Minutos de atraso na partida (>= 0) | minutos | synthetic.generate | não | `12` |
| `has_delay` | int | não | Indicador binário de atraso relevante (> 15 minutos, critério ANAC) | binario | synthetic.generate | não | `0` |
| `is_cancelled` | int | não | Indicador binário de cancelamento do voo | binario | synthetic.generate | não | `0` |

## Checagens de contrato

- **unicidade:** `flight_id`
- **não nulo:** `flight_id`
- **não nulo:** `flight_number`
- **não nulo:** `origin_airport`
- **não nulo:** `destination_airport`
- **não nulo:** `departure_date`
- **não nulo:** `distance_km`
- **não nulo:** `scheduled_departure`
- **não nulo:** `actual_departure`
- **não nulo:** `delay_minutes`
- **não nulo:** `has_delay`
- **não nulo:** `is_cancelled`
