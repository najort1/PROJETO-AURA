SELECT
    interaction_id,
    customer_id,
    CAST(interaction_date AS TIMESTAMP) AS interaction_date,
    channel,
    aspect,
    CAST(has_friction AS INTEGER) AS has_friction,
    CAST(friction_intensity AS DOUBLE) AS friction_intensity,
    CAST(nps_rating AS DOUBLE) AS nps_rating
FROM read_parquet('data/curated/synthetic/*interaction*.parquet')
