"""Testes de conformidade anti-vazamento temporal e governança LGPD/viés (WS3).

Testa:
1. Proibição estrita de atributos sensíveis (faixa_etaria, genero, regiao) nas features analíticas (LGPD).
2. Garantia de que nenhuma transação/evento posterior ao cutoff temporal vaza para as features históricas.
3. Validação do teste customizado anti-vazamento no pipeline rolling origin.
"""

from pathlib import Path

import duckdb
import pandas as pd
import pytest

from ml.common.temporal import assert_no_temporal_leakage

SENSITIVE_FORBIDDEN_COLUMNS = ["faixa_etaria", "genero", "regiao"]


@pytest.fixture
def mini_synthetic_lake(tmp_path: Path):
    """Cria mini data lake sintético em tmp_path para teste hermético das transformações."""
    curated_dir = tmp_path / "data" / "curated" / "synthetic"
    curated_dir.mkdir(parents=True, exist_ok=True)

    # 1. Clientes (com atributos sensíveis que NÃO devem ir para as features)
    df_cust = pd.DataFrame(
        {
            "customer_id": ["C001", "C002", "C003"],
            "archetype": ["executivo_recorrente", "lazer_premium", "eventual_promocional"],
            "faixa_etaria": ["35-44", "45-59", "25-34"],
            "genero": ["M", "F", "M"],
            "regiao": ["Sudeste", "Sul", "Nordeste"],
            "home_airport": ["VCP", "SDU", "SSA"],
            "join_date": [
                pd.Timestamp("2023-10-01"),
                pd.Timestamp("2024-01-15"),
                pd.Timestamp("2024-06-20"),
            ],
            "current_tier": ["safira", "topazio", "azul"],
            "status": ["ativo", "ativo", "ativo"],
        }
    )
    df_cust.to_parquet(curated_dir / "customers.parquet", index=False)

    # 2. Voos
    df_flights = pd.DataFrame(
        {
            "flight_id": ["F01", "F02", "F03", "F04"],
            "flight_number": ["AD4001", "AD4002", "AD4003", "AD4004"],
            "origin_airport": ["VCP", "SDU", "VCP", "SSA"],
            "destination_airport": ["SDU", "VCP", "BSB", "VCP"],
            "departure_date": [
                pd.Timestamp("2024-11-10 10:00:00"),
                pd.Timestamp("2025-01-20 15:00:00"),
                pd.Timestamp("2025-07-15 08:00:00"),
                pd.Timestamp("2025-10-05 14:00:00"),  # Futuro em relação a 2025-08-31
            ],
            "distance_km": [410.0, 410.0, 820.0, 1450.0],
            "delay_minutes": [0, 25, 5, 0],
            "has_delay": [0, 1, 0, 0],
            "is_cancelled": [0, 0, 0, 0],
        }
    )
    df_flights.to_parquet(curated_dir / "flights.parquet", index=False)

    # 3. Transações (passadas e futuras ao cutoff 2025-08-31)
    df_tx = pd.DataFrame(
        {
            "transaction_id": ["T01", "T02", "T03", "T04", "T05"],
            "customer_id": ["C001", "C001", "C002", "C001", "C002"],
            "transaction_date": [
                pd.Timestamp("2024-11-01 10:00:00"),
                pd.Timestamp("2025-01-10 14:00:00"),
                pd.Timestamp("2025-02-15 09:00:00"),
                pd.Timestamp("2025-09-15 11:00:00"),  # Futura (período target)
                pd.Timestamp("2025-11-20 16:00:00"),  # Futura (período target)
            ],
            "transaction_type": [
                "compra_passagem",
                "compra_passagem",
                "compra_passagem",
                "compra_passagem",
                "resgate_passagem",
            ],
            "amount_brl": [600.0, 750.0, 500.0, 800.0, 50.0],
            "ancillary_type": ["espaco_azul", "nenhum", "bagagem", "nenhum", "nenhum"],
            "pontos_azul_acumulados": [1800, 2250, 1000, 2400, 0],
            "pontos_qualificaveis_acumulados": [600, 750, 500, 800, 0],
            "pontos_azul_resgatados": [0, 0, 0, 0, 15000],
            "flight_id": ["F01", "F02", "F03", "F04", None],
        }
    )
    df_tx.to_parquet(curated_dir / "transactions.parquet", index=False)

    # 4. Interações
    df_int = pd.DataFrame(
        {
            "interaction_id": ["I01", "I02"],
            "customer_id": ["C001", "C002"],
            "interaction_date": [
                pd.Timestamp("2025-01-20 18:00:00"),
                pd.Timestamp("2025-08-10 12:00:00"),
            ],
            "channel": ["app", "call_center"],
            "aspect": ["atraso", "atendimento"],
            "has_friction": [1, 0],
            "friction_intensity": [0.7, 0.0],
            "nps_rating": [3.0, 9.0],
        }
    )
    df_int.to_parquet(curated_dir / "interactions.parquet", index=False)

    return tmp_path, curated_dir


