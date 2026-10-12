# `anac_airports`

> **Descrição:** Cadastro de aeródromos brasileiros com coordenadas geográficas e macrorregião derivada da UF  
> **Granularidade:** um aeródromo (código OACI)  
> **Produzida por:** ingestion.curate  
> **Consumidores:** synthetic.generate, snowflake, ml.fairness, app

| Coluna | Tipo | Nulo? | Descrição | Unidade | Fonte | Sensível | Exemplo |
|---|---|---|---|---|---|---|---|
| `codigo_oaci` | string | não | Código ICAO/OACI de 4 letras do aeródromo | - | data/raw/anac/aeroportos/aerodromos.parquet | não | `SBKP` |
| `nome` | string | não | Nome oficial do aeródromo | - | data/raw/anac/aeroportos/aerodromos.parquet | não | `Viracopos` |
| `municipio` | string | não | Município de localização do aeródromo | - | data/raw/anac/aeroportos/aerodromos.parquet | não | `Campinas` |
| `uf` | string | não | Unidade Federativa (sigla de 2 letras) | - | data/raw/anac/aeroportos/aerodromos.parquet | não | `SP` |
| `regiao` | string | não | Macrorregião geográfica brasileira derivada da UF (Norte, Nordeste, Centro-Oeste, Sudeste, Sul) | - | derivação geográfica explícita em ingestion/curate.py | não | `Sudeste` |
| `latitude` | float | sim | Latitude geográfica em graus decimais | graus | data/raw/anac/aeroportos/aerodromos.parquet | não | `-23.0074` |
| `longitude` | float | sim | Longitude geográfica em graus decimais | graus | data/raw/anac/aeroportos/aerodromos.parquet | não | `-47.1345` |
| `altitude` | float | sim | Altitude do aeródromo em metros | metros | data/raw/anac/aeroportos/aerodromos.parquet | não | `661.0` |
| `is_active_commercial` | bool | não | Indica se o aeródromo registrou voos comerciais regulares no período do projeto | - | cruzamento com voos_basica em ingestion/curate.py | não | `True` |

## Checagens de contrato

- **unicidade:** `codigo_oaci`
- **não nulo:** `codigo_oaci`
- **não nulo:** `regiao`
