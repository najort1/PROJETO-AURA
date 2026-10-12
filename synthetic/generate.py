"""Orquestrador do gerador sintético calibrado do Projeto Aura 2.0 (WS2).

Gera uma população reproduzível de clientes, malha de voos, transações
financeiras/fidelidade, progressão de status, interações com atrito e
ground truth segregado (evaluation_only).

Uso:
    python -m synthetic.generate
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from aura_core.config import child_seed, load_yaml, program_rules, settings
from aura_core.log import get_logger
from aura_core.paths import ensure_dir, path
from schemas.load import load_contract, validate_or_raise
from synthetic.churn import compute_ground_truth
from synthetic.customers import generate_customers
from synthetic.flights import generate_flight_record, get_route_catalog
from synthetic.interactions import create_interaction_record, sample_nps_rating
from synthetic.loyalty import (
    create_loyalty_event,
    determine_tier_change_event,
    evaluate_tier,
    get_earn_multiplier,
    get_redemption_ceiling,
)
from synthetic.transactions import calculate_flight_fare, create_transaction_record

log = get_logger("synthetic.generate")


def _enforce_contract_types(df: pd.DataFrame, contract_name: str) -> pd.DataFrame:
    """Garante que as colunas possuam os dtypes exatamente declarados no contrato."""
    contract = load_contract(contract_name)
    df = df.copy()
    for col_info in contract.get("columns", []):
        col = col_info["name"]
        if col not in df.columns:
            continue
        declared = str(col_info.get("dtype", "")).lower()
        if declared in {"string", "str", "text"}:
            df[col] = df[col].astype("string")
        elif declared in {"int", "integer", "int64"}:
            df[col] = df[col].astype("int64")
        elif declared in {"float", "double", "float64"}:
            df[col] = df[col].astype("float64")
        elif declared in {"datetime", "date", "timestamp"}:
            df[col] = pd.to_datetime(df[col])
    return df


def load_calibration_values() -> dict[str, Any] | None:
    """Tenta carregar os valores de calibração produzidos por WS1 (ingestion.curate)."""
    calib_file = path("data/curated/calibration_values.json")
    if calib_file.exists():
        try:
            with open(calib_file, encoding="utf-8") as f:
                data = json.load(f)
            log.info("Valores de calibração carregados com sucesso de %s", calib_file)
            return data
        except Exception as e:
            log.warning("Falha ao decodificar calibration_values.json: %s", e)
    return None


def generate_synthetic_dataset(
    n_customers: int = 50000,
    seed: int = 42,
    output_dir: Path | str | None = None,
    ground_truth_path: Path | str | None = None,
    calibration_values: dict[str, Any] | None = None,
    validate: bool = True,
) -> dict[str, pd.DataFrame]:
    """Gera todo o ecossistema sintético determinístico e valida contratos de dados."""
    out_dir = ensure_dir(output_dir or path("data/curated/synthetic"))
    gt_file = path(ground_truth_path or "data/curated/ground_truth.parquet")

    gen_cfg = load_yaml("config/generator.yaml")
    rules_cfg = program_rules()
    routes = get_route_catalog(calibration_values)

    # Derivação determinística de seeds por componente
    comp_seed = child_seed(seed, "synthetic_generator")
    rng = np.random.default_rng(comp_seed)

    sim_start = dt.date(2023, 9, 1)
    sim_end = dt.date(2026, 8, 31)
    target_start = pd.Timestamp("2025-09-01")
    target_end = pd.Timestamp("2026-08-31 23:59:59")

    # Sazonalidade diária calibrada com índices ANAC
    season_weights = {
        1: 1.036,
        2: 0.894,
        3: 0.988,
        4: 0.96,
        5: 0.983,
        6: 0.979,
        7: 1.077,
        8: 1.058,
        9: 0.983,
        10: 1.018,
        11: 0.996,
        12: 1.029,
    }
    if calibration_values and "market.seasonality_by_route" in calibration_values:
        calib_s = calibration_values["market.seasonality_by_route"].get("market_monthly_index", {})
        if calib_s:
            season_weights.update({int(k): float(v) for k, v in calib_s.items()})

    sim_days = (sim_end - sim_start).days + 1
    all_dates = [sim_start + dt.timedelta(days=i) for i in range(sim_days)]
    date_weights = np.array([season_weights[d.month] for d in all_dates], dtype=float)

    log.info("Iniciando geração sintética: N=%d, seed=%d", n_customers, comp_seed)

    # 1. Clientes
    customers_df = generate_customers(n_customers, rng, gen_cfg, sim_start)
    log.info("População de clientes gerada: %d registros", len(customers_df))

    # Prepara estruturas acumuladoras
    flights_records: list[dict[str, Any]] = []
    tx_records: list[dict[str, Any]] = []
    events_records: list[dict[str, Any]] = []
    interactions_records: list[dict[str, Any]] = []

    flight_seq = 1
    tx_seq = 1
    event_seq = 1
    int_seq = 1

    archetypes_cfg = gen_cfg.get("archetypes", {})
    mar_cfg = gen_cfg.get("latent", {}).get("missing_data", {}).get("nps_mar_mechanism", {})

    # Rotas indexadas por origem para escolha rápida
    routes_by_orig: dict[str, list[dict[str, Any]]] = {}
    for r in routes:
        routes_by_orig.setdefault(r["orig"], []).append(r)

    # 2. Simulação temporal por cliente
    customer_tiers: dict[str, str] = {}

    for c_row in customers_df.itertuples():
        cid = str(c_row.customer_id)
        arch = str(c_row.archetype)
        home_ap = str(c_row.home_airport)
        c_join_dt = pd.to_datetime(c_row.join_date).to_pydatetime()

        current_tier = "azul"
        customer_tiers[cid] = current_tier

        # Histórico de qualificação do cliente: (data, qp, is_segment, spend)
        qual_history: list[tuple[dt.datetime, int, int, float]] = []

        arch_info = archetypes_cfg.get(arch, {})
        adv_mean = float(arch_info.get("advance_days_mean", 20.0))
        ancillary_prop = float(arch_info.get("ancillary_propensity", 0.30))
        redemption_prop = float(arch_info.get("redemption_propensity", 0.25))

        theta_freq = float(c_row.latent_freq_effect)
        theta_spend = float(c_row.latent_spend_effect)

        # Dormência realista: parcela de contas cadastradas historicamente inativas no triênio
        is_dormant = (
            (arch == "eventual_promocional" and rng.random() < 0.58)
            or (arch == "lazer_premium" and rng.random() < 0.32)
            or (arch == "regional_dependente" and rng.random() < 0.25)
            or (arch == "maximizador_milhas" and rng.random() < 0.25)
            or (arch == "executivo_recorrente" and rng.random() < 0.08)
        )

        valid_sim_start = max(sim_start, c_join_dt.date())
        start_day_offset = (valid_sim_start - sim_start).days

        if is_dormant:
            total_flights_est = 0
            flight_dates_sampled = []
        else:
            if arch == "executivo_recorrente":
                exec_is_super = rng.random() < 0.20
                active_trips_mean = 9.5 if exec_is_super else 3.8
            elif arch == "regional_dependente":
                active_trips_mean = 2.0
            elif arch == "maximizador_milhas":
                active_trips_mean = 1.4
            elif arch == "lazer_premium":
                active_trips_mean = 1.3
            else:
                active_trips_mean = 0.7

            adj_lambda = max(0.1, active_trips_mean * np.exp(theta_freq * 0.35))
            total_flights_est = int(rng.poisson(adj_lambda * 3.0))
            if total_flights_est > 0:
                cust_date_weights = date_weights[start_day_offset:]
                cust_date_probs = cust_date_weights / cust_date_weights.sum()
                sampled_offsets = rng.choice(
                    len(cust_date_weights), size=total_flights_est, p=cust_date_probs
                )
                sampled_offsets.sort()
                flight_dates_sampled = [
                    all_dates[start_day_offset + int(o)] for o in sampled_offsets
                ]
            else:
                flight_dates_sampled = []

        # Assinatura de Clube Azul / Cartão Itaú restrita a uma fatia de membros ativos
        has_club_card = (arch == "maximizador_milhas" and rng.random() < 0.20) or (
            arch == "executivo_recorrente" and rng.random() < 0.10
        )
        if has_club_card and not is_dormant:
            n_partner_events = rng.integers(2, 6)
            avail_days = (sim_end - valid_sim_start).days
            if avail_days > 30:
                partner_offsets = np.sort(rng.integers(0, avail_days, size=n_partner_events))
                for p_off in partner_offsets:
                    p_date = dt.datetime.combine(
                        valid_sim_start + dt.timedelta(days=int(p_off)),
                        dt.time(12, int(rng.integers(0, 59)), 0),
                    )
                    pts_card = int(rng.choice([1000, 2500, 5000]))
                    qp_card = int(pts_card // 10)
                    tx_records.append(
                        create_transaction_record(
                            tx_seq,
                            cid,
                            p_date,
                            "acumulo_cartao" if rng.random() > 0.4 else "acumulo_clube",
                            0.0,
                            pts_card,
                            qp_card,
                            0,
                            None,
                            None,
                        )
                    )
                    tx_seq += 1
                    qual_history.append((p_date, qp_card, 0, 0.0))

        # Iteração sobre cada viagem aérea
        for dep_date_d in flight_dates_sampled:
            dep_dt = dt.datetime.combine(
                dep_date_d, dt.time(int(rng.integers(6, 22)), int(rng.integers(0, 59)), 0)
            )

            # Rota: prioriza hub do cliente
            avail_routes = routes_by_orig.get(home_ap, routes)
            route = rng.choice(avail_routes)

            # Voos
            is_winter = dep_date_d.month in {6, 7, 8}
            fl_rec = generate_flight_record(flight_seq, route, dep_dt, rng, is_winter)
            flights_records.append(fl_rec)
            fid = fl_rec["flight_id"]
            flight_seq += 1

            # Antecedência de compra
            adv_days = max(1.0, rng.normal(adv_mean, adv_mean * 0.3))
            purchase_dt = dep_dt - dt.timedelta(days=int(adv_days))
            if purchase_dt < dt.datetime.combine(valid_sim_start, dt.time(0, 0)):
                purchase_dt = dt.datetime.combine(valid_sim_start, dt.time(0, 0))

            # Resgate ou compra
            is_redemption = rng.random() < redemption_prop
            if is_redemption:
                # Transação de resgate
                ceiling = get_redemption_ceiling(current_tier)
                pts_redeemed = int(rng.integers(3000, min(ceiling, 35000)))
                boarding_fee = float(round(rng.uniform(35.0, 55.0), 2))

                tx_records.append(
                    create_transaction_record(
                        tx_seq,
                        cid,
                        purchase_dt,
                        "resgate_passagem",
                        boarding_fee,
                        0,
                        0,
                        pts_redeemed,
                        None,
                        fid,
                    )
                )
                tx_seq += 1
            else:
                # Compra de passagem
                fare = calculate_flight_fare(
                    fl_rec["distance_km"],
                    adv_days,
                    dep_date_d.month,
                    theta_spend,
                    gen_cfg,
                    rng,
                )
                multiplier = get_earn_multiplier(current_tier)
                pts_earned = int(fare * multiplier)
                qp_earned = int(fare)  # R$ 1 = 1 QP

                tx_records.append(
                    create_transaction_record(
                        tx_seq,
                        cid,
                        purchase_dt,
                        "compra_passagem",
                        fare,
                        pts_earned,
                        qp_earned,
                        0,
                        None,
                        fid,
                    )
                )
                tx_seq += 1
                qual_history.append((purchase_dt, qp_earned, 1, fare))

                # Compra de ancillaries
                if rng.random() < ancillary_prop:
                    anc_choice = rng.choice(
                        ["bagagem", "espaco_azul", "marcacao_assento", "antecipacao_voo"],
                        p=[0.50, 0.28, 0.14, 0.08],
                    )
                    anc_price = {
                        "bagagem": 110.0,
                        "espaco_azul": 65.0,
                        "marcacao_assento": 35.0,
                        "antecipacao_voo": 75.0,
                    }[anc_choice]
                    anc_pts = int(anc_price * multiplier)
                    anc_qp = int(anc_price)

                    tx_records.append(
                        create_transaction_record(
                            tx_seq,
                            cid,
                            purchase_dt + dt.timedelta(minutes=5),
                            "servico_ancillary",
                            anc_price,
                            anc_pts,
                            anc_qp,
                            0,
                            anc_choice,
                            fid,
                        )
                    )
                    tx_seq += 1
                    qual_history.append(
                        (purchase_dt + dt.timedelta(minutes=5), anc_qp, 0, anc_price)
                    )

            # Data de avaliação: purchase_dt + 5min se houver ancillary, senão purchase_dt
            eval_dt = purchase_dt
            if rng.random() < ancillary_prop:
                eval_dt = purchase_dt + dt.timedelta(minutes=5)

            # Avaliação de tier em janela móvel de 365 dias (sem vazamento temporal: teto = eval_dt)
            cutoff_365 = eval_dt - dt.timedelta(days=365)
            recent_act = [h for h in qual_history if cutoff_365 <= h[0] <= eval_dt]
            qp_rolling = sum(h[1] for h in recent_act)
            segs_rolling = sum(h[2] for h in recent_act)
            spend_rolling = sum(h[3] for h in recent_act)

            new_tier = evaluate_tier(qp_rolling, segs_rolling, spend_rolling, rules_cfg)
            if new_tier != current_tier:
                event_type, trigger = determine_tier_change_event(
                    previous_tier=current_tier,
                    new_tier=new_tier,
                    qualifying_points=qp_rolling,
                    segments=segs_rolling,
                    spend_brl=spend_rolling,
                )
                events_records.append(
                    create_loyalty_event(
                        event_seq,
                        cid,
                        eval_dt,
                        event_type,
                        current_tier,
                        new_tier,
                        trigger,
                        qp_rolling,
                        segs_rolling,
                        spend_rolling,
                    )
                )
                event_seq += 1
                current_tier = new_tier

            # Geração de interações e atritos
            # 1. Atrito decorrente do voo (atraso severo ou cancelamento)
            if fl_rec["has_delay"] or fl_rec["is_cancelled"]:
                aspect = "atraso" if fl_rec["has_delay"] else "atendimento"
                intensity = (
                    min(1.0, fl_rec["delay_minutes"] / 120.0) if fl_rec["has_delay"] else 0.95
                )
                nps = sample_nps_rating(
                    1, intensity, current_tier in {"diamante", "diamante_unique"}, rng, mar_cfg
                )
                status_res = rng.choice(
                    ["resolvido", "nao_resolvido", "pendente"], p=[0.60, 0.28, 0.12]
                )

                interactions_records.append(
                    create_interaction_record(
                        int_seq,
                        cid,
                        fl_rec["actual_departure"] + dt.timedelta(hours=int(rng.integers(1, 12))),
                        rng.choice(["aeroporto", "app", "call_center", "whatsapp"]),
                        aspect,
                        1,
                        intensity,
                        nps,
                        status_res,
                    )
                )
                int_seq += 1
            elif rng.random() < 0.08:
                # Atrito eventual de bagagem ou app
                aspect = rng.choice(["bagagem", "app_checkin", "resgate_milhas", "preco"])
                intensity = float(round(rng.uniform(0.35, 0.85), 2))
                nps = sample_nps_rating(1, intensity, False, rng, mar_cfg)
                interactions_records.append(
                    create_interaction_record(
                        int_seq,
                        cid,
                        dep_dt + dt.timedelta(hours=2),
                        "app" if aspect == "app_checkin" else "aeroporto",
                        aspect,
                        1,
                        intensity,
                        nps,
                        "resolvido" if rng.random() > 0.3 else "nao_resolvido",
                    )
                )
                int_seq += 1
            elif rng.random() < 0.15:
                # Interação rotineira sem atrito
                nps = sample_nps_rating(
                    0, 0.0, current_tier in {"diamante", "diamante_unique"}, rng, mar_cfg
                )
                interactions_records.append(
                    create_interaction_record(
                        int_seq,
                        cid,
                        dep_dt - dt.timedelta(hours=3),
                        rng.choice(["app", "web", "whatsapp"]),
                        "nenhum",
                        0,
                        0.0,
                        nps,
                        "resolvido",
                    )
                )
                int_seq += 1

        # Avaliação final de tier do cliente no encerramento da simulação.
        # Data de expiração = min(sim_end, última_atividade + 365d)
        if qual_history:
            last_act_dt = max(h[0] for h in qual_history)
            exp_date = min(dt.datetime.combine(sim_end, dt.time(23, 59, 59)), last_act_dt + dt.timedelta(days=365))
        else:
            # Cliente sem nenhuma atividade: tier base (azul) mantido
            exp_date = dt.datetime.combine(sim_end, dt.time(23, 59, 59))

        cutoff_final = exp_date - dt.timedelta(days=365)
        final_act = [h for h in qual_history if cutoff_final <= h[0] <= exp_date]
        final_qp = sum(h[1] for h in final_act)
        final_segs = sum(h[2] for h in final_act)
        final_spend = sum(h[3] for h in final_act)
        final_tier = evaluate_tier(final_qp, final_segs, final_spend, rules_cfg)

        # Emitir evento de downgrade se tier final for inferior ao último registrado
        if final_tier != current_tier:
            event_type, trigger = determine_tier_change_event(
                previous_tier=current_tier,
                new_tier=final_tier,
                qualifying_points=final_qp,
                segments=final_segs,
                spend_brl=final_spend,
            )
            events_records.append(
                create_loyalty_event(
                    event_seq,
                    cid,
                    exp_date,
                    event_type,
                    current_tier,
                    final_tier,
                    trigger,
                    final_qp,
                    final_segs,
                    final_spend,
                )
            )
            event_seq += 1
            current_tier = final_tier

        customer_tiers[cid] = final_tier

    # Atualiza current_tier na tabela de customers
    customers_df["current_tier"] = [
        customer_tiers.get(cid, "azul") for cid in customers_df["customer_id"]
    ]

    flights_df = pd.DataFrame(flights_records)
    transactions_df = pd.DataFrame(tx_records)
    loyalty_events_df = pd.DataFrame(events_records)
    interactions_df = pd.DataFrame(interactions_records)

    # Garantir consistência relacional: replay dos eventos deve reconstruir o tier final
    # Para cada cliente, se o último evento (por data) não bater com customer_tiers, emitir evento de correção
    if len(loyalty_events_df) > 0:
        # Último evento por cliente (por event_date, event_id)
        last_events = loyalty_events_df.sort_values(["event_date", "event_id"]).groupby("customer_id").last().reset_index()
        replay_tiers = dict(zip(last_events["customer_id"], last_events["new_tier"], strict=False))

        corrections = 0
        for cid, final_tier in customer_tiers.items():
            replay_tier = replay_tiers.get(cid, "azul")
            if replay_tier != final_tier:
                # Emitir evento de correção na data de expiração da simulação
                exp_date = dt.datetime.combine(sim_end, dt.time(23, 59, 59))
                event_type, trigger = determine_tier_change_event(
                    previous_tier=replay_tier,
                    new_tier=final_tier,
                    qualifying_points=0,  # placeholder, não usado para trigger de correção
                    segments=0,
                    spend_brl=0.0,
                )
                # Forçar trigger de expiração para correções de consistência
                if event_type == "tier_downgrade":
                    trigger = "qualification_cycle_expired"
                events_records.append(
                    create_loyalty_event(
                        event_seq,
                        cid,
                        exp_date,
                        event_type,
                        replay_tier,
                        final_tier,
                        trigger,
                        0, 0, 0.0,
                    )
                )
                event_seq += 1
                corrections += 1

        if corrections > 0:
            log.info("Emitidos %d eventos de correção para consistência relacional", corrections)
            # Reconstruir DataFrame com os eventos de correção
            loyalty_events_df = pd.DataFrame(events_records)

    # 3. Ground Truth e Churn
    ground_truth_df, final_customers_df = compute_ground_truth(
        customers_df,
        transactions_df,
        interactions_df,
        gen_cfg,
        target_start,
        target_end,
        rng,
    )

    # Tipagem estrita conforme contratos
    final_customers_df = _enforce_contract_types(final_customers_df, "synthetic_customers")
    flights_df = _enforce_contract_types(flights_df, "synthetic_flights")
    transactions_df = _enforce_contract_types(transactions_df, "synthetic_transactions")
    loyalty_events_df = _enforce_contract_types(loyalty_events_df, "synthetic_loyalty_events")
    interactions_df = _enforce_contract_types(interactions_df, "synthetic_interactions")
    ground_truth_df = _enforce_contract_types(ground_truth_df, "ground_truth")

    log.info(
        "Tabelas consolidadas: customers=%d, flights=%d, tx=%d, events=%d, interactions=%d, ground_truth=%d",
        len(final_customers_df),
        len(flights_df),
        len(transactions_df),
        len(loyalty_events_df),
        len(interactions_df),
        len(ground_truth_df),
    )

    # Ordenação canônica temporal global antes de gravar (MENOR 1)
    # Transactions: transaction_date, customer_id
    transactions_df = transactions_df.sort_values(["transaction_date", "customer_id"]).reset_index(drop=True)
    # Flights: scheduled_departure, flight_id
    flights_df = flights_df.sort_values(["scheduled_departure", "flight_id"]).reset_index(drop=True)
    # Interactions: interaction_date, interaction_id
    interactions_df = interactions_df.sort_values(["interaction_date", "interaction_id"]).reset_index(drop=True)
    # Loyalty events: event_date, event_id
    loyalty_events_df = loyalty_events_df.sort_values(["event_date", "event_id"]).reset_index(drop=True)

    # 4. Gravação dos Parquets
    final_customers_df.to_parquet(out_dir / "customers.parquet", index=False)
    flights_df.to_parquet(out_dir / "flights.parquet", index=False)
    transactions_df.to_parquet(out_dir / "transactions.parquet", index=False)
    loyalty_events_df.to_parquet(out_dir / "loyalty_events.parquet", index=False)
    interactions_df.to_parquet(out_dir / "interactions.parquet", index=False)
    ground_truth_df.to_parquet(gt_file, index=False)

    # 5. Validação com contratos YAML
    if validate:
        log.info("Validando contratos de dados...")
        validate_or_raise(load_contract("synthetic_customers"), out_dir / "customers.parquet")
        validate_or_raise(load_contract("synthetic_flights"), out_dir / "flights.parquet")
        validate_or_raise(load_contract("synthetic_transactions"), out_dir / "transactions.parquet")
        validate_or_raise(
            load_contract("synthetic_loyalty_events"), out_dir / "loyalty_events.parquet"
        )
        validate_or_raise(load_contract("synthetic_interactions"), out_dir / "interactions.parquet")
        validate_or_raise(load_contract("ground_truth"), gt_file)
        log.info("Todos os 6 contratos foram validados com sucesso (0 violações).")

    return {
        "customers": final_customers_df,
        "flights": flights_df,
        "transactions": transactions_df,
        "loyalty_events": loyalty_events_df,
        "interactions": interactions_df,
        "ground_truth": ground_truth_df,
    }


def main() -> int:
    """Ponto de entrada para python -m synthetic.generate."""
    calib_values = load_calibration_values()
    if calib_values is None:
        log.warning(
            "data/curated/calibration_values.json não encontrado. Geração em escala completa aguarda ingestão WS1."
        )
        print(
            "AVISO: data/curated/calibration_values.json não existe no momento. Executando em modo de validação com parâmetros de referência."
        )

    st_cfg = settings()
    n_cust = int(st_cfg.get("cohorts", {}).get("n_customers", 50000))
    seed = int(st_cfg.get("seed", 42))

    generate_synthetic_dataset(
        n_customers=n_cust,
        seed=seed,
        calibration_values=calib_values,
        validate=True,
    )

    success_file = path("data/curated/synthetic/_SUCCESS")
    with open(success_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": dt.datetime.now(dt.UTC).isoformat(),
                "seed": seed,
                "n_customers": n_cust,
                "status": "ready",
            },
            f,
            indent=2,
        )
    log.info("Marcador gravado em %s", success_file)
    return 0


if __name__ == "__main__":
    sys.exit(main())
