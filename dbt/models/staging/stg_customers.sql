{{ config(materialized='view') }}

{#-
    Staging de clientes sintéticos.
    NOTA DE CONFORMIDADE LGPD E GOVERNANÇA:
    Atributos demográficos/sensíveis (faixa_etaria, genero, regiao) são estritamente
    EXCLUÍDOS da camada de features analíticas para prevenir viés algorítmico e
    atender às regras inegociáveis de auditoria e governança.
-#}

SELECT
    customer_id,
    CAST(join_date AS TIMESTAMP) AS join_date,
    home_airport,
    current_tier,
    status
FROM read_parquet('data/curated/synthetic/*customer*.parquet')
