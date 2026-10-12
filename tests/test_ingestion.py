"""Testes de integridade, determinismo, contratos e plausibilidade da ingestão ANAC (WS1).

Garante:
1. Determinismo do manifesto (re-execução -> mesmo sha256 exato).
2. Validação estrita dos contratos de dados (0 violações em todas as tabelas curadas).
3. Plausibilidade dos valores de calibração extraídos dos microdados reais.
4. Presença e consistência dos relatórios de governança e calibração.
"""

from __future__ import annotations

import json

from aura_core.paths import path
from ingestion.register import compute_sha256
from schemas.load import load_contract, validate_table


def test_manifest_determinism_and_integrity() -> None:
    """Valida integridade do manifesto e determinismo do cálculo de hash SHA-256."""
    manifest_path = path("data/manifests/anac.json")
    assert manifest_path.exists(), f"Manifesto {manifest_path} não encontrado"

    with open(manifest_path, encoding="utf-8") as f:
        data = json.load(f)

    meta = data.get("_meta", {})
    files = data.get("files", [])

    assert meta.get("total_files") == 723, (
        f"Esperado 723 arquivos no manifesto, encontrado {meta.get('total_files')}"
    )
    assert len(files) == 723, f"Esperado 723 entradas na lista de arquivos, encontrado {len(files)}"

    # Testa determinismo de hash em amostras representativas de diferentes subdiretórios
    sample_paths = [
        "data/raw/anac/aeroportos/aerodromos.parquet",
        "data/raw/anac/aeronaves/aeronaves_rab.parquet",
        "data/raw/anac/movimentacao/movimentacao_201903.parquet",
        "data/raw/anac/voos_basica/voos_basica_202401.parquet",
    ]

    files_by_path = {f["path"].replace("\\", "/"): f for f in files}

    for rel_path in sample_paths:
        abs_file = path(rel_path)
        assert abs_file.exists(), f"Arquivo físico {abs_file} não encontrado"

        expected_entry = files_by_path.get(rel_path)
        assert expected_entry is not None, f"Arquivo {rel_path} não registrado no manifesto"

        # Recalcula o hash do arquivo físico
        recomputed_sha = compute_sha256(abs_file)
        assert recomputed_sha == expected_entry["sha256"], (
            f"Hash recalculado divergente para {rel_path}: "
            f"esperado {expected_entry['sha256']}, obtido {recomputed_sha}"
        )


def test_curated_tables_contracts() -> None:
    """Valida se todas as tabelas curadas geradas cumprem estritamente os contratos YAML."""
    contracts_and_tables = [
        (
            "anac_routes_monthly",
            path("data/curated/anac/anac_routes_monthly.parquet"),
        ),
        ("anac_airports", path("data/curated/anac/anac_airports.parquet")),
        (
            "anac_delays_monthly",
            path("data/curated/anac/anac_delays_monthly.parquet"),
        ),
    ]

    for contract_name, table_path in contracts_and_tables:
        assert table_path.exists(), f"Tabela curada {table_path} não encontrada"
        contract = load_contract(contract_name)
        violations = validate_table(contract, table_path)
        assert violations == [], (
            f"Contrato '{contract_name}' violado em {table_path}:\n"
            + "\n".join(f"  - {v}" for v in violations)
        )


