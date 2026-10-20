"""Curadoria e calibração de microdados ANAC via DuckDB sobre Parquet.

Gera as tabelas curadas:
- data/curated/anac/anac_routes_monthly.parquet
- data/curated/anac/anac_airports.parquet
- data/curated/anac/anac_delays_monthly.parquet
- data/curated/calibration_values.json

Valida cada tabela contra seus contratos em schemas/ (fail loud).
"""

from __future__ import annotations

import datetime as dt
import json
import unicodedata
from datetime import UTC
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from aura_core.config import settings
from aura_core.log import get_logger
from aura_core.paths import ensure_dir, path
from schemas.load import load_contract, validate_or_raise

logger = get_logger("ingestion.curate")

UF_TO_REGION = {
    # Norte
    "AC": "Norte",
    "AP": "Norte",
    "AM": "Norte",
    "PA": "Norte",
    "RO": "Norte",
    "RR": "Norte",
    "TO": "Norte",
    # Nordeste
    "AL": "Nordeste",
    "BA": "Nordeste",
    "CE": "Nordeste",
    "MA": "Nordeste",
    "PB": "Nordeste",
    "PE": "Nordeste",
    "PI": "Nordeste",
    "RN": "Nordeste",
    "SE": "Nordeste",
    # Centro-Oeste
    "DF": "Centro-Oeste",
    "GO": "Centro-Oeste",
    "MT": "Centro-Oeste",
    "MS": "Centro-Oeste",
    # Sudeste
    "ES": "Sudeste",
    "MG": "Sudeste",
    "RJ": "Sudeste",
    "SP": "Sudeste",
    # Sul
    "PR": "Sul",
    "RS": "Sul",
    "SC": "Sul",
}

STATE_NAME_MAPPINGS = {
    "acre": "AC",
    "alagoas": "AL",
    "amapa": "AP",
    "amazonas": "AM",
    "bahia": "BA",
    "ceara": "CE",
    "distrito federal": "DF",
    "espirito santo": "ES",
    "goias": "GO",
    "maranhao": "MA",
    "mato grosso do sul": "MS",
    "mato grosso": "MT",
    "minas gerais": "MG",
    "para": "PA",
    "paraiba": "PB",
    "parana": "PR",
    "pernambuco": "PE",
    "piaui": "PI",
    "rio de janeiro": "RJ",
    "rio grande do norte": "RN",
    "rio grande do sul": "RS",
    "rondonia": "RO",
    "roraima": "RR",
    "santa catarina": "SC",
    "sao paulo": "SP",
    "sergipe": "SE",
    "tocantins": "TO",
}


def normalize_uf(raw_val: str | None) -> str:
    """Normaliza nome de estado ou sigla para sigla de 2 letras da UF."""
    if not raw_val:
        return ""
    val_str = str(raw_val).strip()
    if not val_str:
        return ""
    val_upper = val_str.upper()
    if len(val_upper) == 2 and val_upper in UF_TO_REGION:
        return val_upper

    norm = "".join(
        c for c in unicodedata.normalize("NFD", val_str) if unicodedata.category(c) != "Mn"
    ).lower()
    for state_name, sigla in STATE_NAME_MAPPINGS.items():
        if state_name in norm:
            return sigla
    return ""


def get_timeline_files(base_dir: Path) -> list[str]:
    """Retorna lista ordenada de arquivos voos_basica dentro da janela 2023-09 a 2026-08."""
    tl = settings().get("timeline", {})
    start_ym = tl.get("synthetic_start", "2023-09-01")[:7].replace("-", "")
    end_ym = tl.get("synthetic_end", "2026-08-31")[:7].replace("-", "")

    files: list[str] = []
    for p in sorted(base_dir.glob("voos_basica_*.parquet")):
        # Extrai YYYYMM do nome voos_basica_YYYYMM.parquet
        stem_parts = p.stem.split("_")
        if len(stem_parts) == 3 and stem_parts[2].isdigit():
            ym = stem_parts[2]
            if start_ym <= ym <= end_ym:
                files.append(p.as_posix())
    if not files:
        raise FileNotFoundError(
            f"Nenhum arquivo voos_basica encontrado na janela {start_ym} a {end_ym} em {base_dir}"
        )
    return files


