"""Módulo de particionamento e validação temporal (Aura 2.0).

Regra Inegociável: ZERO random split.
Toda partição respeita o corte temporal explícito (rolling origin).
"""

from __future__ import annotations

import pandas as pd

from aura_core.config import settings


def get_timeline_config() -> dict[str, str]:
    """Retorna os marcos temporais configurados em config/settings.yaml."""
    cfg = settings().get("timeline", {})
    return {
        "synthetic_start": str(cfg.get("synthetic_start", "2023-09-01")),
        "synthetic_end": str(cfg.get("synthetic_end", "2026-08-31")),
        "feature_cutoff": str(cfg.get("feature_cutoff", "2025-08-31")),
        "target_start": str(cfg.get("target_start", "2025-09-01")),
        "target_end": str(cfg.get("target_end", "2026-08-31")),
        "validation_cutoff": str(cfg.get("validation_cutoff", "2025-02-28")),
        "validation_target_start": str(cfg.get("validation_target_start", "2025-03-01")),
        "validation_target_end": str(cfg.get("validation_target_end", "2026-02-28")),
    }


def split_by_date(
    df: pd.DataFrame,
    date_col: str,
    train_end: str | pd.Timestamp,
    test_start: str | pd.Timestamp,
    test_end: str | pd.Timestamp | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Realiza split estritamente temporal sem vazamento.

    Treino: date_col <= train_end
    Teste: date_col >= test_start (e opcionalmente <= test_end)
    """
    dates = pd.to_datetime(df[date_col])
    t_end = pd.to_datetime(train_end)
    s_start = pd.to_datetime(test_start)

    if t_end >= s_start:
        raise ValueError(
            f"Vazamento temporal potencial: train_end ({t_end}) deve ser estritamente anterior a test_start ({s_start})"
        )

    train_mask = dates <= t_end
    if test_end is not None:
        e_end = pd.to_datetime(test_end)
        test_mask = (dates >= s_start) & (dates <= e_end)
    else:
        test_mask = dates >= s_start

    train_df = df.loc[train_mask].copy()
    test_df = df.loc[test_mask].copy()
    return train_df, test_df


def assert_no_temporal_leakage(
    df: pd.DataFrame,
    date_cols: list[str],
    cutoff: str | pd.Timestamp,
) -> None:
    """Valida fail-loud que nenhuma coluna de data excede o cutoff estabelecido."""
    c_date = pd.to_datetime(cutoff)
    violations: list[str] = []

    for col in date_cols:
        if col not in df.columns:
            continue
        max_date = pd.to_datetime(df[col].dropna()).max()
        if pd.notna(max_date) and max_date > c_date:
            violations.append(
                f"Coluna '{col}' tem data máxima {max_date.strftime('%Y-%m-%d')} posterior ao cutoff {c_date.strftime('%Y-%m-%d')}"
            )

    if violations:
        msg = "FALHA CRÍTICA ANTI-VAZAMENTO TEMPORAL:\n" + "\n".join(f"  - {v}" for v in violations)
        raise ValueError(msg)