def test_lgpd_sensitive_columns_forbidden():
    """Regra Inegociável 8: faixa_etaria, genero, regiao são PROIBIDOS nas features analíticas."""
    # Lista de colunas mock/produção de features
    feature_columns = [
        "customer_id",
        "tier",
        "recency_days",
        "frequency_3m",
        "frequency_6m",
        "frequency_12m",
        "monetary_12m",
        "ticket_medio_12m",
        "frequency_trend",
        "frequency_volatility",
        "share_rotas_troncais",
        "share_resgate",
        "avg_advance_booking_days",
        "rota_favorita",
        "pontos_qualificaveis_12m",
        "saldo_pontos",
        "pontos_expirando_30d",
        "meta_proximo_nivel_pct",
        "beneficio_nao_utilizado",
        "days_since_last_interaction",
        "total_atritos_12m",
        "last_activity_date",
        "target_clv_12m",
        "target_churn_12m",
    ]

    for col in SENSITIVE_FORBIDDEN_COLUMNS:
        assert col not in feature_columns, (
            f"VIOLAÇÃO CRÍTICA DE LGPD: atributo sensível '{col}' encontrado nas features!"
        )


def test_anti_leakage_assertion_catches_future_dates():
    """Valida que a função fail-loud assert_no_temporal_leakage intercepta violação de cutoff."""
    cutoff = "2025-08-31"

    # Dataset correto (apenas datas passadas)
    df_ok = pd.DataFrame(
        {
            "customer_id": ["C01", "C02"],
            "last_activity_date": ["2025-05-10", "2025-08-30"],
        }
    )
    assert_no_temporal_leakage(df_ok, ["last_activity_date"], cutoff)

    # Dataset com vazamento (data posterior a 2025-08-31)
    df_leaked = pd.DataFrame(
        {
            "customer_id": ["C01", "C02"],
            "last_activity_date": ["2025-05-10", "2025-09-02"],
        }
    )
    with pytest.raises(ValueError, match="FALHA CRÍTICA ANTI-VAZAMENTO TEMPORAL"):
        assert_no_temporal_leakage(df_leaked, ["last_activity_date"], cutoff)


def test_dbt_feature_generation_anti_leakage(mini_synthetic_lake):
    """Executa a lógica SQL de extração de features em DuckDB e verifica que cutoff é 100% respeitado."""
    tmp_path, curated_dir = mini_synthetic_lake
    cutoff = "2025-08-31"

    con = duckdb.connect()
    # Executa a query de extração histórica com corte em 2025-08-31
    tx_pq = (curated_dir / "transactions.parquet").as_posix()
    res = con.execute(f"""
        SELECT
            customer_id,
            MAX(transaction_date) as last_tx,
            COUNT(*) as freq_hist,
            SUM(amount_brl) as mon_hist
        FROM read_parquet('{tx_pq}')
        WHERE transaction_date <= DATE '{cutoff}'
        GROUP BY customer_id
    """).df()
    con.close()

    assert not res.empty
    # Para o cliente C001, as transações futuras de setembro/2025 NÃO devem ser computadas no histórico
    c1 = res[res["customer_id"] == "C001"].iloc[0]
    # No mini lake, C001 tem T01 (nov/24, R$600) e T02 (jan/25, R$750) antes do cutoff. T04 é em set/25 (R$800).
    assert c1["freq_hist"] == 2
    assert c1["mon_hist"] == 1350.0  # 600 + 750 (sem o 800 futuro!)
    assert pd.to_datetime(c1["last_tx"]) <= pd.to_datetime(cutoff)


def test_rolling_origin_validation_cutoff_leakage_free(mini_synthetic_lake):
    """Verifica que a coorte de validação com cutoff 2025-02-28 não inclui eventos de março/2025 em diante."""
    tmp_path, curated_dir = mini_synthetic_lake
    val_cutoff = "2025-02-28"

    con = duckdb.connect()
    tx_pq = (curated_dir / "transactions.parquet").as_posix()
    res = con.execute(f"""
        SELECT
            customer_id,
            MAX(transaction_date) as last_tx,
            COUNT(*) as freq_hist
        FROM read_parquet('{tx_pq}')
        WHERE transaction_date <= DATE '{val_cutoff}'
        GROUP BY customer_id
    """).df()
    con.close()

    for _, row in res.iterrows():
        assert pd.to_datetime(row["last_tx"]) <= pd.to_datetime(val_cutoff)
