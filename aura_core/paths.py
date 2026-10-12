"""Resolução de caminhos do repositório (sempre relativos à raiz do projeto)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def path(p: str | Path) -> Path:
    """Converte um caminho relativo ao projeto em Path absoluto."""
    q = Path(p)
    return q if q.is_absolute() else ROOT / q


def ensure_dir(p: str | Path) -> Path:
    """Garante que um diretório existe (cria pais) e o retorna."""
    q = path(p)
    q.mkdir(parents=True, exist_ok=True)
    return q
