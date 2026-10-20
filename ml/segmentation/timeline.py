"""Construção da Linha do Tempo de Relacionamento (customer_timeline) para a tela 03 (WS5).

Regras de negócio:
- Concatena eventos de voos, transações de resgate, interações com atrito e mudanças de tier.
- Anti-vazamento temporal rigoroso: apenas eventos estritamente <= cutoff (2025-08-31).
- Estrutura de colunas exatamente idêntica à consumida pelo app:
  ['customer_id', 'data', 'tipo', 'titulo', 'detalhe', 'impacto']
- Ordenação decrescente por data para apresentação cronológica inversa.
- Persistência em data/analytics/customer_timeline.parquet e validação contra contrato.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from aura_core.paths import ROOT
from schemas.load import load_contract, validate_or_raise

FEATURE_CUTOFF = "2025-08-31 23:59:59"


def build_customer_timeline(
    transactions_df: pd.DataFrame,
    flights_df: pd.DataFrame,
    interactions_df: pd.DataFrame,
    loyalty_events_df: pd.DataFrame,
    cutoff_date: str = FEATURE_CUTOFF,
) -> pd.DataFrame:
    """Consolida os eventos históricos do cliente em uma linha do tempo unificada."""
    parts: list[pd.DataFrame] = []

    # 1. Voos operados
    tx_sub = transactions_df[
        (transactions_df["transaction_date"] <= cutoff_date) & transactions_df["flight_id"].notna()
    ].copy()

    tx_flights = tx_sub.merge(
        flights_df[
            [
                "flight_id",
                "origin_airport",
                "destination_airport",
                "departure_date",
                "delay_minutes",
                "has_delay",
            ]
        ],
        on="flight_id",
        how="inner",
    )
    # Anti-vazamento temporal (revisor WS5-B, achado B4-01): a PARTIDA também deve
    # ser <= cutoff. Voos pré-comprados com partida futura não podem exibir
    # resultado operacional (atraso) que não seria conhecido no snapshot.
    tx_flights = tx_flights[
        pd.to_datetime(tx_flights["departure_date"]) <= pd.Timestamp(cutoff_date)
    ]

    if not tx_flights.empty:
        dt_str = pd.to_datetime(tx_flights["departure_date"]).dt.strftime("%Y-%m-%d")
        orig = tx_flights["origin_airport"].astype(str)
        dest = tx_flights["destination_airport"].astype(str)
        # Divergência deliberada vs implementação original (iterrows): com
        # has_delay NaN (merge left sem match), a original falhava alto em
        # int(nan); a vetorizada trata NaN como sem atraso (False→operado
        # pontualmente). Estados intermediários não existem nos dados atuais
        # (verificado); a decisão documenta a semântica para futuros merge misses.
        has_del = tx_flights["has_delay"].fillna(False).astype(bool)
        del_min = tx_flights["delay_minutes"].fillna(0).astype(int)

        is_delayed = has_del & (del_min > 0)
        detalhe = np.where(
            is_delayed,
            "Trecho " + orig + " -> " + dest + " com atraso operacional de " + del_min.astype(str) + " min.",
            "Trecho " + orig + " -> " + dest + " operado pontualmente.",
        )
        impacto = np.where(is_delayed, "negativo", "positivo")
        titulo = "Voo " + orig + "-" + dest

        parts.append(
            pd.DataFrame(
                {
                    "customer_id": tx_flights["customer_id"].astype(str),
                    "data": dt_str,
                    "tipo": "voo",
                    "titulo": titulo,
                    "detalhe": detalhe,
                    "impacto": impacto,
                }
            )
        )

    # 2. Resgates de Pontos
    tx_resgates = transactions_df[
        (transactions_df["transaction_date"] <= cutoff_date)
        & (transactions_df["pontos_azul_resgatados"] > 0)
    ]

    if not tx_resgates.empty:
        dt_str = pd.to_datetime(tx_resgates["transaction_date"]).dt.strftime("%Y-%m-%d")
        pts_list = [
            f"Emissão com pontos: {int(p):,} pts Azul resgatados.".replace(",", ".")
            for p in tx_resgates["pontos_azul_resgatados"]
        ]
        parts.append(
            pd.DataFrame(
                {
                    "customer_id": tx_resgates["customer_id"].astype(str),
                    "data": dt_str,
                    "tipo": "resgate",
                    "titulo": "Resgate de Pontos Azul",
                    "detalhe": pts_list,
                    "impacto": "neutro",
                }
            )
        )

    # 3. Interações com Atrito
    inter_frictions = interactions_df[
        (interactions_df["interaction_date"] <= cutoff_date)
        & (interactions_df["has_friction"] == 1)
    ]

    if not inter_frictions.empty:
        dt_str = pd.to_datetime(inter_frictions["interaction_date"]).dt.strftime("%Y-%m-%d")
        aspect = inter_frictions["aspect"].astype(str)
        channel = inter_frictions["channel"].astype(str)
        if "nps_rating" in inter_frictions.columns:
            nps = inter_frictions["nps_rating"]
            nps_notna = nps.notna()
            nps_str = np.where(
                nps_notna,
                " (NPS: " + nps.fillna(0).astype(int).astype(str) + ")",
                "",
            )
        else:
            nps_str = ""

        titulo = "Atrito registrado: " + aspect.str.capitalize()
        detalhe = "Manifestação no canal " + channel + " referente a " + aspect + nps_str + "."

        parts.append(
            pd.DataFrame(
                {
                    "customer_id": inter_frictions["customer_id"].astype(str),
                    "data": dt_str,
                    "tipo": "atrito",
                    "titulo": titulo,
                    "detalhe": detalhe,
                    "impacto": "negativo",
                }
            )
        )

    # 4. Mudança de Categoria / Eventos de Fidelidade
    lo_events = loyalty_events_df[loyalty_events_df["event_date"] <= cutoff_date]

    if not lo_events.empty:
        dt_str = pd.to_datetime(lo_events["event_date"]).dt.strftime("%Y-%m-%d")
        new_tier_s = (
            lo_events["new_tier"].fillna("azul").astype(str)
            if "new_tier" in lo_events.columns
            else pd.Series("azul", index=lo_events.index)
        )
        prev_tier_s = (
            lo_events["previous_tier"].fillna("azul").astype(str)
            if "previous_tier" in lo_events.columns
            else pd.Series("azul", index=lo_events.index)
        )
        reason_s = (
            lo_events["trigger_reason"].fillna("qualificacao_periodica").astype(str)
            if "trigger_reason" in lo_events.columns
            else pd.Series("qualificacao_periodica", index=lo_events.index)
        )

        new_tier = new_tier_s.str.replace("_", " ", regex=False).str.title()
        prev_tier = prev_tier_s.str.replace("_", " ", regex=False).str.title()

        titulo = "Qualificação Categoria " + new_tier
        detalhe = "Transição de " + prev_tier + " para " + new_tier + " por " + reason_s + "."

        parts.append(
            pd.DataFrame(
                {
                    "customer_id": lo_events["customer_id"].astype(str),
                    "data": dt_str,
                    "tipo": "tier_change",
                    "titulo": titulo,
                    "detalhe": detalhe,
                    "impacto": "positivo",
                }
            )
        )

    if parts:
        out_df = pd.concat(parts, ignore_index=True)
    else:
        out_df = pd.DataFrame(
            columns=["customer_id", "data", "tipo", "titulo", "detalhe", "impacto"]
        )
    # Guarda fail-loud: nenhum evento posterior ao cutoff pode existir na timeline.
    if not out_df.empty:
        max_data = pd.to_datetime(out_df["data"]).max()
        if max_data > pd.Timestamp(cutoff_date):
            raise ValueError(
                f"Vazamento temporal na timeline: max(data)={max_data.date()} > cutoff {cutoff_date}"
            )
    # Ordenação decrescente por data e customer_id
    out_df = out_df.sort_values(["customer_id", "data"], ascending=[True, False]).reset_index(
        drop=True
    )

    # Garante tipagem de strings pura
    for c in ["customer_id", "data", "tipo", "titulo", "detalhe", "impacto"]:
        out_df[c] = out_df[c].astype(str)

    return out_df


def run_timeline_pipeline(
    output_dir: Path | None = None,
) -> pd.DataFrame:
    """Executa o pipeline de geração da linha do tempo e grava customer_timeline.parquet."""
    curated_dir = ROOT / "data" / "curated" / "synthetic"
    data_dir = ROOT / "data" / "analytics"
    out_dir = output_dir or data_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    tx_df = pd.read_parquet(curated_dir / "transactions.parquet")
    fl_df = pd.read_parquet(curated_dir / "flights.parquet")
    it_df = pd.read_parquet(curated_dir / "interactions.parquet")
    lo_df = pd.read_parquet(curated_dir / "loyalty_events.parquet")

    timeline_df = build_customer_timeline(tx_df, fl_df, it_df, lo_df)

    out_file = out_dir / "customer_timeline.parquet"
    timeline_df.to_parquet(out_file, index=False)
    validate_or_raise(load_contract("customer_timeline"), out_file)

    print(f"Customer timeline gerada com sucesso: {len(timeline_df)} eventos salvos em {out_file}")
    return timeline_df


if __name__ == "__main__":
    run_timeline_pipeline()
