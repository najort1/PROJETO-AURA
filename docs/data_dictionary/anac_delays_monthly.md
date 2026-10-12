# `anac_delays_monthly`

> **Descrição:** Série histórica mensal da taxa de atraso (>15 minutos) do sistema aeroportuário nacional (ANAC movimentação)  
> **Granularidade:** um mês  
> **Produzida por:** ingestion.curate  
> **Consumidores:** synthetic.generate, snowflake, ml.sentiment, app

| Coluna | Tipo | Nulo? | Descrição | Unidade | Fonte | Sensível | Exemplo |
|---|---|---|---|---|---|---|---|
| `id_ano_mes` | string | não | Identificador único do mês (AAAA-MM) | - | data/raw/anac/movimentacao/*.parquet | não | `2024-01` |
| `ano` | int | não | Ano do movimento operacional | ano | data/raw/anac/movimentacao/*.parquet | não | `2024` |
| `mes` | int | não | Mês do movimento operacional (1 a 12) | mes | data/raw/anac/movimentacao/*.parquet | não | `1` |
| `ano_mes` | string | não | Ano e mês no formato AAAA-MM | - | data/raw/anac/movimentacao/*.parquet | não | `2024-01` |
| `total_movimentos` | int | não | Total de movimentos de aeronaves registrados com horário previsto e calço/toque | movimentos | data/raw/anac/movimentacao/*.parquet | não | `187310` |
| `movimentos_atrasados` | int | não | Quantidade de movimentos com atraso superior a 15 minutos (dt/hh_calco vs dt/hh_previsto > 900s) | movimentos | data/raw/anac/movimentacao/*.parquet | não | `42825` |
| `taxa_atraso` | float | não | Taxa mensal de atraso superior a 15 min (movimentos atrasados / total movimentos) | taxa | data/raw/anac/movimentacao/*.parquet | não | `0.2286` |
| `cobertura` | string | não | Declaração de abrangência temporal e limitação da fonte (2019-03 a 2025-12; 2026 indisponível) | - | ingestion/curate.py | não | `2019-03_a_2025-12` |

## Checagens de contrato

- **unicidade:** `id_ano_mes`
- **não nulo:** `id_ano_mes`
- **não nulo:** `ano`
- **não nulo:** `mes`
- **não nulo:** `ano_mes`
- **não nulo:** `total_movimentos`
- **não nulo:** `movimentos_atrasados`
- **não nulo:** `taxa_atraso`
- **não nulo:** `cobertura`
- **taxa_bounds**: `MIN(taxa_atraso) >= 0.0 AND MAX(taxa_atraso) <= 1.0` — Taxa de atraso fora dos limites [0, 1]
