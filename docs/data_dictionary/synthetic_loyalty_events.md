# `synthetic_loyalty_events`

> **Descrição:** Eventos de fidelidade na conta do cliente: upgrades, downgrades, renovações de tier e expiração de lotes de pontos  
> **Granularidade:** um evento de fidelidade por ocorrência  
> **Produzida por:** synthetic.generate  
> **Consumidores:** dbt: curated -> analytics, synthetic.fidelity_report, agent.eligibility

| Coluna | Tipo | Nulo? | Descrição | Unidade | Fonte | Sensível | Exemplo |
|---|---|---|---|---|---|---|---|
| `event_id` | string | não | Identificador único do evento de fidelidade | - | synthetic.generate | não | `EV0000001` |
| `customer_id` | string | não | Identificador do cliente afetado | - | synthetic.generate | não | `C000001` |
| `event_date` | datetime | não | Data e hora da ocorrência do evento | - | synthetic.generate | não | `2024-06-15 10:00:00` |
| `event_type` | string | não | Tipo de evento de fidelidade (upgrade, downgrade, retention de tier ou expiracao de lote) | - | synthetic.generate | não | `tier_upgrade` |
| `previous_tier` | string | não | Nível no programa antes da alteração | - | synthetic.generate | não | `azul` |
| `new_tier` | string | não | Nível no programa após a alteração | - | synthetic.generate | não | `topazio` |
| `trigger_reason` | string | não | Regra determinante do evento (pontos qualificaveis, trechos, gasto direto ou expiracao de ciclo) | - | synthetic.generate (config/program_rules.yaml) | não | `qualifying_points_reached` |
| `qualifying_points_at_event` | int | não | Saldo acumulado de pontos qualificáveis no ciclo no momento do evento | pontos_qualificaveis | synthetic.generate | não | `6100` |
| `segments_at_event` | int | não | Contagem de trechos voados no ciclo no momento do evento | trechos | synthetic.generate | não | `7` |
| `spend_brl_at_event` | float | não | Gasto acumulado em compras elegíveis no ciclo no momento do evento | BRL | synthetic.generate | não | `6500.0` |

## Checagens de contrato

- **unicidade:** `event_id`
- **não nulo:** `event_id`
- **não nulo:** `customer_id`
- **não nulo:** `event_date`
- **não nulo:** `event_type`
- **não nulo:** `previous_tier`
- **não nulo:** `new_tier`
- **não nulo:** `trigger_reason`
- **não nulo:** `qualifying_points_at_event`
- **não nulo:** `segments_at_event`
- **não nulo:** `spend_brl_at_event`
