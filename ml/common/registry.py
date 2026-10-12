"""Registro e persistência de modelos e metadados (Projeto Aura 2.0).

Salva modelos em data/analytics/models/ com contrato rigoroso de metadados:
seed, features, cutoff, métricas calculadas e carimbo de criação.
"""

from __future__ import annotations

import json
import pickle
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aura_core.paths import ensure_dir


def models_dir() -> Path:
    return ensure_dir("data/analytics/models")


def save_model_bundle(
    model_name: str,
    model_obj: Any,
    features: list[str],
    metrics: dict[str, Any],
    cutoff: str,
    seed: int,
    extra_metadata: dict[str, Any] | None = None,
) -> Path:
    """Persiste o artefato do modelo e seu manifesto de metadados correspondente."""
    m_dir = models_dir()

    # Salva artefato
    artifact_rel = f"{model_name}.pkl"
    artifact_path = m_dir / artifact_rel

    # Se for LightGBM nativo booster, também suporta save_model text
    if hasattr(model_obj, "save_model"):
        txt_path = m_dir / f"{model_name}.txt"
        model_obj.save_model(str(txt_path))

    with open(artifact_path, "wb") as f:
        pickle.dump(model_obj, f)

    meta = {
        "model_name": model_name,
        "artifact_file": artifact_rel,
        "created_at": datetime.now(UTC).isoformat(),
        "seed": int(seed),
        "cutoff": str(cutoff),
        "features": list(features),
        "n_features": len(features),
        "metrics": metrics,
        "extra": extra_metadata or {},
    }

    meta_path = m_dir / f"{model_name}_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    return meta_path


def load_model_bundle(model_name: str) -> tuple[Any, dict[str, Any]]:
    """Carrega o artefato de modelo e seus respectivos metadados."""
    m_dir = models_dir()
    meta_path = m_dir / f"{model_name}_metadata.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"Metadados do modelo não encontrados: {meta_path}")

    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)

    artifact_path = m_dir / meta["artifact_file"]
    if not artifact_path.exists():
        raise FileNotFoundError(f"Arquivo do artefato não encontrado: {artifact_path}")

    with open(artifact_path, "rb") as f:
        model_obj = pickle.load(f)

    return model_obj, meta
