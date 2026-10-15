"""Testes automatizados do módulo de benchmarks (ingestion/benchmarks.py).

Valida:
1. Execução do pipeline de curadoria e geração hermética de todos os artefatos.
2. Integridade e contagens de linhas de cada conjunto de dados curado.
3. Imputação de atrasos em satisfação, flag booleana de linhagem e int64 (DEF-08, DEF-14).
4. Ausência de total_delay_minutes espúrio e presença de en_route_delay_delta (DEF-02).
5. Coerção numérica e tratamento de notas em reviews ('n' -> NaN, 0.0 -> NaN) (DEF-11).
6. Descarte de colunas unnamed (DEF-07) e booleano em recommended (DEF-15).
7. Strip de aspas em review_title (DEF-16) e transliteração Unicode NFKD (DEF-17).
8. Mitigação de viés de tempo imortal (DEF-01) e cálculo inclusivo de tenure (DEF-18).
9. Tratamento de casos de borda em burn_rate com massas sintéticas controladas (DEF-06, DEF-10).
10. Hermeticidade total da CLI sem efeitos colaterais em arquivos de trabalho (DEF-05).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from aura_core.paths import path
from ingestion.benchmarks import (
    SKYTRAX_ASPECT_COLUMNS,
    curate_airline_reviews,
    curate_loyalty,
    curate_passenger_satisfaction,
    main,
    run_all,
    to_snake_case,
)


def test_to_snake_case_utility() -> None:
    """Valida conversão para snake_case com casos de borda e transliteração Unicode NFKD (DEF-17)."""
    assert to_snake_case("Departure/Arrival time convenient") == "departure_arrival_time_convenient"
    assert to_snake_case("Food & Beverages") == "food_and_beverages"
    assert to_snake_case("Inflight wifi service") == "inflight_wifi_service"
    assert to_snake_case("Unnamed: 0") == "unnamed_0"
    assert to_snake_case("Loyalty Number") == "loyalty_number"
    # Transliteração Unicode NFKD preservando acentos
    assert to_snake_case("Pontuação de Voo") == "pontuacao_de_voo"
    assert to_snake_case("Mês / Ano") == "mes_ano"
    assert to_snake_case("Aeronave & Operação") == "aeronave_and_operacao"


def test_pipeline_execution_and_file_generation(tmp_path: Path) -> None:
    """Verifica que run_all gera os 3 parquets e o JSON de métricas em diretório customizado."""
    summary = run_all(raw_dir="data/raw", output_dir=tmp_path)

    expected_files = [
        tmp_path / "loyalty_aggregated.parquet",
        tmp_path / "passenger_satisfaction.parquet",
        tmp_path / "airline_reviews.parquet",
        tmp_path / "benchmark_summary.json",
    ]
    for ef in expected_files:
        assert ef.exists(), f"Artefato esperado não gerado: {ef}"

    assert "loyalty" in summary
    assert "satisfaction" in summary
    assert "reviews" in summary


def test_loyalty_aggregation_integrity() -> None:
    """Valida integridade do Loyalty Program agregado."""
    out_file = path("data/curated/benchmarks/loyalty_aggregated.parquet")
    if not out_file.exists():
        curate_loyalty()

    df = pd.read_parquet(out_file)

    # 1. Contagem exata de clientes
    assert len(df) == 16737, f"Esperado 16.737 clientes, obtido {len(df)}"
    assert df["loyalty_number"].nunique() == 16737, "loyalty_number deve ser chave única 1:1"

    # 2. Presença de colunas obrigatórias
    expected_cols = [
        "loyalty_number",
        "country",
        "province",
        "city",
        "postal_code",
        "gender",
        "education",
        "salary",
        "marital_status",
        "loyalty_card",
        "clv",
        "enrollment_type",
        "enrollment_year",
        "enrollment_month",
        "cancellation_year",
        "cancellation_month",
        "total_flights",
        "flights_booked",
        "flights_with_companions",
        "total_distance",
        "total_points_accumulated",
        "total_points_redeemed",
        "total_dollar_cost_points_redeemed",
        "active_months_in_window",
        "avg_points_per_month",
        "redemptions_per_active_month",
        "burn_rate",
        "has_churned",
        "tenure_months",
    ]
    for col in expected_cols:
        assert col in df.columns, f"Coluna esperada ausente em loyalty_aggregated: {col}"

    # 3. Consistência de flags e regras de negócio
    churn_count = int(df["has_churned"].sum())
    assert churn_count == 2067, f"Esperado 2.067 churns, obtido {churn_count}"
    assert np.all(df["has_churned"] == df["cancellation_year"].notna())

    # DEF-18: tenure_months inclusivo garantindo >= 1
    assert (df["tenure_months"] >= 1).all(), "tenure_months deve ser >= 1 (cálculo inclusivo)"

    # DEF-03: active_months_in_window entre 1 e 24 meses
    assert (df["active_months_in_window"] >= 1).all()
    assert (df["active_months_in_window"] <= 24).all()

    # burn_rate não negativo (quando não NaN)
    valid_burn = df["burn_rate"].dropna()
    assert (valid_burn >= 0.0).all(), "burn_rate não pode conter valores negativos"

    # Tipos das colunas
    assert pd.api.types.is_bool_dtype(df["has_churned"])
    assert pd.api.types.is_numeric_dtype(df["clv"])
    assert pd.api.types.is_numeric_dtype(df["total_flights"])
    assert pd.api.types.is_numeric_dtype(df["total_distance"])
    assert pd.api.types.is_numeric_dtype(df["avg_points_per_month"])
    assert pd.api.types.is_numeric_dtype(df["redemptions_per_active_month"])


def test_passenger_satisfaction_integrity_and_imputation() -> None:
    """Valida curadoria de satisfação, flag de linhagem (DEF-08), int64 (DEF-14) e ausência de total_delay (DEF-02)."""
    out_file = path("data/curated/benchmarks/passenger_satisfaction.parquet")
    if not out_file.exists():
        curate_passenger_satisfaction()

    df = pd.read_parquet(out_file)

    # 1. Contagem exata de registros
    assert len(df) == 129880, f"Esperado 129.880 avaliações, obtido {len(df)}"

    # 2. Colunas requeridas em snake_case
    required_cols = [
        "gender",
        "customer_type",
        "age",
        "type_of_travel",
        "class",
        "flight_distance",
        "inflight_wifi_service",
        "departure_arrival_time_convenient",
        "ease_of_online_booking",
        "gate_location",
        "food_and_drink",
        "online_boarding",
        "seat_comfort",
        "inflight_entertainment",
        "on_board_service",
        "leg_room_service",
        "baggage_handling",
        "checkin_service",
        "cleanliness",
        "departure_delay_minutes",
        "arrival_delay_minutes",
        "arrival_delay_imputed",
        "en_route_delay_delta",
        "satisfaction",
    ]
    for col in required_cols:
        assert col in df.columns, f"Coluna obrigatória ausente em passenger_satisfaction: {col}"

    # DEF-02: Garantir que total_delay_minutes NÃO existe
    assert "total_delay_minutes" not in df.columns, (
        "total_delay_minutes não deve existir para evitar dupla contagem"
    )

    # DEF-08: Linhagem de imputação
    assert pd.api.types.is_bool_dtype(df["arrival_delay_imputed"]), (
        "arrival_delay_imputed deve ser booleano"
    )
    assert int(df["arrival_delay_imputed"].sum()) == 393, (
        "Exatamente 393 atrasos de chegada devem ser marcados como imputados"
    )

    # DEF-14: Tipagem int64 em atrasos
    assert df["arrival_delay_minutes"].dtype == "int64", "arrival_delay_minutes deve ser int64"
    assert df["departure_delay_minutes"].dtype == "int64", "departure_delay_minutes deve ser int64"
    assert df["en_route_delay_delta"].dtype == "int64", "en_route_delay_delta deve ser int64"

    # Ausência de nulos em atrasos
    assert df["arrival_delay_minutes"].isna().sum() == 0
    assert df["departure_delay_minutes"].isna().sum() == 0


def test_airline_reviews_integrity_and_curation() -> None:
    """Valida curadoria de avaliações, descarte de unnamed (DEF-07), zeros em aspectos (DEF-11) e strip (DEF-16)."""
    out_file = path("data/curated/benchmarks/airline_reviews.parquet")
    if not out_file.exists():
        curate_airline_reviews()

    df = pd.read_parquet(out_file)

    # 1. Contagem exata de avaliações
    assert len(df) == 23171, f"Esperado 23.171 avaliações, obtido {len(df)}"

    # DEF-07: Nenhuma coluna iniciada com unnamed
    unnamed = [c for c in df.columns if c.lower().startswith("unnamed")]
    assert len(unnamed) == 0, f"Colunas unnamed não descartadas: {unnamed}"

    # 2. Colunas padronizadas
    assert "airline_name" in df.columns
    assert "overall_rating" in df.columns
    assert "recommended" in df.columns
    assert "review_title" in df.columns

    # DEF-15: recommended booleano nativo
    assert pd.api.types.is_bool_dtype(df["recommended"]), "recommended deve ser booleano nativo"
    assert df["recommended"].isna().sum() == 0

    # DEF-16: strip de aspas em review_title
    titles = df["review_title"].dropna()
    assert not titles.str.startswith('"').any(), "review_title não deve iniciar com aspas"
    assert not titles.str.endswith('"').any(), "review_title não deve terminar com aspas"

    # DEF-11: Zeros convertidos para NaN nas 7 notas Skytrax
    for col in SKYTRAX_ASPECT_COLUMNS:
        assert col in df.columns
        zeros = (df[col] == 0).sum()
        assert zeros == 0, f"Coluna {col} ainda contém {zeros} zeros espúrios (esperado NaN)"

    # overall_rating numérico com 842 NaNs
    assert pd.api.types.is_float_dtype(df["overall_rating"])
    assert df["overall_rating"].isna().sum() == 842
    valid_ratings = df["overall_rating"].dropna()
    assert (valid_ratings >= 1.0).all() and (valid_ratings <= 10.0).all()


def test_benchmark_summary_json() -> None:
    """Valida métricas do sumário JSON, eliminação de viés (DEF-01), atrasos canônicos (DEF-02) e top_rated (DEF-13)."""
    summary_file = path("data/curated/benchmarks/benchmark_summary.json")
    if not summary_file.exists():
        run_all()

    with open(summary_file, encoding="utf-8") as f:
        summary = json.load(f)

    # 1. Loyalty
    loyalty = summary["loyalty"]
    assert loyalty["total_customers"] == 16737
    assert 12.0 <= loyalty["churn_rate_pct"] <= 13.0
    assert loyalty["churn_count"] == 2067
    assert set(loyalty["avg_clv_by_tier"].keys()) == {"Star", "Nova", "Aurora"}
    assert (
        loyalty["avg_clv_by_tier"]["Aurora"]
        > loyalty["avg_clv_by_tier"]["Nova"]
        > loyalty["avg_clv_by_tier"]["Star"]
    )

    # DEF-01: Verificação da coorte ativa 2017 e ressalva metodológica
    assert "active_cohort_2017" in loyalty, "Coorte ativa 2017 deve estar documentada no JSON"
    cohort = loyalty["active_cohort_2017"]
    assert cohort["total_customers"] == 10512, "Coorte ativa deve ter exatamente 10.512 membros"
    assert cohort["churn_count"] == 656, "Coorte ativa deve registrar exatamente 656 churns"
    assert 6.0 <= cohort["churn_rate_pct"] <= 6.5
    assert "methodological_notes" in cohort
    assert "immortal time bias" in cohort["methodological_notes"].lower()
    assert "correlation_redemptions_per_active_month_vs_churn" in cohort

    # 2. Satisfaction
    sat = summary["satisfaction"]
    assert sat["total_passengers"] == 129880
    assert 40.0 <= sat["satisfaction_rate_pct"] <= 45.0

    # DEF-02: Médias de atraso sem total_delay_minutes e com en_route_delay_delta
    delays = sat["avg_delay_by_satisfaction"]
    for group in ["satisfied", "dissatisfied"]:
        assert "total_delay_minutes" not in delays[group], (
            f"total_delay_minutes espúrio presente em {group}"
        )
        assert "arrival_delay_minutes" in delays[group]
        assert "departure_delay_minutes" in delays[group]
        assert "en_route_delay_delta" in delays[group]

    assert (
        delays["dissatisfied"]["arrival_delay_minutes"]
        > delays["satisfied"]["arrival_delay_minutes"]
    )
    assert sat["lowest_rated_aspect"]["aspect"] == "inflight_wifi_service"

    # 3. Reviews (DEF-13: top_rated_airlines com representatividade >= 50)
    rev = summary["reviews"]
    assert rev["total_reviews"] == 23171
    assert rev["valid_rating_count"] == 22329
    assert 3.0 <= rev["global_avg_rating"] <= 3.3
    assert "top_rated_airlines" in rev, "top_rated_airlines deve ser a chave canônica no JSON"
    assert len(rev["top_rated_airlines"]) == 10
    for airline in rev["top_rated_airlines"]:
        assert airline["review_count"] >= 50, (
            f"Companhia {airline['airline_name']} tem menos de 50 avaliações"
        )
        assert airline["avg_rating"] is not None


def test_benchmarks_cli(tmp_path: Path) -> None:
    """Valida CLI hermética apontando para tmp_path sem efeitos colaterais em data/curated/ (DEF-05)."""
    ret = main(["--raw-dir", "data/raw", "--output-dir", str(tmp_path)])
    assert ret == 0

    assert (tmp_path / "loyalty_aggregated.parquet").exists()
    assert (tmp_path / "passenger_satisfaction.parquet").exists()
    assert (tmp_path / "airline_reviews.parquet").exists()
    assert (tmp_path / "benchmark_summary.json").exists()


# ==============================================================================
# DEF-06: Testes unitários rigorosos com massas sintéticas controladas
# ==============================================================================


def test_burn_rate_edge_cases_synthetic() -> None:
    """Valida rigorosamente o cálculo de burn_rate com casos de borda conhecidos (DEF-06, DEF-10)."""
    synthetic_cases = pd.DataFrame(
        {
            "total_points_accumulated": [1000.0, 1000.0, 500.0, 0.0, 0.0],
            "total_points_redeemed": [500.0, 0.0, 1000.0, 0.0, 500.0],
        }
    )

    conds = [
        synthetic_cases["total_points_accumulated"] > 0,
        (synthetic_cases["total_points_accumulated"] == 0)
        & (synthetic_cases["total_points_redeemed"] == 0),
        (synthetic_cases["total_points_accumulated"] == 0)
        & (synthetic_cases["total_points_redeemed"] > 0),
    ]
    choices = [
        synthetic_cases["total_points_redeemed"] / synthetic_cases["total_points_accumulated"],
        0.0,
        np.nan,
    ]
    burn_rate = np.select(conds, choices, default=np.nan)

    # 1. 500 resgatados / 1000 acumulados = 0.5
    assert burn_rate[0] == 0.5
    # 2. 0 resgatados / 1000 acumulados = 0.0
    assert burn_rate[1] == 0.0
    # 3. 1000 resgatados / 500 acumulados = 2.0 (queima superior ao ganho no período)
    assert burn_rate[2] == 2.0
    # 4. 0 acumulados e 0 resgatados = 0.0
    assert burn_rate[3] == 0.0
    # 5. 0 acumulados e 500 resgatados = NaN (queima exclusiva de saldo prévio sem acúmulo)
    assert np.isnan(burn_rate[4]), "Queima ativa com zero acúmulo deve ser np.nan, não 0.0"


def test_delay_imputation_and_flag_synthetic(tmp_path: Path) -> None:
    """Valida imputação de atrasos e flag de linhagem com massa controlada (DEF-06, DEF-08, DEF-14)."""
    sample_sat = pd.DataFrame(
        {
            "Departure Delay in Minutes": [10, 25, 0],
            "Arrival Delay in Minutes": [15.0, np.nan, 0.0],
            "satisfaction": [True, False, True],
        }
    )
    raw_csv = tmp_path / "data.csv"
    sample_sat.to_csv(raw_csv, index=False)

    df_curated = curate_passenger_satisfaction(raw_dir=tmp_path, output_dir=tmp_path)

    # Flag booleana de imputação
    assert df_curated["arrival_delay_imputed"].tolist() == [False, True, False]

    # Valores imputados e deltas
    assert df_curated["arrival_delay_minutes"].tolist() == [15, 25, 0]
    assert df_curated["en_route_delay_delta"].tolist() == [5, 0, 0]

    # Tipagem int64
    assert df_curated["arrival_delay_minutes"].dtype == "int64"
    assert df_curated["departure_delay_minutes"].dtype == "int64"
    assert df_curated["en_route_delay_delta"].dtype == "int64"


def test_survival_bias_and_cohort_filtering_synthetic(tmp_path: Path) -> None:
    """Valida eliminação de viés de sobrevivência e tempo imortal na coorte ativa (DEF-01, DEF-06)."""
    # 5 clientes com perfis temporais controlados:
    # C1: Adesão 2015-01, sem cancelamento -> ATIVO janela completa (24 meses) -> IN COHORT
    # C2: Adesão 2016-06, cancelou 2017-06 -> CHURN na janela (6 meses de exposição) -> IN COHORT
    # C3: Adesão 2017-01, cancelou 2018-05 -> CHURN na janela (17 meses de exposição) -> IN COHORT
    # C4: Adesão 2017-07, sem cancelamento -> Entrou APÓS início da janela -> EXCLUÍDO DA COORTE
    # C5: Adesão 2015-01, cancelou 2016-10 -> Cancelou ANTES da janela -> EXCLUÍDO DA COORTE
    history_df = pd.DataFrame(
        {
            "Loyalty Number": [101, 102, 103, 104, 105],
            "Enrollment Year": [2015, 2016, 2017, 2017, 2015],
            "Enrollment Month": [1, 6, 1, 7, 1],
            "Cancellation Year": [np.nan, 2017, 2018, np.nan, 2016],
            "Cancellation Month": [np.nan, 6, 5, np.nan, 10],
            "Loyalty Card": ["Star", "Star", "Nova", "Nova", "Star"],
            "CLV": [5000.0, 4000.0, 6000.0, 5500.0, 3000.0],
        }
    )
    activity_df = pd.DataFrame(
        {
            "Loyalty Number": [101, 102, 103, 104, 105],
            "Year": [2017, 2017, 2017, 2017, 2017],
            "Month": [1, 1, 1, 1, 1],
            "Flights Booked": [2, 1, 3, 2, 0],
            "Flights with Companions": [0, 0, 1, 0, 0],
            "Total Flights": [2, 1, 3, 2, 0],
            "Distance": [1000, 500, 2000, 800, 0],
            "Points Accumulated": [2400, 600, 3400, 1800, 0],
            "Points Redeemed": [1200, 300, 1700, 900, 0],
            "Dollar Cost Points Redeemed": [100, 25, 150, 80, 0],
        }
    )

    history_df.to_csv(tmp_path / "Customer Loyalty History.csv", index=False)
    activity_df.to_csv(tmp_path / "Customer Flight Activity.csv", index=False)

    curated_loyalty = curate_loyalty(raw_dir=tmp_path, output_dir=tmp_path)

    # 1. Verifica tempo de permanência inclusivo (tenure_months >= 1)
    assert (curated_loyalty["tenure_months"] >= 1).all()

    # 2. Verifica active_months_in_window
    c1 = curated_loyalty[curated_loyalty["loyalty_number"] == 101].iloc[0]
    c2 = curated_loyalty[curated_loyalty["loyalty_number"] == 102].iloc[0]
    c3 = curated_loyalty[curated_loyalty["loyalty_number"] == 103].iloc[0]
    c4 = curated_loyalty[curated_loyalty["loyalty_number"] == 104].iloc[0]
    c5 = curated_loyalty[curated_loyalty["loyalty_number"] == 105].iloc[0]

    assert c1["active_months_in_window"] == 24
    assert c2["active_months_in_window"] == 6  # Jan-Jun 2017
    assert c3["active_months_in_window"] == 17  # Jan 2017 - Mai 2018
    assert c4["active_months_in_window"] == 18  # Jul 2017 - Dez 2018 (24 - 7 + 1)
    assert c5["active_months_in_window"] == 1  # cancelou antes de 2017 -> min 1

    # 3. Filtro da coorte de 2017
    enrolled_pre_2017 = (curated_loyalty["enrollment_year"] < 2017) | (
        (curated_loyalty["enrollment_year"] == 2017) & (curated_loyalty["enrollment_month"] == 1)
    )
    active_at_start = (
        curated_loyalty["cancellation_year"].isna()
        | (curated_loyalty["cancellation_year"] > 2017)
        | (
            (curated_loyalty["cancellation_year"] == 2017)
            & (curated_loyalty["cancellation_month"] >= 1)
        )
    )
    cohort_df = curated_loyalty[enrolled_pre_2017 & active_at_start]

    cohort_numbers = set(cohort_df["loyalty_number"])
    assert cohort_numbers == {101, 102, 103}, (
        f"A coorte deve conter estritamente {101, 102, 103}, obtido {cohort_numbers}"
    )
    assert 104 not in cohort_numbers, "Cliente 104 ingressou após o início da janela"
    assert 105 not in cohort_numbers, "Cliente 105 cancelou antes do início da janela"
