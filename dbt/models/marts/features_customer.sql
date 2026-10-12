{{ config(
    materialized='table',
    post_hook="COPY (SELECT * FROM {{ this }} ORDER BY customer_id) TO 'data/analytics/features_customer.parquet' (FORMAT PARQUET)"
) }}

{{ generate_customer_features(var('cutoff'), var('target_start'), var('target_end')) }}
