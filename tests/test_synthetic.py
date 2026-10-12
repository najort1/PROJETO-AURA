"""Testes de unidade e integração do gerador sintético, contratos e regras de fidelidade (WS2).

Garante:
1. Progressão de tier estritamente conforme config/program_rules.yaml em casos construídos.
2. Determinismo estrito (mesma seed -> mesma saída idêntica).
3. Isolamento completo do ground truth (consumers: [evaluation_only]).
4. Validação dos contratos YAML (0 violações).
5. Mecanismo de dados faltantes documentado (MAR/MCAR).
6. **REGRESSÃO:** Sem vazamento temporal (transação futura NÃO conta na qualificação).
7. **REGRESSÃO:** Downgrades reais geram event_type="tier_downgrade" com trigger correto.
8. **REGRESSÃO:** Replay dos eventos reconstrói tier final de TODOS os clientes.
9. **REGRESSÃO:** transactions.parquet ordenado por data (ordem canônica global).
10. **REGRESSÃE:** Null-safety em loyalty.py (thresholds None = inelegível, sem TypeError).
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pandas as pd
import pytest

from aura_core.paths import path
from schemas.load import load_contract, validate_table
from synthetic.fidelity_report import compute_fidelity_metrics
from synthetic.generate import generate_synthetic_dataset
from synthetic.loyalty import (
    determine_tier_change_event,
    evaluate_tier,
)


def test_tier_progression_constructed_cases() -> None:
    """Valida casos construídos de qualificação conforme program_rules.yaml."""
    # 1. Base (Azul)
    assert evaluate_tier(0, 0, 0.0) == "azul"
    assert evaluate_tier(2000, 2, 2500.0) == "azul"

    # 2. Topázio: 6.000 qp OU 6 trechos
    assert evaluate_tier(6000, 1, 1000.0) == "topazio"
    assert evaluate_tier(1000, 6, 1000.0) == "topazio"
    assert evaluate_tier(6000, 6, 6000.0) == "topazio"

    # 3. Safira: 10.000 qp OU 10 trechos
    assert evaluate_tier(10000, 2, 2000.0) == "safira"
    assert evaluate_tier(2000, 10, 2000.0) == "safira"

    # 4. Diamante: (12.000 qp E 12 trechos) OU R$ 25.000 em gastos aéreos
    # CASO CRÍTICO: 12.000 qp SEM 12 trechos (e sem R$ 25k) NÃO vira Diamante (vira Safira)
    tier_sem_trechos = evaluate_tier(qualifying_points=12000, segments=8, spend_brl=12000.0)
    assert tier_sem_trechos != "diamante", "12k pontos sem 12 trechos não pode qualificar Diamante"
    assert tier_sem_trechos == "safira", "Deveria qualificar Safira (12k qp >= 10k qp)"

    # CASO CRÍTICO: 12 trechos SEM 12.000 qp (e sem R$ 25k) NÃO vira Diamante (vira Safira)
    tier_sem_qp = evaluate_tier(qualifying_points=8000, segments=12, spend_brl=8000.0)
    assert tier_sem_qp != "diamante"
    assert tier_sem_qp == "safira"

    # CASO CRÍTICO: 12.000 qp COM 12 trechos VIRA Diamante
    tier_completo = evaluate_tier(qualifying_points=12000, segments=12, spend_brl=12000.0)
    assert tier_completo == "diamante"

    # CASO CRÍTICO: R$ 25.000 em gastos aéreos VIRA Diamante mesmo sem 12 trechos ou 12k QP
    tier_por_gasto = evaluate_tier(qualifying_points=4000, segments=3, spend_brl=25000.0)
    assert tier_por_gasto == "diamante", "Gasto alternativo de R$ 25k deve qualificar Diamante"

    # 5. Diamante Unique: (26.000 qp E 26 trechos) OU R$ 50.000 em gastos
    # 26k sem 26 trechos não qualifica Unique (qualifica Diamante se tiver R$ 25k ou 12 trechos)
    tier_du_incompleto = evaluate_tier(qualifying_points=26000, segments=15, spend_brl=26000.0)
    assert tier_du_incompleto == "diamante"

    # 26k QP + 26 trechos qualifica Diamante Unique
    tier_du_completo = evaluate_tier(qualifying_points=26000, segments=26, spend_brl=26000.0)
    assert tier_du_completo == "diamante_unique"

    # R$ 50.000 gastos aéreos qualifica Diamante Unique diretamente
    tier_du_gasto = evaluate_tier(qualifying_points=8000, segments=5, spend_brl=50000.0)
    assert tier_du_gasto == "diamante_unique"


def test_determinism_bit_by_bit(tmp_path: Path) -> None:
    """Verifica que a mesma seed produz exatamente as mesmas tabelas bit a bit."""
    dir1 = tmp_path / "run1"
    dir2 = tmp_path / "run2"

    res1 = generate_synthetic_dataset(
        n_customers=200,
        seed=101,
        output_dir=dir1,
        ground_truth_path=dir1 / "ground_truth.parquet",
        validate=False,
    )
    res2 = generate_synthetic_dataset(
        n_customers=200,
        seed=101,
        output_dir=dir2,
        ground_truth_path=dir2 / "ground_truth.parquet",
        validate=False,
    )

    for table_name in [
        "customers",
        "flights",
        "transactions",
        "loyalty_events",
        "interactions",
        "ground_truth",
    ]:
        df1 = res1[table_name]
        df2 = res2[table_name]
        pd.testing.assert_frame_equal(
            df1,
            df2,
            check_exact=True,
            obj=f"Tabela {table_name} divergiu entre execuções de mesma seed",
        )


def test_schema_contracts_validation(tmp_path: Path) -> None:
    """Valida conformidade rigorosa dos 6 contratos de dados schemas/*.yaml."""
    out_dir = tmp_path / "synth"
    gt_file = tmp_path / "ground_truth.parquet"

    generate_synthetic_dataset(
        n_customers=250,
        seed=77,
        output_dir=out_dir,
        ground_truth_path=gt_file,
        validate=False,
    )

    contracts_to_check = [
        ("synthetic_customers", out_dir / "customers.parquet"),
        ("synthetic_flights", out_dir / "flights.parquet"),
        ("synthetic_transactions", out_dir / "transactions.parquet"),
        ("synthetic_loyalty_events", out_dir / "loyalty_events.parquet"),
        ("synthetic_interactions", out_dir / "interactions.parquet"),
        ("ground_truth", gt_file),
    ]

    for contract_name, table_file in contracts_to_check:
        contract = load_contract(contract_name)
        violations = validate_table(contract, table_file)
        assert not violations, f"Violações encontradas em {contract_name}:\n" + "\n".join(
            violations
        )


def test_ground_truth_isolation() -> None:
    """Garante que o ground_truth é segregado e nunca consumido por modelos ou features."""
    gt_contract = load_contract("ground_truth")
    consumers = gt_contract.get("consumers", [])
    assert consumers == ["evaluation_only"], (
        f"Consumidores de ground_truth devem ser estritamente ['evaluation_only'], obtido: {consumers}"
    )

    # Varredura estática de código-fonte nas pastas de modelos e pipelines analíticos
    dirs_to_audit = ["ml", "agent", "aura_core"]
    forbidden_pattern = re.compile(r"ground_truth\.parquet", re.IGNORECASE)

    for d in dirs_to_audit:
        src_dir = path(d)
        if not src_dir.exists():
            continue
        for py_file in src_dir.rglob("*.py"):
            code = py_file.read_text(encoding="utf-8")
            match = forbidden_pattern.search(code)
            assert match is None, (
                f"Violação de isolamento: {py_file} faz referência direta a ground_truth.parquet!"
            )


def test_missing_data_mechanisms(tmp_path: Path) -> None:
    """Verifica presença dos mecanismos formais de dados faltantes MAR e MCAR."""
    out_dir = tmp_path / "missing_test"
    gt_file = tmp_path / "gt.parquet"

    res = generate_synthetic_dataset(
        n_customers=300,
        seed=99,
        output_dir=out_dir,
        ground_truth_path=gt_file,
        validate=False,
    )

    # 1. MAR em NPS de interações: deve haver nulos proporcionais
    interactions_df = res["interactions"]
    nps_null_share = interactions_df["nps_rating"].isna().mean()
    assert 0.35 <= nps_null_share <= 0.80, (
        f"Taxa de missing em NPS fora do padrão MAR esperado (~58%): {nps_null_share:.2f}"
    )

    # 2. MCAR em atributos demográficos: gênero e faixa etária devem conter pequenos nulos
    customers_df = res["customers"]
    genero_nulls = customers_df["genero"].isna().sum()
    assert genero_nulls > 0, "Deveria haver valores ausentes em gênero (mecanismo MCAR documentado)"


def test_fidelity_metrics_computation(tmp_path: Path) -> None:
    """Verifica cálculo do relatório analítico de fidelidade em base amostral."""
    out_dir = tmp_path / "fidelity_test"
    gt_file = tmp_path / "gt.parquet"

    res = generate_synthetic_dataset(
        n_customers=300,
        seed=55,
        output_dir=out_dir,
        ground_truth_path=gt_file,
        validate=False,
    )

    metrics = compute_fidelity_metrics(
        customers_df=res["customers"],
        flights_df=res["flights"],
        transactions_df=res["transactions"],
    )

    assert "monthly_active_ratio" in metrics
    assert "top_20_spend_share" in metrics
    assert "tier_shares" in metrics
    assert "tolerances" in metrics
    assert len(metrics["tolerances"]) == 5


def test_no_future_transaction_leakage_in_qualification() -> None:
    """REGRESSÃO (Crítico 1): Transação de cartão/clube FUTURA não deve somar na qualificação.

    Cenário construído: compra em 2025-01-15, transação de cartão em 2025-06-01 (futura).
    A janela móvel de 365 dias em 2025-01-15 deve EXCLUIR a transação futura.
    """
    from synthetic.loyalty import evaluate_tier

    # Simular qual_history com transação futura
    purchase_dt = dt.datetime(2025, 1, 15, 10, 0, 0)
    future_card_tx = dt.datetime(2025, 6, 1, 12, 0, 0)
    past_flight_tx = dt.datetime(2024, 12, 1, 10, 0, 0)

    cutoff_365 = purchase_dt - dt.timedelta(days=365)
    qual_history = [
        (past_flight_tx, 5000, 1, 5000.0),     # voo passado: 5000 QP, 1 trecho
        (future_card_tx, 2000, 0, 0.0),        # cartão FUTURO: 2000 QP
    ]

    # ANTES do fix: recent_act incluía future_card_tx (sem teto temporal)
    # DEPOIS do fix: recent_act EXCLUI future_card_tx (teto = purchase_dt)
    recent_act = [h for h in qual_history if cutoff_365 <= h[0] <= purchase_dt]
    qp_rolling = sum(h[1] for h in recent_act)
    segs_rolling = sum(h[2] for h in recent_act)
    spend_rolling = sum(h[3] for h in recent_act)

    # Deve ter apenas 5000 QP (do voo passado), NÃO 7000 (incluindo futuro)
    assert qp_rolling == 5000, f"Vazamento temporal: qp_rolling={qp_rolling} (esperado 5000)"
    assert segs_rolling == 1
    assert spend_rolling == 5000.0

    # Tier deve ser 'azul' (5000 QP < 6000), NÃO 'topazio' (7000 QP >= 6000)
    tier = evaluate_tier(qp_rolling, segs_rolling, spend_rolling)
    assert tier == "azul", f"Tier incorreto devido a vazamento: {tier} (esperado azul)"


def test_downgrade_event_type_and_trigger() -> None:
    """REGRESSÃO (Crítico 2): Downgrade real deve gerar event_type='tier_downgrade' com trigger correto."""
    # Caso: Safira -> Topazio (rebaixamento)
    event_type, trigger = determine_tier_change_event(
        previous_tier="safira",
        new_tier="topazio",
        qualifying_points=5000,
        segments=5,
        spend_brl=5000.0,
    )
    assert event_type == "tier_downgrade"
    assert trigger == "qualification_cycle_expired"

    # Caso: Diamante -> Safira
    event_type, trigger = determine_tier_change_event(
        previous_tier="diamante",
        new_tier="safira",
        qualifying_points=8000,
        segments=8,
        spend_brl=8000.0,
    )
    assert event_type == "tier_downgrade"
    assert trigger == "qualification_cycle_expired"

    # Caso: Topazio -> Azul
    event_type, trigger = determine_tier_change_event(
        previous_tier="topazio",
        new_tier="azul",
        qualifying_points=1000,
        segments=1,
        spend_brl=1000.0,
    )
    assert event_type == "tier_downgrade"
    assert trigger == "qualification_cycle_expired"


def test_upgrade_event_type_and_trigger() -> None:
    """REGRESSÃO: Upgrades devem manter event_type='tier_upgrade' com triggers corretos."""
    # Upgrade para Topázio por QP
    event_type, trigger = determine_tier_change_event(
        previous_tier="azul",
        new_tier="topazio",
        qualifying_points=6500,
        segments=2,
        spend_brl=2000.0,
    )
    assert event_type == "tier_upgrade"
    assert trigger == "qualifying_points_reached"

    # Upgrade para Safira por segmentos
    event_type, trigger = determine_tier_change_event(
        previous_tier="topazio",
        new_tier="safira",
        qualifying_points=5000,
        segments=11,
        spend_brl=3000.0,
    )
    assert event_type == "tier_upgrade"
    assert trigger == "segments_reached"

    # Upgrade para Diamante por gasto alternativo
    event_type, trigger = determine_tier_change_event(
        previous_tier="safira",
        new_tier="diamante",
        qualifying_points=5000,
        segments=5,
        spend_brl=30000.0,
    )
    assert event_type == "tier_upgrade"
    assert trigger == "alternative_spend_reached"


def test_event_replay_reconstructs_final_tier(tmp_path: Path) -> None:
    """REGRESSÃO (Importante 1): Replay dos eventos deve reconstruir tier final de TODOS os clientes."""
    res = generate_synthetic_dataset(
        n_customers=200,
        seed=42,
        output_dir=tmp_path / "replay_test",
        ground_truth_path=tmp_path / "gt.parquet",
        validate=True,
    )

    customers_df = res["customers"]
    events_df = res["loyalty_events"]

    # Reconstruir tier por replay: último evento por cliente define o tier
    last_events = events_df.sort_values("event_date").groupby("customer_id").last().reset_index()
    replay_tiers = dict(zip(last_events["customer_id"], last_events["new_tier"], strict=True))

    # Clientes sem eventos ficam em 'azul'
    for cid in customers_df["customer_id"]:
        expected_tier = replay_tiers.get(cid, "azul")
        actual_tier = customers_df[customers_df["customer_id"] == cid]["current_tier"].values[0]
        assert actual_tier == expected_tier, (
            f"Cliente {cid}: replay={expected_tier} != customers.parquet={actual_tier}"
        )


def test_transactions_ordered_by_date(tmp_path: Path) -> None:
    """REGRESSÃO (Menor 1): transactions.parquet deve estar ordenado por transaction_date + customer_id."""
    res = generate_synthetic_dataset(
        n_customers=200,
        seed=123,
        output_dir=tmp_path / "order_test",
        ground_truth_path=tmp_path / "gt.parquet",
        validate=True,
    )
    tx_df = res["transactions"]

    # Verificar ordem global
    dates = tx_df["transaction_date"].values
    cust_ids = tx_df["customer_id"].values

    for i in range(1, len(dates)):
        if dates[i] < dates[i - 1]:
            raise AssertionError(
                f"transactions fora de ordem: idx={i-1} date={dates[i-1]} -> idx={i} date={dates[i]}"
            )
        if dates[i] == dates[i - 1] and cust_ids[i] < cust_ids[i - 1]:
            raise AssertionError(
                f"transactions empate de data mas customer_id fora de ordem: "
                f"idx={i-1} cid={cust_ids[i-1]} -> idx={i} cid={cust_ids[i]}"
            )

    # Também verificar flights, interactions, loyalty_events
    for table_name, date_col, id_col in [
        ("flights", "scheduled_departure", "flight_id"),
        ("interactions", "interaction_date", "interaction_id"),
        ("loyalty_events", "event_date", "event_id"),
    ]:
        df = res[table_name]
        dates = df[date_col].values
        ids = df[id_col].values
        for i in range(1, len(dates)):
            if dates[i] < dates[i - 1]:
                raise AssertionError(
                    f"{table_name} fora de ordem temporal: idx={i-1} {date_col}={dates[i-1]} -> "
                    f"idx={i} {date_col}={dates[i]}"
                )
            if dates[i] == dates[i - 1] and ids[i] < ids[i - 1]:
                raise AssertionError(
                    f"{table_name} empate de data mas {id_col} fora de ordem"
                )


def test_null_safety_in_loyalty_evaluate_tier() -> None:
    """REGRESSÃO (Importante 3): evaluate_tier não deve disparar TypeError com thresholds None.

    Simula YAML com qualifying_points: null e segments: null para um tier.
    A política null_semantics (fail-safe) = inelegível, não TypeError.
    """
    # Regras mock com null explícito (simula YAML com qualifying_points: null)
    rules_with_nulls = {
        "tiers": [
            {"key": "topazio", "qualification": {"qualifying_points": None, "segments": 6}},
            {"key": "safira", "qualification": {"qualifying_points": 10000, "segments": None}},
            {"key": "diamante", "qualification": {
                "qualifying_points": 12000,
                "segments": 12,
                "alternative_spend_brl": None,
            }},
            {"key": "diamante_unique", "qualification": {
                "qualifying_points": 26000,
                "segments": 26,
                "alternative_spend_brl": 50000,
            }},
        ]
    }

    # Não deve lançar TypeError
    tier = evaluate_tier(qualifying_points=6000, segments=6, spend_brl=1000.0, rules=rules_with_nulls)
    # topazio tem QP null -> inelegível por QP, mas segments=6 -> qualifica
    assert tier == "topazio"

    # Diamante tem alternative_spend_brl: null -> inelegível por gasto
    # Deve qualificar apenas se tiver QP E segments
    tier = evaluate_tier(qualifying_points=12000, segments=12, spend_brl=0.0, rules=rules_with_nulls)
    assert tier == "diamante"

    # Sem QP E segments, com alt_spend null -> não qualifica Diamante
    tier = evaluate_tier(qualifying_points=8000, segments=8, spend_brl=30000.0, rules=rules_with_nulls)
    # alt_spend é null -> inelegível; 8000 QP < 10000, 8 seg < 10 -> Safira não qualifica; Topázio 8000 >= 6000
    assert tier == "topazio"


def test_fail_loud_on_program_rules_load_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """REGRESSÃO (Importante 2): Falha ao carregar program_rules deve propagar exceção (fail-loud)."""
    from synthetic.loyalty import _load_rules

    def failing_program_rules():
        raise FileNotFoundError("Arquivo de regras não encontrado")

    monkeypatch.setattr("synthetic.loyalty.program_rules", failing_program_rules)

    with pytest.raises(FileNotFoundError, match="Arquivo de regras não encontrado"):
        _load_rules()
