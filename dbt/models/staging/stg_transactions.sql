{{ config(materialized='view') }}

SELECT
    transaction_id,
    customer_id,
    CAST(transaction_date AS TIMESTAMP) AS transaction_date,
    transaction_type,
    CAST(amount_brl AS DOUBLE) AS amount_brl,
    COALESCE(ancillary_type, 'nenhum') AS ancillary_type,
    CAST(pontos_azul_acumulados AS INTEGER) AS pontos_azul_acumulados,
    CAST(pontos_qualificaveis_acumulados AS INTEGER) AS pontos_qualificaveis_acumulados,
    CAST(pontos_azul_resgatados AS INTEGER) AS pontos_azul_resgatados,
    flight_id
FROM read_parquet('data/curated/synthetic/*transaction*.parquet')
