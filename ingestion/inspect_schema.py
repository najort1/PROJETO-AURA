"""Inspeciona schemas e volumes de arquivos parquet brutos ANAC (utilitário dev).

Uso:
    python -m ingestion.inspect_schema                 # amostras padrão (primeiro/último mês)
    python -m ingestion.inspect_schema <caminho...>    # arquivos específicos
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb

from aura_core.paths import path


def describe(con: duckdb.DuckDBPyConnection, p: Path) -> None:
    safe = str(p).replace("'", "\\'")
    print("=" * 78)
    print(p)
    df = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{safe}')").df()
    print(df[["column_name", "column_type"]].to_string(index=False))
    n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{safe}')").fetchone()[0]
    print("rows:", n)


def _first_last(folder: Path, pattern: str) -> list[Path]:
    files = sorted(folder.glob(pattern)) if folder.exists() else []
    if not files:
        return []
    return [files[0], files[-1]] if len(files) > 1 else [files[0]]


def main(argv: list[str]) -> int:
    con = duckdb.connect()
    if argv:
        for a in argv:
            describe(con, Path(a))
        return 0

    anac = path("data/raw/anac")
    if not anac.exists():
        anac = path("ANAC")  # localização original, antes do registro em data/raw/
    samples = [
        anac / "aeroportos" / "aerodromos.parquet",
        anac / "aeronaves" / "aeronaves_rab.parquet",
    ]
    samples += _first_last(anac / "movimentacao", "movimentacao_*.parquet")
    samples += _first_last(anac / "voos_basica", "voos_basica_*.parquet")
    samples += _first_last(anac / "voos_combinada", "voos_combinada_*.parquet")
    for p in samples:
        if p.exists():
            describe(con, p)
        else:
            print(f"não encontrado: {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
