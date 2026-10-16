"""Utilitários TreeSHAP nativos via LightGBM (sem dependência do pacote shap).

Utiliza lightgbm.Booster.predict(..., pred_contrib=True) para cálculo exato
de contribuições locais e importância global de atributos.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")  # Backend não interativo
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def compute_shap_contributions(
    model: Any,
    X: pd.DataFrame | np.ndarray,
    feature_names: list[str] | None = None,
) -> tuple[pd.DataFrame, float]:
    """Calcula contribuições SHAP exatas via TreeSHAP do LightGBM.

    Retorna:
        contrib_df: DataFrame das contribuições de cada feature (mesmas linhas de X)
        base_value: valor base esperado (bias/intercepto)
    """
    if isinstance(X, pd.DataFrame):
        names = feature_names or list(X.columns)
        X_arr = X.values
        idx = X.index
    else:
        X_arr = np.asarray(X)
        names = feature_names or [f"f_{i}" for i in range(X_arr.shape[1])]
        idx = pd.RangeIndex(len(X_arr))

    # Booster nativo ou estimador scikit-learn do LightGBM
    booster = model.booster_ if hasattr(model, "booster_") else model

    # pred_contrib=True retorna (n_samples, n_features + 1)
    contribs = booster.predict(X_arr, pred_contrib=True)
    n_feats = len(names)

    feature_contribs = contribs[:, :n_feats]
    base_value = float(contribs[0, -1]) if len(contribs) > 0 else 0.0

    contrib_df = pd.DataFrame(feature_contribs, index=idx, columns=names)
    return contrib_df, base_value


def global_feature_importance(contrib_df: pd.DataFrame) -> pd.DataFrame:
    """Calcula a importância global como a média do valor absoluto do SHAP (|contrib|)."""
    mean_abs = contrib_df.abs().mean().sort_values(ascending=False)
    df = pd.DataFrame(
        {
            "feature": mean_abs.index,
            "mean_abs_shap": mean_abs.values,
            "importance_rank": np.arange(1, len(mean_abs) + 1),
        }
    )
    return df


def local_top_k(
    customer_ids: pd.Series | list[str] | np.ndarray,
    contrib_df: pd.DataFrame,
    X_df: pd.DataFrame | None = None,
    k: int = 3,
) -> pd.DataFrame:
    """Extrai os top-k fatores de maior impacto (por magnitude |SHAP|) por cliente."""
    c_ids = np.asarray(customer_ids)
    n = len(c_ids)
    feats = list(contrib_df.columns)
    c_vals = contrib_df.values

    records: list[dict[str, Any]] = []

    for i in range(n):
        row_shap = c_vals[i]
        # Índices dos top k em ordem decrescente de magnitude absoluta
        top_indices = np.argsort(-np.abs(row_shap))[:k]

        top_names = [feats[idx] for idx in top_indices]
        rec: dict[str, Any] = {
            "customer_id": str(c_ids[i]),
            "shap_top3_json": json.dumps(top_names, ensure_ascii=False),
        }

        for rank, idx in enumerate(top_indices, start=1):
            feat_name = feats[idx]
            rec[f"top{rank}_feature"] = feat_name
            rec[f"top{rank}_shap"] = float(row_shap[idx])
            if X_df is not None and feat_name in X_df.columns:
                rec[f"top{rank}_value"] = float(X_df.iloc[i][feat_name])
            else:
                rec[f"top{rank}_value"] = 0.0

        records.append(rec)

    return pd.DataFrame(records)


def plot_waterfall(
    feature_names: list[str],
    shap_values: list[float] | np.ndarray,
    base_value: float,
    predicted_value: float,
    title: str,
    output_path: str | Path,
    max_features: int = 8,
) -> None:
    """Gera e salva gráfico waterfall simples de explicabilidade local com matplotlib."""
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    names = list(feature_names)
    vals = np.asarray(shap_values, dtype=float)

    # Ordenar por magnitude absoluta
    order = np.argsort(-np.abs(vals))
    names = [names[i] for i in order]
    vals = vals[order]

    if len(names) > max_features:
        top_names = names[:max_features]
        top_vals = list(vals[:max_features])
        other_val = float(np.sum(vals[max_features:]))
        top_names.append("Outras features")
        top_vals.append(other_val)
        names = top_names
        vals = np.asarray(top_vals)

    fig, ax = plt.subplots(figsize=(9, 6))

    accum = base_value
    y_positions = np.arange(len(names) + 2)

    # Base value bar
    ax.barh(0, base_value, color="#4A90E2", alpha=0.8, label="Base value (E[Y])")
    labels = [f"E[Y] ({base_value:+.2f})"]

    for i, (name, val) in enumerate(zip(names, vals, strict=True), start=1):
        color = "#2E7D32" if val >= 0 else "#C62828"
        ax.barh(i, val, left=accum, color=color, alpha=0.85)
        accum += val
        labels.append(f"{name} ({val:+.2f})")

    # Final prediction bar
    final_val = (
        accum if abs(predicted_value - accum) > 0.01 and abs(accum) > 0.01 else predicted_value
    )
    ax.barh(len(names) + 1, final_val, color="#0D47A1", alpha=0.9, label="Predição Final")
    labels.append(f"f(x) Final ({final_val:+.2f})")

    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Contribuição no modelo")
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.axvline(0, color="gray", linestyle="--", linewidth=0.8)
    ax.grid(axis="x", linestyle=":", alpha=0.6)

    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_global_summary(
    importance_df: pd.DataFrame,
    title: str,
    output_path: str | Path,
    top_n: int = 15,
) -> None:
    """Gera gráfico de barras com a importância global média |SHAP|."""
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    top_df = importance_df.head(top_n).iloc[::-1]

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(top_df["feature"], top_df["mean_abs_shap"], color="#00529B", alpha=0.85)
    ax.set_xlabel("Importância Média |SHAP|")
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.grid(axis="x", linestyle=":", alpha=0.6)

    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close(fig)