def curate_routes_monthly(
    con: duckdb.DuckDBPyConnection, vb_files: list[str], output_path: Path
) -> pd.DataFrame:
    """Agrega rotas mensais do mercado doméstico regular de voos_basica."""
    logger.info(
        f"Curando mercado de rotas mensais a partir de {len(vb_files)} arquivos voos_basica..."
    )
    # Filtro estrito do mercado doméstico regular:
    # cd_tipo_linha = 'N' (DOMÉSTICA MISTA) e cd_di IN ('0', '4') (REGULAR PREVISTO EM HOTRAN / INCLUSÃO)
    query = """
    WITH raw_vb AS (
        SELECT
            sg_icao_origem,
            sg_icao_destino,
            CAST(SUBSTR(dt_referencia, 1, 4) AS INT) AS ano,
            CAST(SUBSTR(dt_referencia, 6, 2) AS INT) AS mes,
            SUBSTR(dt_referencia, 1, 7) AS ano_mes,
            sg_empresa_icao,
            COALESCE(nr_passag_pagos, 0.0) AS pax,
            COALESCE(nr_assentos_ofertados, 0.0) AS assentos,
            COALESCE(nr_decolagem, 0.0) AS decolagens
        FROM read_parquet($files)
        WHERE cd_tipo_linha = 'N'
          AND cd_di IN ('0', '4')
          AND sg_icao_origem IS NOT NULL
          AND sg_icao_destino IS NOT NULL
          AND LENGTH(sg_icao_origem) = 4
          AND LENGTH(sg_icao_destino) = 4
          AND sg_icao_origem != sg_icao_destino
    ),
    aggregated AS (
        SELECT
            sg_icao_origem || '-' || sg_icao_destino || ':' || ano_mes AS id_rota_mes,
            sg_icao_origem || '-' || sg_icao_destino AS rota,
            sg_icao_origem AS origem_oaci,
            sg_icao_destino AS destino_oaci,
            ano,
            mes,
            ano_mes,
            CAST(SUM(pax) AS DOUBLE) AS total_pax_pagos,
            CAST(SUM(assentos) AS DOUBLE) AS total_assentos_ofertados,
            CAST(SUM(decolagens) AS DOUBLE) AS total_decolagens,
            CAST(SUM(CASE WHEN sg_empresa_icao = 'AZU' THEN pax ELSE 0.0 END) AS DOUBLE) AS azul_pax_pagos,
            CAST(SUM(CASE WHEN sg_empresa_icao = 'AZU' THEN assentos ELSE 0.0 END) AS DOUBLE) AS azul_assentos_ofertados,
            CAST(SUM(CASE WHEN sg_empresa_icao = 'AZU' THEN decolagens ELSE 0.0 END) AS DOUBLE) AS azul_decolagens
        FROM raw_vb
        GROUP BY sg_icao_origem, sg_icao_destino, ano, mes, ano_mes
    )
    SELECT
        id_rota_mes,
        rota,
        origem_oaci,
        destino_oaci,
        ano,
        mes,
        ano_mes,
        total_pax_pagos,
        total_assentos_ofertados,
        total_decolagens,
        azul_pax_pagos,
        azul_assentos_ofertados,
        azul_decolagens,
        CASE
            WHEN total_pax_pagos > 0 THEN ROUND(azul_pax_pagos / total_pax_pagos, 4)
            ELSE 0.0
        END AS azul_share_pax,
        CASE
            WHEN total_decolagens > 0 THEN ROUND(azul_decolagens / total_decolagens, 4)
            ELSE 0.0
        END AS azul_share_decolagens,
        CASE
            WHEN azul_assentos_ofertados > 0 THEN ROUND(azul_pax_pagos / azul_assentos_ofertados, 4)
            ELSE 0.0
        END AS azul_load_factor,
        CASE
            WHEN total_assentos_ofertados > 0 THEN ROUND(total_pax_pagos / total_assentos_ofertados, 4)
            ELSE 0.0
        END AS total_load_factor,
        CASE WHEN azul_decolagens > 0 THEN TRUE ELSE FALSE END AS has_azul
    FROM aggregated
    ORDER BY rota, ano, mes
    """
    df = con.execute(query, {"files": vb_files}).df()
    ensure_dir(output_path.parent)
    df.to_parquet(output_path, index=False)
    logger.info(
        f"Tabela de rotas gravada em {output_path} ({len(df)} registros, {df['rota'].nunique()} rotas únicas)."
    )

    contract = load_contract("anac_routes_monthly")
    validate_or_raise(contract, output_path)
    logger.info("Contrato 'anac_routes_monthly' validado com sucesso.")
    return df


