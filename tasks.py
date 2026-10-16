#!/usr/bin/env python3
"""Aura 2.0 - task runner multiplataforma (equivalente funcional ao Makefile).

Uso:
    python tasks.py <alvo>
    python tasks.py help
    python tasks.py all          # pipeline completo, do zero aos artefatos analíticos + testes

O Makefile na raiz apenas repassa os mesmos alvos para este script, permitindo
`make <alvo>` em ambientes com GNU Make (Linux, macOS, CI).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _venv_python() -> str:
    rel = Path("Scripts") / "python.exe" if os.name == "nt" else Path("bin") / "python"
    candidate = ROOT / ".venv" / rel
    return str(candidate) if candidate.exists() else sys.executable


PY = _venv_python()

# Alvo -> lista de passos. Cada passo é uma lista de argumentos na qual "{py}" é
# substituído pelo interpretador do venv do projeto. Passos falham alto (erro
# claro) para que a integração nunca "pareça" concluída sem estar.
TARGETS: dict[str, list[list[str]]] = {
    "ingest": [
        ["{py}", "-m", "ingestion.register"],
        ["{py}", "-m", "ingestion.curate"],
    ],
    "synth": [
        ["{py}", "-m", "synthetic.generate"],
        ["{py}", "-m", "synthetic.fidelity_report"],
    ],
    "features": [
        ["{py}", "-m", "aura_core.dbt_run"],
    ],
    "train": [
        ["{py}", "-m", "ml.clv.train"],
        ["{py}", "-m", "ml.churn.train"],
    ],
    "score": [
        ["{py}", "-m", "ml.segmentation.train"],
    ],
    "sentiment": [
        ["{py}", "-m", "ml.sentiment.pipeline"],
    ],
    "rag": [
        ["{py}", "-m", "agent.rag.indexer"],
    ],
    "agent-eval": [
        ["{py}", "-m", "agent.eval.harness"],
    ],
    "agent-eval-real": [
        ["{py}", "-m", "ml.eval.real_input_eval"],
    ],
    "agent-precompute": [
        ["{py}", "-m", "agent.pipeline", "--precompute-demo"],
    ],
    "fairness": [
        ["{py}", "-m", "ml.fairness.audit"],
    ],
    "impact": [
        ["{py}", "-m", "ml.impact.simulate"],
    ],
    "dictionary": [
        ["{py}", "-m", "schemas.build_dictionary"],
    ],
    "benchmarks": [
        ["{py}", "-m", "ingestion.benchmarks"],
    ],
    "app": [
        ["{py}", "-m", "streamlit", "run", "app/main.py"],
    ],
    "dashboard": [
        ["pnpm", "--dir", "dashboard", "dev"],
    ],
    "dashboard-build": [
        ["pnpm", "--dir", "dashboard", "build"],
    ],
    "test": [
        ["{py}", "-m", "pytest"],
    ],
    "lint": [
        ["{py}", "-m", "ruff", "check", "."],
    ],
    "fmt": [
        ["{py}", "-m", "ruff", "format", "."],
    ],
}

DESCRIPTIONS = {
    "ingest": "Registra fontes brutas (manifesto com sha256/licenca) e curar agregados ANAC",
    "synth": "Gera base sintetica calibrada + relatorio de fidelidade vs fontes publicas",
    "features": "Rodar modelos dbt: curated -> analytics (features anti-vazamento temporal)",
    "train": "Treina CLV (BG/NBD+GG baseline vs LightGBM) e churn (logistica vs LightGBM)",
    "score": "Score de Alto Valor + segmentacao/personas + sensibilidade",
    "sentiment": "Corpus PT-BR rotulado por aspecto + 2 abordagens + mapa de atritos",
    "rag": "Indexa a base de conhecimento versionada (regulamento Azul Fidelidade)",
    "agent-eval": "Harness de avaliacao do agente (groundedness, guardrails, adversarial)",
    "agent-eval-real": "Avaliacao do agente sobre clientes reais da base (agent_input.parquet)",
    "agent-precompute": "Precomputa recomendacoes offline para o modo demonstracao do app",
    "fairness": "Auditoria de vies por faixa etaria, genero e regiao",
    "impact": "Simulacao de impacto (cenarios conservador/base/otimista + sensibilidade)",
    "dictionary": "Gera dicionario de dados em docs/data_dictionary a partir dos schemas",
    "benchmarks": "Curadoria e agregacao dos benchmarks (loyalty, satisfacao e reviews)",
    "app": "Abre o protótipo Streamlit legado (port 8501)",
    "dashboard": "Inicia o cockpit oficial de produção em Next.js 15 (port 3000)",
    "dashboard-build": "Gera build de produção do dashboard Next.js 15",
    "test": "pytest (unit + integracao)",
    "lint": "ruff check",
    "fmt": "ruff format",
}

# Pipeline "do zero ao painel" (o app roda separado, e interativo).
PIPELINE = [
    "ingest",
    "benchmarks",
    "synth",
    "features",
    "train",
    "score",
    "sentiment",
    "rag",
    "agent-eval",
    "agent-precompute",
    "fairness",
    "impact",
    "dictionary",
]
ALL = PIPELINE + ["test"]


def run_step(step: list[str]) -> None:
    cmd = [PY if arg == "{py}" else arg for arg in step]
    print(f"\n$ {' '.join(cmd)}", flush=True)
    is_win = sys.platform == "win32"
    subprocess.run(cmd, cwd=ROOT, check=True, shell=is_win)


def run_target(name: str) -> None:
    for step in TARGETS[name]:
        run_step(step)


def main(argv: list[str]) -> int:
    if not argv or argv[0] in {"help", "--help", "-h"}:
        print(__doc__)
        print("Alvos disponiveis:")
        for name, desc in DESCRIPTIONS.items():
            print(f"  {name:<18} {desc}")
        print(f"  {'all':<18} Pipeline completo: {' -> '.join(ALL)}")
        return 0
    name = argv[0]
    if name == "all":
        for target in ALL:
            print(f"\n{'=' * 72}\n=== AURA :: {target.upper()}\n{'=' * 72}", flush=True)
            run_target(target)
        print("\nPipeline concluido com sucesso.")
        return 0
    if name not in TARGETS:
        print(f"Alvo desconhecido: {name!r}\nUse: python tasks.py help", file=sys.stderr)
        return 2
    run_target(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
