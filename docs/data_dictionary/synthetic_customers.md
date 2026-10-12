# `synthetic_customers`

> **Descrição:** Clientes sintéticos cadastrados no Azul Fidelidade (população da base sintética do Projeto Aura 2.0)  
> **Granularidade:** um registro por cliente sintético  
> **Produzida por:** synthetic.generate  
> **Consumidores:** dbt: curated -> analytics, ml.fairness, synthetic.fidelity_report

| Coluna | Tipo | Nulo? | Descrição | Unidade | Fonte | Sensível | Exemplo |
|---|---|---|---|---|---|---|---|
| `customer_id` | string | não | Identificador único do cliente sintético | - | synthetic.generate | não | `C000001` |
| `archetype` | string | não | Família latente de comportamento do cliente | - | synthetic.generate (config/generator.yaml: archetypes) | não | `executivo_recorrente` |
| `faixa_etaria` | string | sim | Faixa etária do cliente (apenas para auditoria de viés/LGPD - NUNCA usada como feature) | - | synthetic.generate | 🔴 sim | `35-44` |
| `genero` | string | sim | Gênero declarado pelo cliente (apenas para auditoria de viés/LGPD - NUNCA usada como feature) | - | synthetic.generate | 🔴 sim | `M` |
| `regiao` | string | não | Região geográfica brasileira de residência (apenas para auditoria de viés/LGPD) | - | synthetic.generate | 🔴 sim | `Sudeste` |
| `home_airport` | string | não | Aeroporto base mais frequente (código IATA) | - | synthetic.generate | não | `VCP` |
| `join_date` | datetime | não | Data de cadastro no programa Azul Fidelidade | - | synthetic.generate | não | `2023-09-15 00:00:00` |
| `current_tier` | string | não | Nível vigente no encerramento da janela (azul, topazio, safira, diamante, diamante_unique) | - | synthetic.generate | não | `azul` |
| `status` | string | não | Status cadastral do cliente ao fim da janela (ativo ou inativo) | - | synthetic.generate | não | `ativo` |

## Checagens de contrato

- **unicidade:** `customer_id`
- **não nulo:** `customer_id`
- **não nulo:** `archetype`
- **não nulo:** `regiao`
- **não nulo:** `home_airport`
- **não nulo:** `join_date`
- **não nulo:** `current_tier`
- **não nulo:** `status`