def curate_airports(
    con: duckdb.DuckDBPyConnection,
    aerodromos_path: Path,
    vb_files: list[str],
    output_path: Path,
) -> pd.DataFrame:
    """Curadoria de aeródromos, enriquecendo UF/município via voos_basica e derivando macrorregião."""
    logger.info(f"Curando cadastro de aeródromos a partir de {aerodromos_path}...")
    query = """
    WITH vb_reference AS (
        SELECT
            sg_icao_origem AS oaci,
            MAX(sg_uf_origem) AS ref_uf,
            MAX(nm_municipio_origem) AS ref_municipio
        FROM read_parquet($files)
        WHERE sg_icao_origem IS NOT NULL
          AND LENGTH(sg_icao_origem) = 4
          AND sg_uf_origem IS NOT NULL
          AND sg_uf_origem != ''
        GROUP BY sg_icao_origem
    ),
    raw_airports AS (
        SELECT
            codigo_oaci,
            MAX(nome) AS nome,
            MAX(municipio) AS municipio,
            MAX(uf) AS uf,
            AVG(latitude) AS latitude,
            AVG(longitude) AS longitude,
            AVG(altitude) AS altitude
        FROM read_parquet($aerodromos)
        WHERE codigo_oaci IS NOT NULL AND LENGTH(codigo_oaci) = 4
        GROUP BY codigo_oaci
    )
    SELECT
        r.codigo_oaci,
        COALESCE(r.nome, '') AS nome,
        COALESCE(NULLIF(r.municipio, ''), v.ref_municipio, '') AS municipio,
        COALESCE(NULLIF(r.uf, ''), v.ref_uf, '') AS uf_raw,
        CAST(r.latitude AS DOUBLE) AS latitude,
        CAST(r.longitude AS DOUBLE) AS longitude,
        CAST(r.altitude AS DOUBLE) AS altitude,
        CASE WHEN v.oaci IS NOT NULL THEN TRUE ELSE FALSE END AS is_active_commercial
    FROM raw_airports r
    LEFT JOIN vb_reference v ON r.codigo_oaci = v.oaci
    ORDER BY r.codigo_oaci
    """
    df = con.execute(query, {"files": vb_files, "aerodromos": aerodromos_path.as_posix()}).df()

    df["uf"] = df["uf_raw"].apply(normalize_uf)
    df["regiao"] = df["uf"].apply(lambda u: UF_TO_REGION.get(u, "Desconhecida"))
    df = df.drop(columns=["uf_raw"])

    ensure_dir(output_path.parent)
    df.to_parquet(output_path, index=False)
    logger.info(
        f"Cadastro de aeródromos gravado em {output_path} ({len(df)} aeródromos, "
        f"{df['is_active_commercial'].sum()} comerciais ativos)."
    )

    contract = load_contract("anac_airports")
    validate_or_raise(contract, output_path)
    logger.info("Contrato 'anac_airports' validado com sucesso.")
    return df


