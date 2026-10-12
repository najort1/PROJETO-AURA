{% macro generate_customer_features(cutoff_date, target_start_date, target_end_date) %}

WITH base_customers AS (
    SELECT
        customer_id,
        join_date,
        home_airport,
        current_tier,
        status
    FROM {{ ref('stg_customers') }}
    WHERE join_date <= DATE '{{ cutoff_date }}'
),

historical_transactions AS (
    SELECT
        t.transaction_id,
        t.customer_id,
        t.transaction_date,
        t.transaction_type,
        t.amount_brl,
        t.ancillary_type,
        t.pontos_azul_acumulados,
        t.pontos_qualificaveis_acumulados,
        t.pontos_azul_resgatados,
        t.flight_id,
        f.origin_airport,
        f.destination_airport,
        f.is_troncal,
        CASE
            WHEN f.departure_date IS NOT NULL AND f.departure_date >= t.transaction_date
            THEN DATEDIFF('day', t.transaction_date, f.departure_date)
            ELSE 14
        END AS advance_days
    FROM {{ ref('stg_transactions') }} t
    LEFT JOIN {{ ref('stg_flights') }} f
        ON t.flight_id = f.flight_id
    WHERE t.transaction_date <= DATE '{{ cutoff_date }}'
),

agg_tx AS (
    SELECT
        customer_id,
        MAX(transaction_date) AS last_activity_date,
        COALESCE(DATEDIFF('day', MAX(transaction_date), DATE '{{ cutoff_date }}'), 999) AS recency_days,

        COUNT(CASE WHEN transaction_date >= (DATE '{{ cutoff_date }}' - INTERVAL '365' DAY)
                    AND transaction_type IN ('compra_passagem', 'servico_ancillary')
                   THEN 1 END) AS frequency_12m,

        COUNT(CASE WHEN transaction_date >= (DATE '{{ cutoff_date }}' - INTERVAL '180' DAY)
                    AND transaction_type IN ('compra_passagem', 'servico_ancillary')
                   THEN 1 END) AS frequency_6m,

        COUNT(CASE WHEN transaction_date >= (DATE '{{ cutoff_date }}' - INTERVAL '90' DAY)
                    AND transaction_type IN ('compra_passagem', 'servico_ancillary')
                   THEN 1 END) AS frequency_3m,

        COALESCE(SUM(CASE WHEN transaction_date >= (DATE '{{ cutoff_date }}' - INTERVAL '365' DAY)
                          THEN amount_brl::DECIMAL(18,2) ELSE 0 END), 0.0) AS monetary_12m,

        COALESCE(SUM(CASE WHEN transaction_date >= (DATE '{{ cutoff_date }}' - INTERVAL '365' DAY)
                          THEN pontos_qualificaveis_acumulados ELSE 0 END), 0) AS pontos_qualificaveis_12m,

        GREATEST(0, COALESCE(SUM(pontos_azul_acumulados - pontos_azul_resgatados), 0)) AS saldo_pontos,

        COUNT(CASE WHEN transaction_date >= (DATE '{{ cutoff_date }}' - INTERVAL '365' DAY)
                    AND transaction_type = 'resgate_passagem'
                   THEN 1 END) AS resgates_12m,

        COUNT(CASE WHEN transaction_date >= (DATE '{{ cutoff_date }}' - INTERVAL '365' DAY)
                    AND is_troncal = 1
                   THEN 1 END) AS troncal_flights_12m,

        AVG(CASE WHEN transaction_date >= (DATE '{{ cutoff_date }}' - INTERVAL '365' DAY)
                  AND flight_id IS NOT NULL
                 THEN advance_days END) AS avg_advance_booking_days,

        -- Contagem de ancillaries específicos utilizados
        COUNT(CASE WHEN transaction_date >= (DATE '{{ cutoff_date }}' - INTERVAL '365' DAY)
                    AND ancillary_type = 'espaco_azul' THEN 1 END) AS count_espaco_azul,
        COUNT(CASE WHEN transaction_date >= (DATE '{{ cutoff_date }}' - INTERVAL '365' DAY)
                    AND ancillary_type = 'bagagem' THEN 1 END) AS count_bagagem

    FROM historical_transactions
    GROUP BY customer_id
),

route_ranking AS (
    SELECT
        customer_id,
        origin_airport || '-' || destination_airport AS rota,
        COUNT(*) AS rota_count,
        ROW_NUMBER() OVER(PARTITION BY customer_id ORDER BY COUNT(*) DESC, rota ASC) AS rn
    FROM historical_transactions
    WHERE origin_airport IS NOT NULL AND destination_airport IS NOT NULL
      AND transaction_date >= (DATE '{{ cutoff_date }}' - INTERVAL '365' DAY)
    GROUP BY customer_id, origin_airport, destination_airport
),

