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
from typing import Any

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
    timeline_records: list[dict[str, Any]] = []

    # 1. Voos operados
    tx_sub = transactions_df[
        (transactions_df["transaction_date"] <= cutoff_date) & transactions_df["flight_id"].notna()
    ].copy()

    tx_flights = tx_sub.merge(
        flights_df[["flight_id", "origin_airport", "destination_airport", "departure_date", "delay_minutes", "has_delay"]],
        on="flight_id",
        how="inner",
    )

    for _, f in tx_flights.iterrows():
        dt_str = pd.to_datetime(f["departure_date"]).strftime("%Y-%m-%d")
        orig = f["origin_airport"]
        dest = f["destination_airport"]
        has_del = bool(f["has_delay"])
        del_min = int(f.get("delay_minutes", 0))

        if has_del and del_min > 0:
            detalhe = f"Trecho {orig} -> {dest} com atraso operacional de {del_min} min."
            impacto = "negativo"
        else:
            detalhe = f"Trecho {orig} -> {dest} operado pontualmente."
            impacto = "positivo"

        timeline_records.append(
            {
                "customer_id": str(f["customer_id"]),
                "data": dt_str,
                "tipo": "voo",
                "titulo": f"Voo {orig}-{dest}",
                "detalhe": detalhe,
                "impacto": impacto,
            }
        )

    # 2. Resgates de Pontos
    tx_resgates = transactions_df[
        (transactions_df["transaction_date"] <= cutoff_date)
        & (transactions_df["pontos_azul_resgatados"] > 0)
    ]

    for _, r in tx_resgates.iterrows():
        dt_str = pd.to_datetime(r["transaction_date"]).strftime("%Y-%m-%d")
        pts = int(r["pontos_azul_resgatados"])
        timeline_records.append(
            {
                "customer_id": str(r["customer_id"]),
                "data": dt_str,
                "tipo": "resgate",
                "titulo": "Resgate de Pontos Azul",
                "detalhe": f"Emissão com pontos: {pts:,} pts Azul resgatados.".replace(",", "."),
                "impacto": "neutro",
            }
        )

    # 3. Interações com Atrito
    inter_frictions = interactions_df[
        (interactions_df["interaction_date"] <= cutoff_date)
        & (interactions_df["has_friction"] == 1)
    ]

    for _, it in inter_frictions.iterrows():
        dt_str = pd.to_datetime(it["interaction_date"]).strftime("%Y-%m-%d")
        aspect = str(it["aspect"])
        channel = str(it["channel"])
        nps = it.get("nps_rating")
        nps_str = f" (NPS: {int(nps)})" if pd.notna(nps) else ""

        timeline_records.append(
            {
                "customer_id": str(it["customer_id"]),
                "data": dt_str,
                "tipo": "atrito",
                "titulo": f"Atrito registrado: {aspect.capitalize()}",
                "detalhe": f"Manifestação no canal {channel} referente a {aspect}{nps_str}.",
                "impacto": "negativo",
            }
        )

    # 4. Mudança de Categoria / Eventos de Fidelidade
    lo_events = loyalty_events_df[loyalty_events_df["event_date"] <= cutoff_date]

    for _, le in lo_events.iterrows():
        dt_str = pd.to_datetime(le["event_date"]).strftime("%Y-%m-%d")
        new_tier = str(le.get("new_tier", "azul")).replace("_", " ").title()
        prev_tier = str(le.get("previous_tier", "azul")).replace("_", " ").title()
        reason = str(le.get("trigger_reason", "qualificacao_periodica"))

        timeline_records.append(
            {
                "customer_id": str(le["customer_id"]),
                "data": dt_str,
                "tipo": "tier_change",
                "titulo": f"Qualificação Categoria {new_tier}",
                "detalhe": f"Transição de {prev_tier} para {new_tier} por {reason}.",
                "impacto": "positivo",
            }
        )

    out_df = pd.DataFrame(timeline_records)
    # Ordenação decrescente por data e customer_id
    out_df = out_df.sort_values(["customer_id", "data"], ascending=[True, False]).reset_index(drop=True)

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