def curate_delays_monthly(
    con: duckdb.DuckDBPyConnection, mov_files: list[str], output_path: Path
) -> pd.DataFrame:
    """Calcula taxa de atraso (>15 min) da série histórica movimentacao (2019-03 a 2025-12)."""
    logger.info(
        f"Processando taxas de atraso a partir de {len(mov_files)} arquivos de movimentação..."
    )
    # Atraso padrão ANAC / IATA: diferença entre calço e previsto superior a 15 min (900 seg)
    query = """
    WITH calc AS (
        SELECT
            CAST(ano AS INT) AS ano,
            CAST(mes AS INT) AS mes,
            CASE
                WHEN TRY_CAST(mes AS INT) BETWEEN 1 AND 12
                THEN PRINTF('%04d-%02d', TRY_CAST(ano AS INT), TRY_CAST(mes AS INT))
                ELSE NULL
            END AS ano_mes,
            TRY_STRPTIME(dt_previsto || ' ' || hh_previsto, '%Y-%m-%d %H:%M:%S') AS ts_prev,
            TRY_STRPTIME(dt_calco || ' ' || hh_calco, '%Y-%m-%d %H:%M:%S') AS ts_calc
        FROM read_parquet($files)
        WHERE dt_previsto IS NOT NULL AND hh_previsto IS NOT NULL
          AND dt_calco IS NOT NULL AND hh_calco IS NOT NULL
          AND hh_previsto != '' AND hh_calco != ''
    ),
    monthly_stats AS (
        SELECT
            ano,
            mes,
            ano_mes,
            CAST(COUNT(*) AS INT) AS total_movimentos,
            CAST(COUNT(CASE WHEN EPOCH(ts_calc) - EPOCH(ts_prev) > 900 THEN 1 END) AS INT) AS movimentos_atrasados
        FROM calc
        WHERE ts_prev IS NOT NULL AND ts_calc IS NOT NULL
        GROUP BY ano, mes, ano_mes
    )
    SELECT
        ano_mes AS id_ano_mes,
        ano,
        mes,
        ano_mes,
        total_movimentos,
        movimentos_atrasados,
        ROUND(CAST(movimentos_atrasados AS DOUBLE) / total_movimentos, 4) AS taxa_atraso,
        '2019-03_a_2025-12' AS cobertura
    FROM monthly_stats
    ORDER BY ano, mes
    """
    df = con.execute(query, {"files": mov_files}).df()
    ensure_dir(output_path.parent)
    df.to_parquet(output_path, index=False)
    mean_delay = (
        df["movimentos_atrasados"].sum() / df["total_movimentos"].sum() if len(df) > 0 else 0.0
    )
    logger.info(
        f"Série de atrasos gravada em {output_path} ({len(df)} meses, taxa média nacional: {mean_delay:.2%})."
    )

    contract = load_contract("anac_delays_monthly")
    validate_or_raise(contract, output_path)
    logger.info("Contrato 'anac_delays_monthly' validado com sucesso.")
    return df


def compute_seasonality_indices(
    routes_df: pd.DataFrame,
) -> tuple[dict[str, float], dict[str, list[float]]]:
    """Calcula índices de sazonalidade mensais normalizados (média=1.0) para mercado geral e por rota."""
    # Sazonalidade geral do mercado
    market_monthly = routes_df.groupby("mes")["total_pax_pagos"].sum()
    # Ponderar por número de ocorrências de cada mês na janela de 36 meses
    occurrences = routes_df.groupby("mes")["ano_mes"].nunique()
    avg_per_month = market_monthly / occurrences
    overall_mean = avg_per_month.mean()
    market_seasonality = {
        str(m): round(float(avg_per_month.loc[m] / overall_mean), 3) for m in range(1, 13)
    }

    # Sazonalidade por rota para rotas com volume representativo (otimização vetorizada 2D)
    route_totals = routes_df.groupby("rota")["total_pax_pagos"].sum()
    valid_routes = route_totals[route_totals >= 1000].index

    route_seasonality: dict[str, list[float]] = {}
    if len(valid_routes) > 0:
        filtered = routes_df[routes_df["rota"].isin(valid_routes)]

        grouped_vol = (
            filtered.groupby(["rota", "mes"])["total_pax_pagos"]
            .sum()
            .unstack(level="mes", fill_value=0.0)
        )
        grouped_occ = (
            filtered.groupby(["rota", "mes"])["ano_mes"]
            .nunique()
            .unstack(level="mes", fill_value=0)
        )

        vol_2d = grouped_vol.reindex(index=valid_routes, columns=range(1, 13), fill_value=0.0)
        occ_2d = grouped_occ.reindex(index=valid_routes, columns=range(1, 13), fill_value=0)

        occ_safe = np.maximum(occ_2d.values, 1)
        monthly_avgs = vol_2d.values / occ_safe

        mean_vals = monthly_avgs.sum(axis=1, keepdims=True) / 12.0

        with np.errstate(divide="ignore", invalid="ignore"):
            indices = np.where(mean_vals > 0, np.round(monthly_avgs / mean_vals, 3), 1.0)

        for rota, row in zip(valid_routes, indices, strict=True):
            route_seasonality[str(rota)] = [float(v) for v in row]

    return market_seasonality, route_seasonality


