# `features_customer`

> **Descrição:** Features agregadas por cliente na coorte de análise com corte estrito anti-vazamento  
> **Granularidade:** um cliente  
> **Produzida por:** dbt: marts.features_customer  
> **Consumidores:** ml.clv, ml.churn, ml.segmentation, agent.input, app

| Coluna | Tipo | Nulo? | Descrição | Unidade | Fonte | Sensível | Exemplo |
|---|---|---|---|---|---|---|---|
| `customer_id` | string | não | Identificador único do cliente | - | data/curated/synthetic/customers.parquet | não | `C000001` |
| `tier` | string | não | Nível atual no programa de fidelidade (azul, topazio, safira, diamante, diamante_unique) | - | dbt: features_customer | não | `safira` |
| `recency_days` | int | não | Dias decorridos entre a última transação/atividade e o corte temporal (2025-08-31) | dias | dbt: features_customer | não | `45` |
| `frequency_3m` | int | não | Número de transações aéreas nos últimos 3 meses antes do cutoff | transacoes | dbt: features_customer | não | `3` |
| `frequency_6m` | int | não | Número de transações aéreas nos últimos 6 meses antes do cutoff | transacoes | dbt: features_customer | não | `6` |
| `frequency_12m` | int | não | Número de transações aéreas nos últimos 12 meses antes do cutoff | transacoes | dbt: features_customer | não | `12` |
| `trechos_12m` | int | não | Trechos aéreos voados nos últimos 12 meses antes do cutoff | trechos | dbt: features_customer | não | `12` |
| `monetary_12m` | float | não | Receita total gerada nos últimos 12 meses anteriores ao cutoff (BRL) | BRL | dbt: features_customer | não | `4850.5` |
| `gastos_12m_brl` | float | não | Gastos aéreos elegíveis em passagens e adicionais nos últimos 12 meses (BRL) | BRL | dbt: features_customer | não | `4850.5` |
| `ticket_medio_12m` | float | não | Gasto médio por transação/trecho nos 12 meses anteriores ao cutoff (BRL) | BRL | dbt: features_customer | não | `404.21` |
| `frequency_trend` | float | não | Tendência de aceleração/desaceleração da frequência (recente vs histórico anual) | ratio | dbt: features_customer | não | `0.9231` |
| `frequency_volatility` | float | não | Volatilidade/irregularidade calculada da frequência de compras nos períodos | coeficiente | dbt: features_customer | não | `0.1428` |
| `share_rotas_troncais` | float | não | Proporção de voos realizados em rotas troncais de alta densidade | ratio | dbt: features_customer | não | `0.75` |
| `share_resgate` | float | não | Participação de resgates de passagens sobre o total de viagens realizadas | ratio | dbt: features_customer | não | `0.1428` |
| `avg_advance_booking_days` | float | não | Média de dias de antecedência entre compra da passagem e data de embarque | dias | dbt: features_customer | não | `18.5` |
| `rota_favorita` | string | não | Par de aeroportos de rota mais frequente no histórico de 12m | - | dbt: features_customer | não | `VCP-SDU` |
| `pontos_qualificaveis_12m` | int | não | Total de pontos qualificáveis creditados nos 12 meses anteriores ao corte | pontos | dbt: features_customer | não | `8500` |
| `saldo_pontos` | int | não | Saldo consolidado de pontos disponíveis para resgate até o cutoff | pontos | dbt: features_customer | não | `45000` |
| `pontos_expirando_30d` | int | não | Estimativa de pontos acumulados sujeitos a expiração nos próximos 30 dias | pontos | dbt: features_customer | não | `3600` |
| `meta_proximo_nivel_pct` | float | não | Percentual atingido da meta de qualificação para o próximo nível vigente | ratio | dbt: features_customer | não | `0.7083` |
| `beneficio_nao_utilizado` | string | não | Benefício contratual elegível não exercido pelo cliente no ano | - | dbt: features_customer | não | `espaco_azul` |
| `days_since_last_interaction` | int | não | Dias decorridos desde o último contato ou interação de atendimento | dias | dbt: features_customer | não | `21` |
| `atritos_atraso_12m` | int | não | Número de ocorrências de atrito por atraso de voo nos últimos 12m | ocorrencias | dbt: features_customer | não | `1` |
| `atritos_bagagem_12m` | int | não | Número de ocorrências de atrito por extravio ou dano de bagagem nos últimos 12m | ocorrencias | dbt: features_customer | não | `0` |
| `atritos_app_checkin_12m` | int | não | Número de ocorrências de atrito no canal app/check-in digital nos últimos 12m | ocorrencias | dbt: features_customer | não | `0` |
| `atritos_resgate_milhas_12m` | int | não | Número de ocorrências de atrito ao tentar resgatar milhas/passagens nos últimos 12m | ocorrencias | dbt: features_customer | não | `0` |
| `atritos_atendimento_12m` | int | não | Número de ocorrências de insatisfação com atendimento nos últimos 12m | ocorrencias | dbt: features_customer | não | `0` |
| `atritos_preco_12m` | int | não | Número de reclamações ou atritos relacionados a preço e tarifas nos últimos 12m | ocorrencias | dbt: features_customer | não | `0` |
| `total_atritos_12m` | int | não | Total acumulado de eventos de atrito vivenciados nos últimos 12 meses | ocorrencias | dbt: features_customer | não | `1` |
| `last_activity_date` | date | sim | Data da última transação ou voo anterior ao marco temporal | - | dbt: features_customer | não | `2025-07-15` |
| `target_clv_12m` | float | não | Alvo legítimo: receita realizada no horizonte futuro de 12 meses (2025-09-01 a 2026-08-31) | BRL | dbt: features_customer | não | `5200.0` |
| `target_churn_12m` | int | não | Alvo legítimo: inatividade superior a 2x o intervalo típico e >= 180 dias sem compras | binario | dbt: features_customer | não | `0` |

## Checagens de contrato

- **unicidade:** `customer_id`
- **não nulo:** `customer_id`
- **não nulo:** `tier`
- **não nulo:** `recency_days`
- **não nulo:** `frequency_12m`
- **não nulo:** `monetary_12m`
- **não nulo:** `target_clv_12m`
- **não nulo:** `target_churn_12m`
- **no_future_information**: `MAX(last_activity_date) <= DATE '2025-08-31'` — Feature contém informação posterior ao cutoff temporal (vazamento)