top_route AS (
    SELECT customer_id, rota AS rota_favorita
    FROM route_ranking
    WHERE rn = 1
),

historical_interactions AS (
    SELECT
        customer_id,
        MAX(interaction_date) AS last_interaction_date,
        COALESCE(DATEDIFF('day', MAX(interaction_date), DATE '{{ cutoff_date }}'), 999) AS days_since_last_interaction,

        COUNT(CASE WHEN interaction_date >= (DATE '{{ cutoff_date }}' - INTERVAL '365' DAY)
                    AND aspect = 'atraso' AND has_friction = 1 THEN 1 END) AS atritos_atraso_12m,

        COUNT(CASE WHEN interaction_date >= (DATE '{{ cutoff_date }}' - INTERVAL '365' DAY)
                    AND aspect = 'bagagem' AND has_friction = 1 THEN 1 END) AS atritos_bagagem_12m,

        COUNT(CASE WHEN interaction_date >= (DATE '{{ cutoff_date }}' - INTERVAL '365' DAY)
                    AND aspect = 'app_checkin' AND has_friction = 1 THEN 1 END) AS atritos_app_checkin_12m,

        COUNT(CASE WHEN interaction_date >= (DATE '{{ cutoff_date }}' - INTERVAL '365' DAY)
                    AND aspect = 'resgate_milhas' AND has_friction = 1 THEN 1 END) AS atritos_resgate_milhas_12m,

        COUNT(CASE WHEN interaction_date >= (DATE '{{ cutoff_date }}' - INTERVAL '365' DAY)
                    AND aspect = 'atendimento' AND has_friction = 1 THEN 1 END) AS atritos_atendimento_12m,

        COUNT(CASE WHEN interaction_date >= (DATE '{{ cutoff_date }}' - INTERVAL '365' DAY)
                    AND aspect = 'preco' AND has_friction = 1 THEN 1 END) AS atritos_preco_12m,

        COUNT(CASE WHEN interaction_date >= (DATE '{{ cutoff_date }}' - INTERVAL '365' DAY)
                    AND has_friction = 1 THEN 1 END) AS total_atritos_12m

    FROM {{ ref('stg_interactions') }}
    WHERE interaction_date <= DATE '{{ cutoff_date }}'
    GROUP BY customer_id
),

future_performance AS (
    SELECT
        customer_id,
        COALESCE(SUM(amount_brl::DECIMAL(18,2)), 0.0)::DOUBLE AS target_clv_12m,
        COUNT(*) AS future_tx_count,
        MIN(transaction_date) AS first_future_tx_date
    FROM {{ ref('stg_transactions') }}
    WHERE transaction_date BETWEEN DATE '{{ target_start_date }}' AND DATE '{{ target_end_date }}'
    GROUP BY customer_id
)