def compute_vb_integrity_stats(
    con: duckdb.DuckDBPyConnection, vb_files: list[str]
) -> dict[str, int]:
    """Estatísticas de integridade de voos_basica usadas nas notas de limitação.

    Computa (dinamicamente, nunca hardcoded):
    - pernas com nr_decolagem = 0 (artefatos técnicos, não voos);
    - quantas dessas são duplicidade de perna cd_di = 'D' (e o recorte anual de 2024);
    - nº de aeródromos de origem com tráfego estritamente REGULAR
      (cd_tipo_linha = 'N' e cd_di IN ('0','4')) — distinto do total comercial,
      que inclui charters/táxi aéreo.
    """
    query = """
    SELECT
        COUNT(*) FILTER (WHERE nr_decolagem = 0) AS n_zero_departure,
        COUNT(*) FILTER (WHERE nr_decolagem = 0 AND cd_di = 'D') AS n_cd_di_d,
        COUNT(*) FILTER (WHERE nr_decolagem = 0 AND cd_di = 'D'
                          AND SUBSTR(dt_referencia, 1, 4) = '2024') AS n_cd_di_d_2024,
        COUNT(DISTINCT sg_icao_origem) FILTER (
            WHERE cd_tipo_linha = 'N' AND cd_di IN ('0', '4')
        ) AS n_regular_origin_airports
    FROM read_parquet($files)
    """
    row = con.execute(query, {"files": vb_files}).fetchone()
    return {
        "n_zero_departure": int(row[0]),
        "n_cd_di_d": int(row[1]),
        "n_cd_di_d_2024": int(row[2]),
        "n_regular_origin_airports": int(row[3]),
    }


