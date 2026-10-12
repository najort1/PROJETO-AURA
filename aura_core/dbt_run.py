"""Invoca o dbt programaticamente (dbt-duckdb) - alvo `features` do tasks.py.

Uso: python -m aura_core.dbt_run
Falha alto (exit != 0 + mensagem clara) se o projeto dbt não existir.
"""
from __future__ import annotations

import sys

from aura_core.paths import ROOT


def main() -> int:
    try:
        from dbt.cli.main import dbtRunner
    except ImportError:
        print(
            "ERRO: dbt-duckdb não está instalado no ambiente. Rode: pip install dbt-duckdb",
            file=sys.stderr,
        )
        return 1

    project_dir = ROOT / "dbt"
    if not (project_dir / "dbt_project.yml").exists():
        print(
            "ERRO: dbt/dbt_project.yml não encontrado. A frente de features (WS3) "
            "ainda não criou o projeto dbt.",
            file=sys.stderr,
        )
        return 1

    runner = dbtRunner()
    result = runner.invoke(
        ["run", "--project-dir", str(project_dir), "--profiles-dir", str(project_dir)]
    )
    if not result.success:
        for node in result.nodes:
            if node.status in {"error", "fail", "skipped"}:
                print(f"dbt: {node.name} -> {node.status}: {node.message}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
