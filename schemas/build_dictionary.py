"""Gera o dicionário de dados (docs/data_dictionary/) a partir dos schemas YAML.

Uso: python -m schemas.build_dictionary   (ou `python tasks.py dictionary`)

O dicionário é 100% gerado: mudança de coluna muda o YAML, e o dicionário
é regenerado. Documentação escrita à mão diverge do código; aqui ela não pode.
"""
from __future__ import annotations

import json

from aura_core.log import get_logger
from aura_core.paths import ensure_dir, path
from schemas.load import list_contracts, load_contract

log = get_logger("schemas.dictionary")


def _render_table_md(c: dict) -> str:
    lines = [
        f"# `{c['table']}`",
        "",
        f"> **Descrição:** {c.get('description', '-')}  ",
        f"> **Granularidade:** {c.get('granularity', '-')}  ",
        f"> **Produzida por:** {c.get('produced_by', '-')}  ",
        f"> **Consumidores:** {', '.join(c.get('consumers', [])) or '-'}",
        "",
        "| Coluna | Tipo | Nulo? | Descrição | Unidade | Fonte | Sensível | Exemplo |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for col in c.get("columns", []):
        nullable = "sim" if col.get("nullable", True) else "não"
        sensitive = "🔴 sim" if col.get("sensitive") else "não"
        unit = col.get("unit") or "-"
        source = col.get("source") or "-"
        example = col.get("example")
        example = f"`{example}`" if example is not None else "-"
        desc = str(col.get("description", "")).replace("|", "\\|")
        lines.append(
            f"| `{col['name']}` | {col.get('dtype', '-')} | {nullable} | {desc} "
            f"| {unit} | {source} | {sensitive} | {example} |"
        )

    checks = c.get("checks", {}) or {}
    if checks:
        lines += ["", "## Checagens de contrato", ""]
        for key in checks.get("unique", []) or []:
            lines.append(f"- **unicidade:** `{key}`")
        for key in checks.get("non_null", []) or []:
            lines.append(f"- **não nulo:** `{key}`")
        for chk in checks.get("custom", []) or []:
            lines.append(f"- **{chk.get('name')}**: `{chk['expr']}` — {chk.get('message', '')}")
    return "\n".join(lines)


def main() -> int:
    contracts = [p for p in list_contracts()]
    if not contracts:
        log.warning("Nenhum contrato encontrado em schemas/")
        return 0

    out_dir = ensure_dir("docs/data_dictionary")
    index = [
        "# Dicionário de dados (gerado)",
        "",
        "> Gerado automaticamente a partir de `schemas/*.yaml` por `python tasks.py dictionary`.",
        "> Não edite à mão — edite o contrato e regenere.",
        "",
        "| Tabela | Granularidade | Produzida por | Consumidores | Colunas |",
        "|---|---|---|---|---|",
    ]
    combined = {}
    for p in contracts:
        c = load_contract(str(p))
        combined[c["table"]] = c
        md = _render_table_md(c)
        (out_dir / f"{c['table']}.md").write_text(md + "\n", encoding="utf-8")
        n = len(c.get("columns", []))
        index.append(
            f"| [`{c['table']}`]({c['table']}.md) | {c.get('granularidade', c.get('granularity', '-'))} "
            f"| {c.get('produced_by', '-')} | {', '.join(c.get('consumers', [])) or '-'} | {n} |"
        )
    (out_dir / "INDEX.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    (out_dir / "dictionary.json").write_text(
        json.dumps(combined, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log.info("Dicionário gerado: %d tabelas em %s", len(contracts), path("docs/data_dictionary"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