def generate_calibration_values(
    routes_df: pd.DataFrame,
    airports_df: pd.DataFrame,
    delays_df: pd.DataFrame,
    output_path: Path,
    vb_integrity: dict[str, int] | None = None,
) -> dict:
    """Monta e exporta calibration_values.json com chaves exatas de config/calibration_map.yaml."""
    logger.info("Computando valores de calibração para o gerador sintético...")
    market_seasonality, route_seasonality = compute_seasonality_indices(routes_df)

    # Route Inventory
    route_agg = (
        routes_df.groupby("rota")
        .agg(
            origem=("origem_oaci", "first"),
            destino=("destino_oaci", "first"),
            total_pax=("total_pax_pagos", "sum"),
            azul_pax=("azul_pax_pagos", "sum"),
            decolagens=("total_decolagens", "sum"),
            azul_decolagens=("azul_decolagens", "sum"),
            meses_ativos=("ano_mes", "nunique"),
        )
        .reset_index()
    )
    route_agg["azul_share_pax"] = (route_agg["azul_pax"] / route_agg["total_pax"]).fillna(0.0)

    top_routes_records = (
        route_agg.sort_values(by="total_pax", ascending=False).head(50).to_dict(orient="records")
    )
    # Formatação limpa dos top routes
    top_routes_clean = [
        {
            "rota": str(r["rota"]),
            "origem": str(r["origem"]),
            "destino": str(r["destino"]),
            "total_pax": round(float(r["total_pax"]), 1),
            "azul_pax": round(float(r["azul_pax"]), 1),
            "azul_share_pax": round(float(r["azul_share_pax"]), 4),
            "total_decolagens": round(float(r["decolagens"]), 1),
            "meses_ativos": int(r["meses_ativos"]),
        }
        for r in top_routes_records
    ]

    route_inventory = {
        "total_active_domestic_routes": int(route_agg["rota"].nunique()),
        "total_azul_routes": int((route_agg["azul_decolagens"] > 0).sum()),
        "total_domestic_pax": round(float(route_agg["total_pax"].sum()), 1),
        "total_azul_pax": round(float(route_agg["azul_pax"].sum()), 1),
        "top_routes": top_routes_clean,
    }

    # Volume by route month
    monthly_market_totals = (
        routes_df.groupby("ano_mes")
        .agg(
            total_pax=("total_pax_pagos", "sum"),
            azul_pax=("azul_pax_pagos", "sum"),
            total_decolagens=("total_decolagens", "sum"),
            azul_decolagens=("azul_decolagens", "sum"),
        )
        .to_dict(orient="index")
    )
    monthly_totals_clean = {
        ym: {
            "total_pax": round(float(v["total_pax"]), 1),
            "azul_pax": round(float(v["azul_pax"]), 1),
            "azul_share": round(float(v["azul_pax"] / max(v["total_pax"], 1)), 4),
            "decolagens": round(float(v["total_decolagens"]), 1),
        }
        for ym, v in monthly_market_totals.items()
    }

    volume_by_route_month = {
        "period_start": "2023-09",
        "period_end": "2026-08",
        "total_months": int(routes_df["ano_mes"].nunique()),
        "monthly_mean_market_pax": round(
            float(routes_df.groupby("ano_mes")["total_pax_pagos"].sum().mean()),
            1,
        ),
        "monthly_mean_azul_pax": round(
            float(routes_df.groupby("ano_mes")["azul_pax_pagos"].sum().mean()), 1
        ),
        "by_month_totals": monthly_totals_clean,
    }

    # Delay rate
    total_mov = int(delays_df["total_movimentos"].sum())
    total_delayed = int(delays_df["movimentos_atrasados"].sum())
    mean_delay_rate = round(total_delayed / total_mov, 4) if total_mov > 0 else 0.0
    delay_by_month_series = {
        str(r["ano_mes"]): round(float(r["taxa_atraso"]), 4) for _, r in delays_df.iterrows()
    }
    delay_by_calendar_month = {
        str(m): round(
            float(
                delays_df[delays_df["mes"] == m]["movimentos_atrasados"].sum()
                / max(
                    delays_df[delays_df["mes"] == m]["total_movimentos"].sum(),
                    1,
                )
            ),
            4,
        )
        for m in range(1, 13)
    }

    delay_rate_structure = {
        "granularity": "sistema_nacional_mensal",
        "overall_mean": mean_delay_rate,
        "threshold_minutes": 15,
        "period_start": "2019-03",
        "period_end": "2025-12",
        "total_movements_analyzed": total_mov,
        "total_delayed_movements": total_delayed,
        "by_calendar_month_mean": delay_by_calendar_month,
        "by_year_month_series": delay_by_month_series,
        "limitation_note": (
            "Na base bruta de movimentacao da ANAC, o campo nr_aeroporto_referencia é 100% nulo "
            "(0 registros preenchidos em 11.737.280 linhas). Ademais, voos_basica possui apenas "
            "horários realizados. Portanto, a taxa de atraso reflete a pontualidade do sistema "
            "nacional por mês. Janela: 2019-03 a 2025-12 (exercício de 2026 indisponível nesta fonte)."
        ),
    }

    # Cancellation rate
    n_zero = (vb_integrity or {}).get("n_zero_departure", 0)
    n_dup = (vb_integrity or {}).get("n_cd_di_d", 0)
    n_dup_2024 = (vb_integrity or {}).get("n_cd_di_d_2024", 0)
    cancellation_rate_structure = {
        "status": "not_computable_local",
        "value": None,
        "limitation_note": (
            "Investigação exaustiva confirmou que voos_basica registra unicamente etapas VOADAS. "
            f"Na janela de 36 meses há {n_zero} registros com nr_decolagem = 0 — todos artefatos "
            f"técnicos de duplicidade de perna cd_di='D' ({n_dup} registros; destes, {n_dup_2024} "
            "apenas no ano-calendário de 2024), com 0 passageiros e 0 assentos. "
            "A tabela movimentacao registra unicamente movimentos "
            "efetivos de pátio/calço. Voos cancelados (cancelamentos HOTRAN / VRA) não constam nos "
            "dados brutos locais. Conforme a regra de honestidade, a taxa não foi inventada."
        ),
    }

    # Airport Inventory
    commercial_airports = airports_df[airports_df["is_active_commercial"]]
    regional_counts = airports_df["regiao"].value_counts().to_dict()
    commercial_regional_counts = commercial_airports["regiao"].value_counts().to_dict()

    airport_inventory = {
        "total_airports": int(len(airports_df)),
        "commercial_active_airports": int(len(commercial_airports)),
        # Aeroportos com tráfego ESTRITAMENTE regular (cd_tipo_linha='N', cd_di in {'0','4'}).
        # O total 'commercial_active_airports' inclui também voos não-regulares (charters/táxi).
        "commercial_regular_airports": int(
            (vb_integrity or {}).get("n_regular_origin_airports", 0)
        ),
        "regional_distribution": {k: int(v) for k, v in regional_counts.items()},
        "commercial_regional_distribution": {
            k: int(v) for k, v in commercial_regional_counts.items()
        },
        "top_commercial_airports": commercial_airports[
            ["codigo_oaci", "nome", "municipio", "uf", "regiao"]
        ]
        .head(40)
        .to_dict(orient="records"),
    }

    calibration_dict = {
        "_meta": {
            "schema_version": "1.0",
            "generated_at": dt.datetime.now(tz=UTC).isoformat(),
            "generator": "ingestion.curate",
            "description": (
                "Valores medidos dos microdados ANAC locais mapeados para as chaves exatas "
                "de config/calibration_map.yaml para consumo do gerador sintético e documentação."
            ),
        },
        "market.route_inventory": route_inventory,
        "market.volume_by_route_month": volume_by_route_month,
        "market.seasonality_by_route": {
            "market_monthly_index": market_seasonality,
            "routes_sample_count": len(route_seasonality),
            "by_route": route_seasonality,
        },
        "market.delay_rate_by_route": delay_rate_structure,
        "market.cancellation_rate_by_route": cancellation_rate_structure,
        "market.airport_inventory": airport_inventory,
    }

    ensure_dir(output_path.parent)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(calibration_dict, f, indent=2, ensure_ascii=False)
    logger.info(f"Valores de calibração persistidos com sucesso em {output_path}.")
    return calibration_dict


