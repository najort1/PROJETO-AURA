# `synthetic_interactions`

> **Descrição:** Interações de atendimento, pontos de contato nos canais e atritos vivenciados pelos clientes  
> **Granularidade:** uma interação  
> **Produzida por:** synthetic.generate  
> **Consumidores:** dbt: curated -> analytics, synthetic.fidelity_report, ml.churn, agent.pipeline

| Coluna | Tipo | Nulo? | Descrição | Unidade | Fonte | Sensível | Exemplo |
|---|---|---|---|---|---|---|---|
| `interaction_id` | string | não | Identificador único da interação | - | synthetic.generate | não | `INT0000001` |
| `customer_id` | string | não | Identificador do cliente que interagiu | - | synthetic.generate | não | `C000001` |
| `interaction_date` | datetime | não | Data e hora do contato ou ocorrência do atrito | - | synthetic.generate | não | `2024-05-12 16:45:00` |
| `channel` | string | não | Canal da interação (app, web, call_center, aeroporto, whatsapp) | - | synthetic.generate | não | `app` |
| `aspect` | string | não | Aspecto central abordado (atraso, bagagem, app_checkin, resgate_milhas, atendimento, preco, nenhum) | - | synthetic.generate (config/generator.yaml: dominant_frictions) | não | `atraso` |
| `has_friction` | int | não | Indicador binário de experiência com atrito ou insatisfação | binario | synthetic.generate | não | `1` |
| `friction_intensity` | float | não | Intensidade contínua calculada do atrito (escala 0.0 a 1.0) | escala_0_a_1 | synthetic.generate | não | `0.75` |
| `nps_rating` | float | sim | Nota de satisfação declarada no NPS (0 a 10); missing MAR documentado (~58% nulo) | nota_0_a_10 | synthetic.generate (config/generator.yaml: missing_data) | não | `8.0` |
| `resolution_status` | string | não | Status do caso (resolvido, nao_resolvido, pendente) | - | synthetic.generate | não | `resolvido` |

## Checagens de contrato

- **unicidade:** `interaction_id`
- **não nulo:** `interaction_id`
- **não nulo:** `customer_id`
- **não nulo:** `interaction_date`
- **não nulo:** `channel`
- **não nulo:** `aspect`
- **não nulo:** `has_friction`
- **não nulo:** `friction_intensity`
- **não nulo:** `resolution_status`
