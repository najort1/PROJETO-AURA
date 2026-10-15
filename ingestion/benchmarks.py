"""Módulo de ingestão, curadoria e agregação de benchmarks da aviação.

Fontes brutas (data/raw/):
- Customer Loyalty History.csv: 16.737 membros do programa de fidelidade
- Customer Flight Activity.csv: 405.624 registros mensais de atividade de voo
- data.csv: 129.880 avaliações de satisfação de passageiros
- Airline_review.csv: 23.171 avaliações de companhias aéreas globais

Destinos curados (data/curated/benchmarks/):
- loyalty_aggregated.parquet
- passenger_satisfaction.parquet
- airline_reviews.parquet
- benchmark_summary.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from aura_core.log import get_logger
from aura_core.paths import ensure_dir, path

logger = get_logger("ingestion.benchmarks")

SATISFACTION_COLUMN_OVERRIDES = {
    "Departure Delay in Minutes": "departure_delay_minutes",
    "Arrival Delay in Minutes": "arrival_delay_minutes",
}

SKYTRAX_ASPECT_COLUMNS = [
    "seat_comfort",
    "cabin_staff_service",
    "food_and_beverages",
    "ground_service",
    "inflight_entertainment",
    "wifi_and_connectivity",
    "value_for_money",
]


def to_snake_case(name: str) -> str:
    """Converte um nome de coluna ou identificador para snake_case padronizado.

    Aplica transliteração Unicode NFKD prévia para preservar caracteres
    acentuados sem mutilação léxica (ex: 'Pontuação' -> 'pontuacao').
    """
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode("utf-8")
    s = s.strip()
    s = s.replace("/", "_")
    s = s.replace("&", "_and_")
    s = re.sub(r"[\s\-]+", "_", s)
    s = re.sub(r"[^a-zA-Z0-9_]", "", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_").lower()


def curate_loyalty(
    raw_dir: Path | str = "data/raw",
    output_dir: Path | str = "data/curated/benchmarks",
) -> pd.DataFrame:
    """Processa, agrega e enriquece os dados de fidelidade (Loyalty History + Flight Activity).

    - Aplica drop_duplicates() em nível de linha antes de agregar (DEF-09).
    - Agrega diretamente por cliente (Loyalty Number) em estágio único consolidado.
    - Trata casos de borda de burn_rate (DEF-10):
        * accumulated > 0: redeemed / accumulated
        * accumulated == 0 e redeemed == 0: 0.0
        * accumulated == 0 e redeemed > 0: np.nan (queima exclusiva de saldo prévio).
    - Merge 1:1 com Customer Loyalty History.
    - tenure_months com cálculo inclusivo (meses decorridos + 1, garantindo >= 1) (DEF-18).
    - Calcula active_months_in_window real na janela 2017-2018 para normalizar acúmulo (DEF-03)
      e resgates por mês ativo (redemptions_per_active_month) (DEF-01).
    - Salva em loyalty_aggregated.parquet.
    """
    raw_path = path(raw_dir)
    history_file = raw_path / "Customer Loyalty History.csv"
    activity_file = raw_path / "Customer Flight Activity.csv"

    if not history_file.exists():
        raise FileNotFoundError(f"Arquivo de histórico de fidelidade ausente: {history_file}")
    if not activity_file.exists():
        raise FileNotFoundError(f"Arquivo de atividade de voos ausente: {activity_file}")

    logger.info("Carregando Customer Flight Activity de %s...", activity_file)
    df_fa = pd.read_csv(activity_file, encoding="utf-8")
    logger.info("Registros brutos em Flight Activity: %d", len(df_fa))

    # DEF-09: Deduplicação explícita em nível de linha antes de agregar
    rows_before_dedup = len(df_fa)
    df_fa = df_fa.drop_duplicates()
    logger.info(
        "Deduplicação de voos: removidas %d linhas idênticas (restantes: %d)",
        rows_before_dedup - len(df_fa),
        len(df_fa),
    )

    # Agregação direta em estágio único por cliente
    fa_cust = df_fa.groupby("Loyalty Number", as_index=False).agg(
        {
            "Total Flights": "sum",
            "Flights Booked": "sum",
            "Flights with Companions": "sum",
            "Distance": "sum",
            "Points Accumulated": "sum",
            "Points Redeemed": "sum",
            "Dollar Cost Points Redeemed": "sum",
        }
    )

    fa_cust.rename(
        columns={
            "Loyalty Number": "loyalty_number",
            "Total Flights": "total_flights",
            "Flights Booked": "flights_booked",
            "Flights with Companions": "flights_with_companions",
            "Distance": "total_distance",
            "Points Accumulated": "total_points_accumulated",
            "Points Redeemed": "total_points_redeemed",
            "Dollar Cost Points Redeemed": "total_dollar_cost_points_redeemed",
        },
        inplace=True,
    )

    # DEF-10: Tratamento robusto de casos de borda em burn_rate
    burn_conditions = [
        fa_cust["total_points_accumulated"] > 0,
        (fa_cust["total_points_accumulated"] == 0) & (fa_cust["total_points_redeemed"] == 0),
        (fa_cust["total_points_accumulated"] == 0) & (fa_cust["total_points_redeemed"] > 0),
    ]
    burn_choices = [
        fa_cust["total_points_redeemed"] / fa_cust["total_points_accumulated"],
        0.0,
        np.nan,
    ]
    fa_cust["burn_rate"] = np.select(burn_conditions, burn_choices, default=np.nan)

    logger.info("Carregando Customer Loyalty History de %s...", history_file)
    df_lh = pd.read_csv(history_file, encoding="utf-8")
    logger.info("Clientes em Loyalty History: %d", len(df_lh))

    # Padronização de colunas para snake_case
    df_lh.columns = [to_snake_case(c) for c in df_lh.columns]

    # Merge 1:1
    loyalty_agg = pd.merge(df_lh, fa_cust, on="loyalty_number", how="left")

    # Preenchimento defensivo para métricas numéricas caso algum cliente não possua voos
    numeric_fill_cols = [
        "total_flights",
        "flights_booked",
        "flights_with_companions",
        "total_distance",
        "total_points_accumulated",
        "total_points_redeemed",
        "total_dollar_cost_points_redeemed",
    ]
    for col in numeric_fill_cols:
        loyalty_agg[col] = loyalty_agg[col].fillna(0)

    # Flag de churn
    loyalty_agg["has_churned"] = loyalty_agg["cancellation_year"].notna()

    # DEF-18: tenure_months com cálculo inclusivo (meses decorridos + 1, garantindo >= 1)
    end_year = loyalty_agg["cancellation_year"].fillna(2018).astype(int)
    end_month = loyalty_agg["cancellation_month"].fillna(12).astype(int)
    start_year = loyalty_agg["enrollment_year"].astype(int)
    start_month = loyalty_agg["enrollment_month"].astype(int)
    loyalty_agg["tenure_months"] = (end_year - start_year) * 12 + (end_month - start_month) + 1

    # DEF-03: Tempo de exposição real do cliente na janela 2017-2018 (em meses)
    # active_months_in_window = max(1, min(cancellation_date, 2018-12) - max(enrollment_date, 2017-01) + 1)
    enr_idx = (start_year - 2017) * 12 + start_month
    start_window_idx = np.maximum(1, enr_idx)
    canc_idx = np.where(
        loyalty_agg["has_churned"],
        (end_year - 2017) * 12 + end_month,
        24,
    )
    end_window_idx = np.minimum(24, canc_idx)
    exposure_months = end_window_idx - start_window_idx + 1
    loyalty_agg["active_months_in_window"] = np.maximum(1, exposure_months)

    # Média mensal baseada na exposição efetiva
    loyalty_agg["avg_points_per_month"] = (
        loyalty_agg["total_points_accumulated"] / loyalty_agg["active_months_in_window"]
    )
    # DEF-01: Resgates normalizados pelo tempo de exposição efetivo
    loyalty_agg["redemptions_per_active_month"] = (
        loyalty_agg["total_points_redeemed"] / loyalty_agg["active_months_in_window"]
    )

    out_file = ensure_dir(output_dir) / "loyalty_aggregated.parquet"
    loyalty_agg.to_parquet(out_file, index=False)
    logger.info(
        "Loyalty agregado salvo em %s (%d clientes, %d colunas)",
        out_file,
        len(loyalty_agg),
        len(loyalty_agg.columns),
    )
    return loyalty_agg


def curate_passenger_satisfaction(
    raw_dir: Path | str = "data/raw",
    output_dir: Path | str = "data/curated/benchmarks",
) -> pd.DataFrame:
    """Processa e cura a base de satisfação de passageiros (data.csv).

    - Renomeia colunas para snake_case.
    - Cria flag booleana de linhagem de imputação arrival_delay_imputed (DEF-08).
    - Trata nulos em arrival_delay_minutes imputando departure_delay_minutes.
    - Converte arrival_delay_minutes para int64 pós-imputação (DEF-14).
    - Adiciona métrica aeronáutica canônica en_route_delay_delta (DEF-02).
    - Salva em passenger_satisfaction.parquet.
    """
    raw_path = path(raw_dir)
    sat_file = raw_path / "data.csv"
    if not sat_file.exists():
        raise FileNotFoundError(f"Arquivo de satisfação de passageiros ausente: {sat_file}")

    logger.info("Carregando satisfação de passageiros de %s...", sat_file)
    df_sat = pd.read_csv(sat_file, encoding="utf-8")
    logger.info("Registros carregados: %d", len(df_sat))

    # Renomeação snake_case respeitando overrides específicos
    new_cols = [SATISFACTION_COLUMN_OVERRIDES.get(c, to_snake_case(c)) for c in df_sat.columns]
    df_sat.columns = new_cols

    # DEF-08: Flag booleana de linhagem antes do fillna
    df_sat["arrival_delay_imputed"] = df_sat["arrival_delay_minutes"].isna()
    null_count_before = int(df_sat["arrival_delay_imputed"].sum())

    # Imputação de nulos em arrival_delay_minutes via departure_delay_minutes
    df_sat["arrival_delay_minutes"] = df_sat["arrival_delay_minutes"].fillna(
        df_sat["departure_delay_minutes"]
    )
    null_count_after = int(df_sat["arrival_delay_minutes"].isna().sum())
    logger.info(
        "Imputados %d nulos de arrival_delay_minutes usando departure_delay_minutes (restantes: %d)",
        null_count_before,
        null_count_after,
    )

    # DEF-14: Conversão de tipos para int64
    df_sat["arrival_delay_minutes"] = df_sat["arrival_delay_minutes"].round().astype("int64")
    df_sat["departure_delay_minutes"] = df_sat["departure_delay_minutes"].round().astype("int64")

    # DEF-02: Métrica aeronáutica canônica de tempo ganho/perdido em rota
    df_sat["en_route_delay_delta"] = (
        df_sat["arrival_delay_minutes"] - df_sat["departure_delay_minutes"]
    )

    out_file = ensure_dir(output_dir) / "passenger_satisfaction.parquet"
    df_sat.to_parquet(out_file, index=False)
    logger.info(
        "Satisfação de passageiros salva em %s (%d avaliações, %d colunas)",
        out_file,
        len(df_sat),
        len(df_sat.columns),
    )
    return df_sat


def curate_airline_reviews(
    raw_dir: Path | str = "data/raw",
    output_dir: Path | str = "data/curated/benchmarks",
) -> pd.DataFrame:
    """Processa e cura a base de avaliações de companhias aéreas (Airline_review.csv).

    - Descarta explicitamente qualquer coluna que inicie com 'unnamed' (DEF-07).
    - Renomeia colunas para snake_case com transliteração NFKD (DEF-17).
    - Aplica .str.strip('\"\\s') em review_title (DEF-16).
    - Converte recommended para booleano nativo (DEF-15).
    - Trata valores não numéricos em overall_rating ('n' -> NaN).
    - Converte notas 0.0 para np.nan nas 7 colunas de aspectos Skytrax (DEF-11).
    - Salva em airline_reviews.parquet.
    """
    raw_path = path(raw_dir)
    reviews_file = raw_path / "Airline_review.csv"
    if not reviews_file.exists():
        raise FileNotFoundError(f"Arquivo de avaliações ausente: {reviews_file}")

    logger.info("Carregando avaliações de companhias aéreas de %s...", reviews_file)
    df_rev = pd.read_csv(reviews_file, encoding="utf-8")
    logger.info("Registros carregados: %d", len(df_rev))

    # DEF-07: Descartar explicitamente qualquer coluna que inicie com 'unnamed'
    unnamed_cols = [c for c in df_rev.columns if c.strip().lower().startswith("unnamed")]
    if unnamed_cols:
        logger.info("Descartando colunas unnamed identificadas: %s", unnamed_cols)
        df_rev = df_rev.drop(columns=unnamed_cols)

    # Renomeação snake_case
    df_rev.columns = [to_snake_case(c) for c in df_rev.columns]

    # DEF-07: Garantia pós-renomeação
    df_rev = df_rev.drop(
        columns=[c for c in df_rev.columns if c.startswith("unnamed")],
        errors="ignore",
    )

    # DEF-16: Strip de aspas e espaçamentos em review_title
    if "review_title" in df_rev.columns:
        df_rev["review_title"] = df_rev["review_title"].astype(str).str.strip(r'"\s')

    # DEF-15: Booleano nativo em recommended
    if "recommended" in df_rev.columns:
        df_rev["recommended"] = df_rev["recommended"].astype(str).str.strip().str.lower().eq("yes")

    # Conversão de overall_rating para float, transformando strings não numéricas ('n') em NaN
    non_num_count = int(
        (~pd.to_numeric(df_rev["overall_rating"], errors="coerce").notna()).sum()
        - df_rev["overall_rating"].isna().sum()
    )
    df_rev["overall_rating"] = pd.to_numeric(df_rev["overall_rating"], errors="coerce")
    logger.info(
        "Tratados %d valores não numéricos em overall_rating para NaN (total nulos final: %d)",
        non_num_count,
        int(df_rev["overall_rating"].isna().sum()),
    )

    # DEF-11: Converter notas 0.0 para np.nan nas 7 colunas de aspectos de avaliação de voo da Skytrax
    for col in SKYTRAX_ASPECT_COLUMNS:
        if col in df_rev.columns:
            df_rev[col] = pd.to_numeric(df_rev[col], errors="coerce").replace(0.0, np.nan)

    out_file = ensure_dir(output_dir) / "airline_reviews.parquet"
    df_rev.to_parquet(out_file, index=False)
    logger.info(
        "Avaliações salvas em %s (%d avaliações, %d colunas)",
        out_file,
        len(df_rev),
        len(df_rev.columns),
    )
    return df_rev


def generate_benchmark_summary(
    loyalty_df: pd.DataFrame,
    satisfaction_df: pd.DataFrame,
    reviews_df: pd.DataFrame,
    output_dir: Path | str = "data/curated/benchmarks",
) -> dict[str, Any]:
    """Calcula estatísticas agregadas e exporta benchmark_summary.json.

    Métricas geradas:
    - Loyalty:
        * Métricas gerais de base e CLV por tier.
        * Análise rigorosa sobre coorte ativa 2017 (eliminando immortal time bias) (DEF-01).
        * Correlações com resgates normalizados por tempo de exposição efetivo.
    - Satisfaction:
        * Satisfação geral (%) e médias de atraso por status (DEF-02: sem dupla contagem).
        * Médias de departure_delay_minutes, arrival_delay_minutes e en_route_delay_delta.
        * Aspecto com menor nota.
    - Reviews:
        * top_rated_airlines com representatividade (>= 50 reviews) ordenadas por nota (DEF-13).
        * Nota média global.
    """
    logger.info("Calculando métricas agregadas consolidadas...")

    # 1. Loyalty metrics
    total_customers = int(len(loyalty_df))
    churn_count = int(loyalty_df["has_churned"].sum())
    churn_rate_pct = round(float(loyalty_df["has_churned"].mean() * 100), 2)
    avg_clv_by_tier = {
        tier: round(float(val), 2)
        for tier, val in loyalty_df.groupby("loyalty_card")["clv"].mean().items()
    }

    # DEF-01: Filtrar coorte de clientes ativos no início da janela temporal (adesão <= 2017-01
    # e cancelamento nulo ou >= 2017-01), eliminando immortal time bias e viés de sobrevivência.
    enrolled_pre_2017 = (loyalty_df["enrollment_year"] < 2017) | (
        (loyalty_df["enrollment_year"] == 2017) & (loyalty_df["enrollment_month"] == 1)
    )
    active_at_start = (
        loyalty_df["cancellation_year"].isna()
        | (loyalty_df["cancellation_year"] > 2017)
        | ((loyalty_df["cancellation_year"] == 2017) & (loyalty_df["cancellation_month"] >= 1))
    )
    cohort_mask = enrolled_pre_2017 & active_at_start
    cohort_df = loyalty_df[cohort_mask]

    cohort_total = int(len(cohort_df))
    cohort_churn_count = int(cohort_df["has_churned"].sum())
    cohort_churn_rate_pct = round(float(cohort_df["has_churned"].mean() * 100), 2)

    # Normalizar volume de resgates pelo tempo de exposição efetivo do cliente na janela
    corr_redemptions_rate_churn = round(
        float(
            cohort_df["redemptions_per_active_month"].corr(cohort_df["has_churned"].astype(float))
        ),
        4,
    )
    valid_burn = cohort_df["burn_rate"].dropna()
    corr_burn_rate_churn = round(
        float(valid_burn.corr(cohort_df.loc[valid_burn.index, "has_churned"].astype(float))),
        4,
    )
    corr_total_points_churn = round(
        float(cohort_df["total_points_redeemed"].corr(cohort_df["has_churned"].astype(float))),
        4,
    )

    loyalty_metrics = {
        "total_customers": total_customers,
        "churn_rate_pct": churn_rate_pct,
        "churn_count": churn_count,
        "avg_clv_by_tier": avg_clv_by_tier,
        "active_cohort_2017": {
            "cohort_definition": (
                "Clientes com adesão <= 2017-01 e ativos no início da janela temporal "
                "(cancelamento nulo ou >= 2017-01)"
            ),
            "total_customers": cohort_total,
            "churn_count": cohort_churn_count,
            "churn_rate_pct": cohort_churn_rate_pct,
            "correlation_redemptions_per_active_month_vs_churn": corr_redemptions_rate_churn,
            "correlation_burn_rate_vs_churn": corr_burn_rate_churn,
            "correlation_total_points_redeemed_vs_churn": corr_total_points_churn,
            "methodological_notes": (
                "Para eliminar o viés de tempo imortal (immortal time bias) e o viés de sobrevivência, "
                "a análise de correlação entre resgates e retenção foi calculada estritamente sobre a coorte "
                "de clientes já filiados no início da janela (2017-01) que não haviam cancelado antes de 2017. "
                "O volume de resgate foi normalizado pelos meses ativos na janela (redemptions_per_active_month)."
            ),
        },
        "correlation_points_redeemed_vs_churn": corr_redemptions_rate_churn,
        "correlation_burn_rate_vs_churn": corr_burn_rate_churn,
    }

    # 2. Satisfaction metrics (DEF-02: sem total_delay_minutes espúrio)
    total_passengers = int(len(satisfaction_df))
    satisfaction_rate_pct = round(float(satisfaction_df["satisfaction"].mean() * 100), 2)

    sat_grouped = satisfaction_df.groupby("satisfaction")
    sat_true = sat_grouped.get_group(True)
    sat_false = sat_grouped.get_group(False)

    avg_delays = {
        "satisfied": {
            "departure_delay_minutes": round(float(sat_true["departure_delay_minutes"].mean()), 2),
            "arrival_delay_minutes": round(float(sat_true["arrival_delay_minutes"].mean()), 2),
            "en_route_delay_delta": round(float(sat_true["en_route_delay_delta"].mean()), 2),
        },
        "dissatisfied": {
            "departure_delay_minutes": round(float(sat_false["departure_delay_minutes"].mean()), 2),
            "arrival_delay_minutes": round(float(sat_false["arrival_delay_minutes"].mean()), 2),
            "en_route_delay_delta": round(float(sat_false["en_route_delay_delta"].mean()), 2),
        },
    }

    # Aspectos avaliados (notas de 1 a 5)
    non_aspect_cols = {
        "gender",
        "customer_type",
        "age",
        "type_of_travel",
        "class",
        "flight_distance",
        "departure_delay_minutes",
        "arrival_delay_minutes",
        "arrival_delay_imputed",
        "en_route_delay_delta",
        "satisfaction",
    }
    aspect_cols = [c for c in satisfaction_df.columns if c not in non_aspect_cols]
    aspect_scores = {c: round(float(satisfaction_df[c].mean()), 2) for c in aspect_cols}
    lowest_aspect_name = min(aspect_scores.keys(), key=lambda k: aspect_scores[k])
    lowest_aspect_val = aspect_scores[lowest_aspect_name]

    satisfaction_metrics = {
        "total_passengers": total_passengers,
        "satisfaction_rate_pct": satisfaction_rate_pct,
        "avg_delay_by_satisfaction": avg_delays,
        "lowest_rated_aspect": {
            "aspect": lowest_aspect_name,
            "mean_score": lowest_aspect_val,
        },
        "aspect_scores": aspect_scores,
    }

    # 3. Reviews metrics
    total_reviews = int(len(reviews_df))
    valid_rating_count = int(reviews_df["overall_rating"].count())
    global_avg_rating = round(float(reviews_df["overall_rating"].mean()), 2)

    # DEF-13: top_rated_airlines com representatividade (>= 50 reviews válidas), ordenadas pela média
    airline_agg = (
        reviews_df.groupby("airline_name")
        .agg(
            review_count=("overall_rating", "count"),
            mean_rating=("overall_rating", "mean"),
        )
        .reset_index()
    )
    rep_airlines = airline_agg[airline_agg["review_count"] >= 50]
    top_rated_df = rep_airlines.sort_values(
        ["mean_rating", "review_count"], ascending=[False, False]
    ).head(10)

    top_rated_list = [
        {
            "airline_name": row["airline_name"],
            "review_count": int(row["review_count"]),
            "avg_rating": round(float(row["mean_rating"]), 2)
            if pd.notnull(row["mean_rating"])
            else None,
        }
        for _, row in top_rated_df.iterrows()
    ]

    reviews_metrics = {
        "total_reviews": total_reviews,
        "valid_rating_count": valid_rating_count,
        "global_avg_rating": global_avg_rating,
        "top_rated_airlines": top_rated_list,
    }

    summary = {
        "_meta": {
            "generated_at": dt.datetime.now(dt.UTC).isoformat(),
            "description": "Métricas consolidadas dos benchmarks de Loyalty, Satisfação e Reviews (Aura 2.0)",
        },
        "loyalty": loyalty_metrics,
        "satisfaction": satisfaction_metrics,
        "reviews": reviews_metrics,
    }

    summary_file = ensure_dir(output_dir) / "benchmark_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    logger.info("Sumário salvo em %s", summary_file)
    return summary


def run_all(
    raw_dir: Path | str = "data/raw",
    output_dir: Path | str = "data/curated/benchmarks",
) -> dict[str, Any]:
    """Executa o pipeline completo de benchmarks e exporta todos os artefatos curados."""
    logger.info("=== Iniciando Pipeline de Benchmarks (Aura 2.0) ===")
    out = ensure_dir(output_dir)

    loyalty_df = curate_loyalty(raw_dir, out)
    sat_df = curate_passenger_satisfaction(raw_dir, out)
    rev_df = curate_airline_reviews(raw_dir, out)
    summary = generate_benchmark_summary(loyalty_df, sat_df, rev_df, out)

    logger.info("=== Pipeline de Benchmarks concluído com sucesso ===")
    return summary


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint para execução via python -m ingestion.benchmarks.

    Aceita argumentos --raw-dir e --output-dir para permitir execução
    hermética e isolada (DEF-05).
    """
    parser = argparse.ArgumentParser(description="Pipeline de benchmarks da aviação.")
    parser.add_argument(
        "--raw-dir",
        default="data/raw",
        help="Diretório contendo os arquivos brutos CSV (padrão: data/raw)",
    )
    parser.add_argument(
        "--output-dir",
        default="data/curated/benchmarks",
        help="Diretório de saída para artefatos curados (padrão: data/curated/benchmarks)",
    )

    if argv is None:
        argv = sys.argv[1:] if __name__ == "__main__" else []
    args = parser.parse_args(argv)

    run_all(raw_dir=args.raw_dir, output_dir=args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
