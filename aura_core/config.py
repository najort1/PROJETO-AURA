"""Carregamento de configuração YAML e derivação determinística de seeds."""

from __future__ import annotations

import zlib
from functools import cache

import yaml

from aura_core.paths import ROOT, path

try:
    from dotenv import load_dotenv

    _env_file = ROOT / ".env"
    if _env_file.exists():
        load_dotenv(_env_file)
except ImportError:
    pass


def load_yaml(p: str) -> dict:
    """Carrega um YAML do projeto (relativo à raiz) em dict."""
    with open(path(p), encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"Config esperava um mapeamento YAML no topo: {p}")
    return data


@cache
def settings() -> dict:
    """config/settings.yaml (cacheado)."""
    return load_yaml("config/settings.yaml")


def program_rules() -> dict:
    """config/program_rules.yaml (sem cache: pode ser atualizado entre estágios)."""
    return load_yaml("config/program_rules.yaml")


def child_seed(base_seed: int, name: str) -> int:
    """Deriva uma seed determinística por estágio a partir da seed global.

    Garante que cada componente (generator, modelos, sentiment, agent) tenha
    reprodutibilidade independente sem colisões triviais de seed.
    """
    return (int(base_seed) + zlib.crc32(name.encode("utf-8"))) % (2**31)
