{{ config(
    materialized='table',
    post_hook="COPY (SELECT * FROM {{ this }}) TO 'data/analytics/features_customer_val.parquet' (FORMAT PARQUET)"
) }}

{{ generate_customer_features(var('val_cutoff'), var('val_target_start'), var('val_target_end')) }}
