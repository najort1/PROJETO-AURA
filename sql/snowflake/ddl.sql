-- =============================================================================
-- PROJETO AURA 2.0 — DDL SNOWFLAKE (CAMADA CURATED ANAC)
-- =============================================================================
-- Contrato idêntico: trocar parquet sintético/local por Snowflake é troca de
-- fonte, não reescrita de código ou pipeline (alinhado a schemas/*.yaml).
-- =============================================================================

-- 1. Criação de Warehouse, Database e Schemas
CREATE WAREHOUSE IF NOT EXISTS AURA_WH
    WITH WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Warehouse analítico do Projeto Aura 2.0';

CREATE DATABASE IF NOT EXISTS AURA_DB
    COMMENT = 'Data lakehouse analítico do Projeto Aura 2.0';

USE DATABASE AURA_DB;

CREATE SCHEMA IF NOT EXISTS AURA_RAW
    COMMENT = 'Camada bruta: arquivos imutáveis com manifesto de proveniência';

CREATE SCHEMA IF NOT EXISTS AURA_CURATED
    COMMENT = 'Camada tratada e tipada com contratos de dados schemas/*.yaml';

CREATE SCHEMA IF NOT EXISTS AURA_ANALYTICS
    COMMENT = 'Camada analítica com features, modelos, scores e recomendações';

USE SCHEMA AURA_CURATED;

-- 2. File Format para ingestão de arquivos Parquet
CREATE OR REPLACE FILE FORMAT AURA_PARQUET_FORMAT
    TYPE = PARQUET
    COMPRESSION = AUTO
    BINARY_AS_TEXT = FALSE
    COMMENT = 'Formato padrão Parquet para tabelas curadas do Projeto Aura';

-- 3. Stage Interno/Externo para arquivos curados da ANAC
CREATE OR REPLACE STAGE AURA_STAGE_CURATED_ANAC
    FILE_FORMAT = AURA_PARQUET_FORMAT
    COMMENT = 'Stage para recepção de arquivos Parquet curados ANAC';

-- =============================================================================
-- TABELAS CURADAS (CONTRATOS IDÊNTICOS A schemas/anac_*.yaml)
-- =============================================================================

-- Tabela 1: Mercado mensal de rotas domésticas regulares (schemas/anac_routes_monthly.yaml)
CREATE OR REPLACE TABLE AURA_CURATED.ANAC_ROUTES_MONTHLY (
    id_rota_mes                 VARCHAR(64)     NOT NULL,
    rota                        VARCHAR(32)     NOT NULL,
    origem_oaci                 VARCHAR(4)      NOT NULL,
    destino_oaci                VARCHAR(4)      NOT NULL,
    ano                         INTEGER         NOT NULL,
    mes                         INTEGER         NOT NULL,
    ano_mes                     VARCHAR(7)      NOT NULL,
    total_pax_pagos             NUMBER(38,0)    NOT NULL,
    total_assentos_ofertados    NUMBER(38,0)    NOT NULL,
    total_decolagens            NUMBER(38,0)    NOT NULL,
    azul_pax_pagos              NUMBER(38,0)    NOT NULL,
    azul_assentos_ofertados     NUMBER(38,0)    NOT NULL,
    azul_decolagens             NUMBER(38,0)    NOT NULL,
    azul_share_pax              FLOAT           NOT NULL,
    azul_share_decolagens       FLOAT           NOT NULL,
    azul_load_factor            FLOAT           NOT NULL,
    total_load_factor           FLOAT           NOT NULL,
    has_azul                    BOOLEAN         NOT NULL,
    CONSTRAINT pk_anac_routes_monthly PRIMARY KEY (id_rota_mes)
)
CLUSTER BY (ano_mes)
COMMENT = 'Agregado mensal de rotas do mercado doméstico regular brasileiro (ANAC voos_basica) com métricas de mercado e Azul';

-- Tabela 2: Cadastro de aeródromos e macrorregiões (schemas/anac_airports.yaml)
CREATE OR REPLACE TABLE AURA_CURATED.ANAC_AIRPORTS (
    codigo_oaci                 VARCHAR(4)      NOT NULL,
    nome                        VARCHAR(255)    NOT NULL,
    municipio                   VARCHAR(128)    NOT NULL,
    uf                          VARCHAR(2)      NOT NULL,
    regiao                      VARCHAR(32)     NOT NULL,
    latitude                    FLOAT,
    longitude                   FLOAT,
    altitude                    FLOAT,
    is_active_commercial        BOOLEAN         NOT NULL,
    CONSTRAINT pk_anac_airports PRIMARY KEY (codigo_oaci)
)
COMMENT = 'Cadastro de aeródromos brasileiros com coordenadas geográficas e macrorregião derivada da UF';

-- Tabela 3: Série histórica mensal de atrasos operacionais (schemas/anac_delays_monthly.yaml)
CREATE OR REPLACE TABLE AURA_CURATED.ANAC_DELAYS_MONTHLY (
    id_ano_mes                  VARCHAR(7)      NOT NULL,
    ano                         INTEGER         NOT NULL,
    mes                         INTEGER         NOT NULL,
    ano_mes                     VARCHAR(7)      NOT NULL,
    total_movimentos            INTEGER         NOT NULL,
    movimentos_atrasados        INTEGER         NOT NULL,
    taxa_atraso                 FLOAT           NOT NULL,
    cobertura                   VARCHAR(64)     NOT NULL,
    CONSTRAINT pk_anac_delays_monthly PRIMARY KEY (id_ano_mes)
)
CLUSTER BY (ano_mes)
COMMENT = 'Série histórica mensal da taxa de atraso (>15 minutos) do sistema aeroportuário nacional (ANAC movimentação)';
