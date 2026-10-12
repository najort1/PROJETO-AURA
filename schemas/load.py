"""Carrega contratos YAML e valida tabelas (parquet) contra eles.

Uso:
    from schemas.load import load_contract, validate_table
    violations = validate_table(load_contract("features_customer"), "data/analytics/features_customer.parquet")

`validate_table` retorna lista de violações (vazia = conforme contrato).
Checks custom são expressões SQL booleanas avaliadas via DuckDB sobre a tabela.
"""
from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import yaml

from aura_core.paths import path


def _contract_path(name: str) -> Path:
    p = Path(name)
    if p.suffix == ".yaml" and p.exists():
        return p
    candidate = path("schemas") / f"{name}.yaml"
    if not candidate.exists():
        raise FileNotFoundError(f"Contrato não encontrado: {candidate}")
    return candidate


def load_contract(name: str) -> dict:
    with open(_contract_path(name), encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not data or "table" not in data:
        raise ValueError(f"Contrato inválido (sem 'table'): {name}")
    return data


def list_contracts() -> list[Path]:
    return sorted(path("schemas").glob("*.yaml"))


def _dtype_ok(declared: str, series: pd.Series) -> bool:
    d = str(declared).lower()
    if d in {"string", "str", "text"}:
        return pd.api.types.is_string_dtype(series)
    if d == "category":
        return isinstance(series.dtype, pd.CategoricalDtype)
    if d in {"int", "integer", "int64", "int32"}:
        return pd.api.types.is_integer_dtype(series)
    if d in {"float", "double", "float64", "number"}:
        return pd.api.types.is_numeric_dtype(series)
    if d in {"bool", "boolean"}:
        return pd.api.types.is_bool_dtype(series)
    if d in {"date", "datetime", "timestamp"}:
        return pd.api.types.is_datetime64_any_dtype(series)
    return True  # tipo declarado desconhecido: documentado, não bloqueia


def validate_table(contract: dict, table_path: str | Path) -> list[str]:
    """Valida um parquet contra o contrato. Retorna lista de violações."""
    table_path = Path(table_path)
    if not table_path.exists():
        return [f"arquivo ausente: {table_path}"]

    tname = contract.get("table", "?")
    errors: list[str] = []
    df = pd.read_parquet(table_path)

    declared_cols = {c["name"]: c for c in contract.get("columns", [])}
    for name in declared_cols:
        if name not in df.columns:
            errors.append(f"[{tname}] coluna declarada ausente: {name}")
    for name in df.columns:
        if name not in declared_cols:
            errors.append(f"[{tname}] coluna extra não declarada no contrato: {name}")

    for name, col in declared_cols.items():
        if name not in df.columns:
            continue
        s = df[name]
        if not _dtype_ok(col.get("dtype", ""), s):
            errors.append(f"[{tname}] dtype de {name}: declarado {col.get('dtype')}, encontrado {s.dtype}")
        if not col.get("nullable", True) and s.isna().any():
            errors.append(f"[{tname}] {name} contém nulos (nullable: false)")

    checks = contract.get("checks", {}) or {}
    for key in checks.get("unique", []) or []:
        if key in df.columns and df[key].duplicated().any():
            errors.append(f"[{tname}] chave não única: {key}")
    for key in checks.get("non_null", []) or []:
        if key in df.columns and df[key].isna().any():
            errors.append(f"[{tname}] coluna com nulos exigidos não nulos: {key}")
    for col, allowed in (checks.get("allowed_values", {}) or {}).items():
        if col in df.columns:
            bad = set(df[col].dropna().unique()) - set(allowed)
            if bad:
                errors.append(f"[{tname}] valores fora do domínio em {col}: {sorted(bad)[:5]}")

    con = duckdb.connect()
    try:
        con.execute(
            f"CREATE VIEW contract_check_t AS SELECT * FROM read_parquet('{table_path.as_posix()}')"
        )
        for chk in checks.get("custom", []) or []:
            expr = chk["expr"]
            val = con.execute(f"SELECT COALESCE({expr}, FALSE) FROM contract_check_t").fetchone()[0]
            if not val:
                errors.append(
                    f"[{tname}] check custom falhou: {chk.get('name')} - {chk.get('message', '')}"
                )
    finally:
        con.close()
    return errors


def validate_or_raise(contract: dict, table_path: str | Path) -> None:
    """Valida e levanta RuntimeError se houver violações (usado pelo pipeline)."""
    errors = validate_table(contract, table_path)
    if errors:
        raise RuntimeError("Contrato de dados violado:\n" + "\n".join(f"  - {e}" for e in errors))