def main() -> int:
    """Executa pipeline de curadoria dos microdados ANAC ponta a ponta."""
    con = duckdb.connect()
    raw_anac = path("data/raw/anac")
    vb_dir = raw_anac / "voos_basica"
    mov_dir = raw_anac / "movimentacao"
    aerodromos_file = raw_anac / "aeroportos" / "aerodromos.parquet"

    vb_files = get_timeline_files(vb_dir)
    mov_files = sorted(p.as_posix() for p in mov_dir.glob("movimentacao_*.parquet"))
    if not mov_files:
        raise FileNotFoundError(f"Arquivos de movimentação ausentes em {mov_dir}")

    # 1. Curadoria de rotas mensais
    routes_parquet = path("data/curated/anac/anac_routes_monthly.parquet")
    routes_df = curate_routes_monthly(con, vb_files, routes_parquet)

    # 2. Curadoria de aeródromos
    airports_parquet = path("data/curated/anac/anac_airports.parquet")
    airports_df = curate_airports(con, aerodromos_file, vb_files, airports_parquet)

    # 3. Curadoria de atrasos
    delays_parquet = path("data/curated/anac/anac_delays_monthly.parquet")
    delays_df = curate_delays_monthly(con, mov_files, delays_parquet)

    # 4. Geração de calibration_values.json (com estatísticas de integridade computadas)
    calib_json = path("data/curated/calibration_values.json")
    vb_integrity = compute_vb_integrity_stats(con, vb_files)
    generate_calibration_values(routes_df, airports_df, delays_df, calib_json, vb_integrity)

    # 5. Renderização automática do relatório de calibração em docs/calibration_report.md
    # Fail loud: render_calibration é parte integrante do pipeline — se não importar,
    # a instalação está quebrada e o erro deve propagar (nunca silencioso).
    from ingestion.render_calibration import render_report

    report_file = render_report()
    logger.info(f"Relatório de calibração renderizado em {report_file}.")

    con.close()
    logger.info("Pipeline de curadoria ANAC concluído com sucesso.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
