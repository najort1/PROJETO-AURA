# `synthetic_transactions`

> **Descrição:** Transações financeiras e de fidelidade realizadas pelos clientes (compras de passagens, ancillaries, acúmulos e resgates)  
> **Granularidade:** uma transação  
> **Produzida por:** synthetic.generate  
> **Consumidores:** dbt: curated -> analytics, synthetic.fidelity_report, ml.clv

| Coluna | Tipo | Nulo? | Descrição | Unidade | Fonte | Sensível | Exemplo |
|---|---|---|---|---|---|---|---|
| `transaction_id` | string | não | Identificador único da transação | - | synthetic.generate | não | `TX0000001` |
| `customer_id` | string | não | Identificador do cliente que realizou a transação | - | synthetic.generate | não | `C000001` |
| `transaction_date` | datetime | não | Data e hora da transação | - | synthetic.generate | não | `2024-03-10 14:20:00` |
| `transaction_type` | string | não | Natureza da transação (compra de passagem, serviço ancillary, acúmulo externo ou resgate) | - | synthetic.generate | não | `compra_passagem` |
| `amount_brl` | float | não | Valor monetário pago em reais (BRL) | BRL | synthetic.generate | não | `450.5` |
| `ancillary_type` | string | sim | Subtipo de serviço ancillary (quando transaction_type == servico_ancillary) | - | synthetic.generate | não | `espaco_azul` |
| `pontos_azul_acumulados` | int | não | Pontos Azul acumulados (multiplicador do nível vigente: 1x, 2x, 3x, 4x por R$ gasto) | pontos | synthetic.generate (config/program_rules.yaml) | não | `1800` |
| `pontos_qualificaveis_acumulados` | int | não | Pontos qualificáveis creditados (R$ 1 gasto em passagens/serviços = 1 QP; 10:1 cartão/clube) | pontos_qualificaveis | synthetic.generate (config/program_rules.yaml: AF-QUALIFYING-POINTS) | não | `450` |
| `pontos_azul_resgatados` | int | não | Pontos Azul debitados em resgates (mínimo 3.000 pts/trecho, teto pelo nível) | pontos | synthetic.generate (config/program_rules.yaml: AF-REDEMPTION) | não | `0` |
| `flight_id` | string | sim | Identificador do voo associado à compra aérea (quando aplicável) | - | synthetic.generate | não | `FL0000001` |

## Checagens de contrato

- **unicidade:** `transaction_id`
- **não nulo:** `transaction_id`
- **não nulo:** `customer_id`
- **não nulo:** `transaction_date`
- **não nulo:** `transaction_type`
- **não nulo:** `amount_brl`
- **não nulo:** `pontos_azul_acumulados`
- **não nulo:** `pontos_qualificaveis_acumulados`
- **não nulo:** `pontos_azul_resgatados`