SELECT
    c.customer_id,
    c.current_tier AS tier,

    -- RFM e Frequências
    COALESCE(tx.recency_days, 999) AS recency_days,
    COALESCE(tx.frequency_3m, 0) AS frequency_3m,
    COALESCE(tx.frequency_6m, 0) AS frequency_6m,
    COALESCE(tx.frequency_12m, 0) AS frequency_12m,
    COALESCE(tx.frequency_12m, 0) AS trechos_12m,
    -- ::DOUBLE na publicação: a SOMA é feita em DECIMAL (exata, determinística),
    -- mas a coluna sai como float64 para compatibilidade com o ecossistema pandas/sklearn.
    ROUND(COALESCE(tx.monetary_12m, 0.0), 2)::DOUBLE AS monetary_12m,
    ROUND(COALESCE(tx.monetary_12m, 0.0), 2)::DOUBLE AS gastos_12m_brl,

    CASE
        WHEN COALESCE(tx.frequency_12m, 0) > 0
        THEN ROUND(tx.monetary_12m / tx.frequency_12m, 2)::DOUBLE
        ELSE 0.0
    END AS ticket_medio_12m,

    ROUND(
        (COALESCE(tx.frequency_3m, 0) * 4.0) / (COALESCE(tx.frequency_12m, 0) + 1.0),
        4
    ) AS frequency_trend,

    -- Volatilidade estimada da frequência (frequência semestral vs trimestral)
    ROUND(
        ABS(COALESCE(tx.frequency_3m, 0) * 2.0 - (COALESCE(tx.frequency_6m, 0) - COALESCE(tx.frequency_3m, 0)))
        / (COALESCE(tx.frequency_6m, 0) + 1.0),
        4
    ) AS frequency_volatility,

    -- Mix de rota e viagens
    CASE
        WHEN COALESCE(tx.frequency_12m, 0) > 0
        THEN ROUND(CAST(tx.troncal_flights_12m AS DOUBLE) / tx.frequency_12m, 4)
        ELSE 0.0
    END AS share_rotas_troncais,

    ROUND(
        CAST(COALESCE(tx.resgates_12m, 0) AS DOUBLE)
        / (COALESCE(tx.frequency_12m, 0) + COALESCE(tx.resgates_12m, 0) + 0.001),
        4
    ) AS share_resgate,

    ROUND(COALESCE(tx.avg_advance_booking_days, 14.0), 1) AS avg_advance_booking_days,
    COALESCE(tr.rota_favorita, c.home_airport || '-VCP') AS rota_favorita,

    -- Programa de Fidelidade
    CAST(COALESCE(tx.pontos_qualificaveis_12m, 0) AS BIGINT) AS pontos_qualificaveis_12m,
    CAST(COALESCE(tx.saldo_pontos, 0) AS BIGINT) AS saldo_pontos,
    CAST(ROUND(COALESCE(tx.saldo_pontos, 0) * 0.08) AS INTEGER) AS pontos_expirando_30d,

    -- Progresso para próximo nível (meta percentual)
    ROUND(
        CASE
            WHEN c.current_tier = 'azul'
            THEN LEAST(1.0, GREATEST(COALESCE(tx.pontos_qualificaveis_12m, 0) / 6000.0, COALESCE(tx.frequency_12m, 0) / 6.0))
            WHEN c.current_tier = 'topazio'
            THEN LEAST(1.0, GREATEST(COALESCE(tx.pontos_qualificaveis_12m, 0) / 12000.0, COALESCE(tx.frequency_12m, 0) / 12.0))
            WHEN c.current_tier = 'safira'
            THEN LEAST(1.0, GREATEST(COALESCE(tx.pontos_qualificaveis_12m, 0) / 25000.0, COALESCE(tx.frequency_12m, 0) / 24.0))
            WHEN c.current_tier = 'diamante'
            THEN LEAST(1.0, GREATEST(COALESCE(tx.pontos_qualificaveis_12m, 0) / 50000.0, COALESCE(tx.frequency_12m, 0) / 40.0))
            ELSE 1.0
        END,
        4
    ) AS meta_proximo_nivel_pct,

    CASE
        WHEN c.current_tier IN ('diamante', 'diamante_unique', 'safira') AND COALESCE(tx.count_espaco_azul, 0) = 0 THEN 'espaco_azul'
        WHEN c.current_tier IN ('diamante', 'diamante_unique') AND COALESCE(tx.count_bagagem, 0) = 0 THEN 'despacho_bagagem'
        ELSE 'nenhum'
    END AS beneficio_nao_utilizado,

    -- Interações e Atritos
    COALESCE(inter.days_since_last_interaction, 999) AS days_since_last_interaction,
    COALESCE(inter.atritos_atraso_12m, 0) AS atritos_atraso_12m,
    COALESCE(inter.atritos_bagagem_12m, 0) AS atritos_bagagem_12m,
    COALESCE(inter.atritos_app_checkin_12m, 0) AS atritos_app_checkin_12m,
    COALESCE(inter.atritos_resgate_milhas_12m, 0) AS atritos_resgate_milhas_12m,
    COALESCE(inter.atritos_atendimento_12m, 0) AS atritos_atendimento_12m,
    COALESCE(inter.atritos_preco_12m, 0) AS atritos_preco_12m,
    COALESCE(inter.total_atritos_12m, 0) AS total_atritos_12m,

    -- Data do último evento (para auditoria anti-vazamento)
    CAST(CAST(tx.last_activity_date AS DATE) AS TIMESTAMP) AS last_activity_date,

    -- Alvos de Treinamento e Avaliação (período futuro)
    ROUND(COALESCE(fut.target_clv_12m, 0.0), 2) AS target_clv_12m,

    -- Definição operacional de Churn: inatividade > 2x intervalo individual (mínimo 180 dias)
    CASE
        WHEN COALESCE(fut.future_tx_count, 0) = 0 THEN 1
        WHEN DATEDIFF('day', DATE '{{ target_start_date }}', fut.first_future_tx_date) > 180
             AND DATEDIFF('day', DATE '{{ target_start_date }}', fut.first_future_tx_date) > 2.0 * (365.0 / (COALESCE(tx.frequency_12m, 0) + 1.0))
        THEN 1
        ELSE 0
    END AS target_churn_12m

FROM base_customers c
LEFT JOIN agg_tx tx ON c.customer_id = tx.customer_id
LEFT JOIN top_route tr ON c.customer_id = tr.customer_id
LEFT JOIN historical_interactions inter ON c.customer_id = inter.customer_id
LEFT JOIN future_performance fut ON c.customer_id = fut.customer_id

{% endmacro %}
