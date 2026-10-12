{{ config(materialized='view') }}

SELECT
    flight_id,
    flight_number,
    origin_airport,
    destination_airport,
    CAST(departure_date AS TIMESTAMP) AS departure_date,
    CAST(distance_km AS DOUBLE) AS distance_km,
    CAST(delay_minutes AS INTEGER) AS delay_minutes,
    CAST(has_delay AS INTEGER) AS has_delay,
    CAST(is_cancelled AS INTEGER) AS is_cancelled,
    CASE
        WHEN (origin_airport IN ('VCP', 'SDU', 'CGH', 'CNF', 'BSB')
              AND destination_airport IN ('VCP', 'SDU', 'CGH', 'CNF', 'BSB'))
        THEN 1 ELSE 0
    END AS is_troncal
FROM read_parquet('data/curated/synthetic/*flight*.parquet')
