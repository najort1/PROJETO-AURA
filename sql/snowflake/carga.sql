-- =============================================================================
-- PROJETO AURA 2.0 — CARGA SNOWFLAKE (CAMADA CURATED ANAC)
-- =============================================================================
-- Scripts de carga das tabelas tratadas em Parquet para o Snowflake.
-- Suporta named stage interno (via SnowSQL PUT) ou external stage (S3/Azure/GCS).
-- =============================================================================

USE DATABASE AURA_DB;
USE SCHEMA AURA_CURATED;
USE WAREHOUSE AURA_WH;

-- -----------------------------------------------------------------------------
-- OPÇÃO A: Upload via SnowSQL para Stage Interno (exemplo de linha de comando)
-- -----------------------------------------------------------------------------
-- snowsql -q "PUT file://data/curated/anac/anac_routes_monthly.parquet @AURA_STAGE_CURATED_ANAC/routes/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;"
-- snowsql -q "PUT file://data/curated/anac/anac_airports.parquet @AURA_STAGE_CURATED_ANAC/airports/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;"
-- snowsql -q "PUT file://data/curated/anac/anac_delays_monthly.parquet @AURA_STAGE_CURATED_ANAC/delays/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;"

-- -----------------------------------------------------------------------------
-- 1. Carga de ANAC_ROUTES_MONTHLY
-- -----------------------------------------------------------------------------
COPY INTO AURA_CURATED.ANAC_ROUTES_MONTHLY
FROM @AURA_STAGE_CURATED_ANAC/routes/
FILE_FORMAT = (FORMAT_NAME = 'AURA_PARQUET_FORMAT')
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
ON_ERROR = 'ABORT_STATEMENT'
PURGE = FALSE;

-- -----------------------------------------------------------------------------
-- 2. Carga de ANAC_AIRPORTS
-- -----------------------------------------------------------------------------
COPY INTO AURA_CURATED.ANAC_AIRPORTS
FROM @AURA_STAGE_CURATED_ANAC/airports/
FILE_FORMAT = (FORMAT_NAME = 'AURA_PARQUET_FORMAT')
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
ON_ERROR = 'ABORT_STATEMENT'
PURGE = FALSE;

-- -----------------------------------------------------------------------------
-- 3. Carga de ANAC_DELAYS_MONTHLY
-- -----------------------------------------------------------------------------
COPY INTO AURA_CURATED.ANAC_DELAYS_MONTHLY
FROM @AURA_STAGE_CURATED_ANAC/delays/
FILE_FORMAT = (FORMAT_NAME = 'AURA_PARQUET_FORMAT')
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
ON_ERROR = 'ABORT_STATEMENT'
PURGE = FALSE;

-- =============================================================================
-- OPÇÃO B: Tabelas Externas (Direct Query sobre Parquet em Data Lake / Cloud Storage)
-- =============================================================================
/*
CREATE OR REPLACE EXTERNAL TABLE AURA_CURATED.EXT_ANAC_ROUTES_MONTHLY
WITH LOCATION = @AURA_STAGE_CURATED_ANAC/routes/
AUTO_REFRESH = TRUE
FILE_FORMAT = (FORMAT_NAME = 'AURA_PARQUET_FORMAT');
*/

-- =============================================================================
-- QUERIES DE VALIDAÇÃO PÓS-CARGA (CONTROLE DE QUALIDADE)
-- =============================================================================

-- Validação 1: Contagens de linhas e integridade
SELECT 'ANAC_ROUTES_MONTHLY' AS TABELA, COUNT(*) AS TOTAL_LINHAS, COUNT(DISTINCT ROTA) AS TOTAL_ROTAS FROM AURA_CURATED.ANAC_ROUTES_MONTHLY
UNION ALL
SELECT 'ANAC_AIRPORTS', COUNT(*), COUNT(DISTINCT CODIGO_OACI) FROM AURA_CURATED.ANAC_AIRPORTS
UNION ALL
SELECT 'ANAC_DELAYS_MONTHLY', COUNT(*), COUNT(DISTINCT ID_ANO_MES) FROM AURA_CURATED.ANAC_DELAYS_MONTHLY;

-- Validação 2: Plausibilidade do volume de passageiros da Azul e mercado
SELECT
    ANO_MES,
    ROUND(SUM(TOTAL_PAX_PAGOS), 0) AS MERCADO_PAX,
    ROUND(SUM(AZUL_PAX_PAGOS), 0) AS AZUL_PAX,
    ROUND(SUM(AZUL_PAX_PAGOS) * 100.0 / NULLIF(SUM(TOTAL_PAX_PAGOS), 0), 2) AS MARKET_SHARE_AZUL_PCT
FROM AURA_CURATED.ANAC_ROUTES_MONTHLY
GROUP BY ANO_MES
ORDER BY ANO_MES DESC
LIMIT 12;

-- Validação 3: Ausência de nulos em chaves primárias
SELECT
    COUNT(*) AS VIOLACOES_NULOS
FROM AURA_CURATED.ANAC_ROUTES_MONTHLY
WHERE ID_ROTA_MES IS NULL OR ORIGEM_OACI IS NULL OR DESTINO_OACI IS NULL;
