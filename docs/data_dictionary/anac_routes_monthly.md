# `anac_routes_monthly`

> **Descrição:** Agregado mensal de rotas do mercado doméstico regular brasileiro (ANAC voos_basica) com métricas de mercado e Azul  
> **Granularidade:** uma rota (origem-destino OACI) por mês  
> **Produzida por:** ingestion.curate  
> **Consumidores:** synthetic.generate, snowflake, ml.impact, app

| Coluna | Tipo | Nulo? | Descrição | Unidade | Fonte | Sensível | Exemplo |
|---|---|---|---|---|---|---|---|
| `id_rota_mes` | string | não | Identificador único da rota e mês (origem-destino:AAAA-MM) | - | data/raw/anac/voos_basica/*.parquet | não | `SBKP-SBRJ:2024-01` |
| `rota` | string | não | Par de códigos OACI origem e destino (ex: SBKP-SBRJ) | - | data/raw/anac/voos_basica/*.parquet | não | `SBKP-SBRJ` |
| `origem_oaci` | string | não | Código OACI do aeródromo de origem | - | data/raw/anac/voos_basica/*.parquet | não | `SBKP` |
| `destino_oaci` | string | não | Código OACI do aeródromo de destino | - | data/raw/anac/voos_basica/*.parquet | não | `SBRJ` |
| `ano` | int | não | Ano de referência do voo | ano | data/raw/anac/voos_basica/*.parquet | não | `2024` |
| `mes` | int | não | Mês de referência do voo (1 a 12) | mes | data/raw/anac/voos_basica/*.parquet | não | `1` |
| `ano_mes` | string | não | Ano e mês no formato AAAA-MM | - | data/raw/anac/voos_basica/*.parquet | não | `2024-01` |
| `total_pax_pagos` | float | não | Total de passageiros pagos transportados na rota no mês por todas as empresas aéreas | passageiros | data/raw/anac/voos_basica/*.parquet | não | `15420.0` |
| `total_assentos_ofertados` | float | não | Total de assentos ofertados na rota no mês pelo mercado | assentos | data/raw/anac/voos_basica/*.parquet | não | `18500.0` |
| `total_decolagens` | float | não | Total de decolagens realizadas na rota no mês | voos | data/raw/anac/voos_basica/*.parquet | não | `112.0` |
| `azul_pax_pagos` | float | não | Passageiros pagos transportados pela Azul Linhas Aéreas (sg_empresa_icao='AZU') na rota no mês | passageiros | data/raw/anac/voos_basica/*.parquet | não | `6200.0` |
| `azul_assentos_ofertados` | float | não | Assentos ofertados pela Azul na rota no mês | assentos | data/raw/anac/voos_basica/*.parquet | não | `7400.0` |
| `azul_decolagens` | float | não | Decolagens realizadas pela Azul na rota no mês | voos | data/raw/anac/voos_basica/*.parquet | não | `44.0` |
| `azul_share_pax` | float | não | Participação de mercado da Azul em passageiros pagos na rota no mês (0 a 1) | ratio | data/raw/anac/voos_basica/*.parquet | não | `0.402` |
| `azul_share_decolagens` | float | não | Participação de mercado da Azul em decolagens na rota no mês (0 a 1) | ratio | data/raw/anac/voos_basica/*.parquet | não | `0.393` |
| `azul_load_factor` | float | não | Taxa de ocupação da Azul na rota (pax / assentos) ou 0 se sem voos | ratio | data/raw/anac/voos_basica/*.parquet | não | `0.838` |
| `total_load_factor` | float | não | Taxa de ocupação geral do mercado na rota (total pax / total assentos) | ratio | data/raw/anac/voos_basica/*.parquet | não | `0.833` |
| `has_azul` | bool | não | Indica se a Azul operou na rota durante o mês | - | data/raw/anac/voos_basica/*.parquet | não | `True` |

## Checagens de contrato

- **unicidade:** `id_rota_mes`
- **não nulo:** `id_rota_mes`
- **não nulo:** `rota`
- **não nulo:** `origem_oaci`
- **não nulo:** `destino_oaci`
- **não nulo:** `ano`
- **não nulo:** `mes`
- **não nulo:** `ano_mes`
- **não nulo:** `total_pax_pagos`
- **não nulo:** `total_decolagens`
- **não nulo:** `has_azul`
- **no_negative_pax**: `MIN(total_pax_pagos) >= 0` — Total de passageiros não pode ser negativo
- **timeline_bounds**: `MIN(ano_mes) >= '2023-09' AND MAX(ano_mes) <= '2026-08'` — Dados fora da janela temporal do projeto (2023-09 a 2026-08)