def test_calibration_values_plausibility() -> None:
    """Valida a plausibilidade dos agregados reais de mercado no calibration_values.json."""
    calib_path = path("data/curated/calibration_values.json")
    assert calib_path.exists(), f"Arquivo {calib_path} não encontrado"

    with open(calib_path, encoding="utf-8") as f:
        calib = json.load(f)

    # 1. Chaves obrigatórias contratuais
    required_keys = [
        "market.route_inventory",
        "market.volume_by_route_month",
        "market.seasonality_by_route",
        "market.delay_rate_by_route",
        "market.cancellation_rate_by_route",
        "market.airport_inventory",
    ]
    for k in required_keys:
        assert k in calib, f"Chave de calibração obrigatória ausente: {k}"

    # 2. Plausibilidade do volume mensal de passageiros
    vol = calib["market.volume_by_route_month"]
    mean_market_pax = vol.get("monthly_mean_market_pax", 0)
    mean_azul_pax = vol.get("monthly_mean_azul_pax", 0)

    # Mercado doméstico brasileiro típico: ~6M a ~10M passageiros pagos/mês
    # Valor real observado registrado: ~7.993.034 pax/mês
    assert 6_000_000 <= mean_market_pax <= 10_000_000, (
        f"Média mensal de mercado fora do intervalo plausível: {mean_market_pax}"
    )

    # Azul transporta tipicamente ~2M a ~3M passageiros pagos/mês no mercado doméstico
    # Valor real observado registrado: ~2.377.790 pax/mês
    assert 1_800_000 <= mean_azul_pax <= 3_500_000, (
        f"Média mensal da Azul fora do intervalo plausível: {mean_azul_pax}"
    )

    # Market share da Azul no mercado doméstico deve estar em torno de 25% a 35%
    azul_share = mean_azul_pax / mean_market_pax
    assert 0.25 <= azul_share <= 0.35, (
        f"Market share doméstico da Azul fora do esperado: {azul_share:.2%}"
    )

    # 3. Plausibilidade de rotas ativas
    routes = calib["market.route_inventory"]
    total_routes = routes.get("total_active_domestic_routes", 0)
    azul_routes = routes.get("total_azul_routes", 0)

    # Malha doméstica regular do Brasil: tipicamente 1.200 a 2.200 rotas
    assert 1_200 <= total_routes <= 2_200, (
        f"Contagem de rotas fora do intervalo esperado: {total_routes}"
    )
    assert 800 <= azul_routes <= total_routes, (
        f"Rotas da Azul fora do intervalo esperado: {azul_routes}"
    )

    # 4. Plausibilidade da taxa de atraso operacional
    delays = calib["market.delay_rate_by_route"]
    mean_delay = delays.get("overall_mean", 0.0)

    # Taxa de atraso (>15 min) da aviação civil: tipicamente 12% a 22%
    # Valor real observado: 16.75%
    assert 0.12 <= mean_delay <= 0.22, (
        f"Taxa média de atraso fora do padrão histórico: {mean_delay:.2%}"
    )

    # 5. Plausibilidade da sazonalidade mensal
    season = calib["market.seasonality_by_route"]
    monthly_idx = season.get("market_monthly_index", {})
    assert len(monthly_idx) == 12, (
        f"Esperado 12 meses na sazonalidade, encontrado {len(monthly_idx)}"
    )

    indices = [float(monthly_idx[str(m)]) for m in range(1, 13)]
    avg_index = sum(indices) / 12.0
    assert 0.98 <= avg_index <= 1.02, (
        f"Índices de sazonalidade não estão normalizados em torno de 1.0: média = {avg_index}"
    )

    # Julho (mês 7) é pico histórico de férias escolares no Brasil (> 1.0)
    assert float(monthly_idx["7"]) > 1.05, (
        f"Mês de julho não apresentou índice de pico: {monthly_idx['7']}"
    )
    # Fevereiro (mês 2) é o mês mais curto e de menor tráfego (< 1.0)
    assert float(monthly_idx["2"]) < 0.95, (
        f"Mês de fevereiro não apresentou vale sazonal: {monthly_idx['2']}"
    )

    # 6. Status formal de cancelamento (não computável localmente)
    cancels = calib["market.cancellation_rate_by_route"]
    assert cancels.get("status") == "not_computable_local"
    assert cancels.get("value") is None
    assert "limitation_note" in cancels

    # 7. Aeródromos
    airports = calib["market.airport_inventory"]
    assert airports.get("total_airports") > 4000
    assert 150 <= airports.get("commercial_active_airports") <= 300


def test_documentation_and_reports_exist() -> None:
    """Verifica existência e preenchimento dos relatórios de auditoria e calibração."""
    src_verif = path("docs/source_verification.md")
    assert src_verif.exists(), f"{src_verif} não encontrado"
    src_text = src_verif.read_text(encoding="utf-8")
    assert "Microdados ANAC locais" in src_text
    assert "tarifas aéreas" in src_text
    assert "Azul S.A." in src_text
    assert "Azul Fidelidade" in src_text
    assert "CC BY-ND 3.0" in src_text

    calib_rep = path("docs/calibration_report.md")
    assert calib_rep.exists(), f"{calib_rep} não encontrado"
    calib_text = calib_rep.read_text(encoding="utf-8")
    assert "market.route_inventory" in calib_text
    assert "market.delay_rate_by_route" in calib_text
    assert "market.cancellation_rate_by_route" in calib_text
    assert "16.75%" in calib_text or "16.7" in calib_text
