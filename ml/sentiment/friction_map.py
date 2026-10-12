"""Mapeamento analítico de atritos (aspectos × intensidade × tendência temporal).

Gera:
1. data/analytics/friction_map.parquet:
   - Granularidade: aspecto × semestre (2023-S2 a 2026-S2, último parcial: jul-ago/2026)
   - Intensidade semestral, média global, deltas e direção de tendência
   - Validado contra schemas/friction_map.yaml
2. data/curated/friction_weights.json:
   - Pesos normalizados de atrito para o gerador sintético de WS2
   - Schema documentado no próprio arquivo através da chave '_meta'
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Final

import numpy as np
import pandas as pd

from aura_core.log import get_logger
from aura_core.paths import ensure_dir, path
from ml.sentiment.corpus import ASPECTS
from schemas.load import load_contract, validate_or_raise

logger = get_logger("sentiment.friction_map")

SEMESTERS: Final[list[str]] = [
    "2023-S2",
    "2024-S1",
    "2024-S2",
    "2025-S1",
    "2025-S2",
    "2026-S1",
    "2026-S2",  # semestre PARCIAL: cobre apenas jul-ago/2026 (fim da janela sintetica)
]

# ---- Parâmetros de design do mapa de atritos (premissas calibradas, não magic numbers) ----
# Peso da severidade negativa na intensidade semestral (fórmula: 70% negatividade + 30% prevalência).
NEG_SEVERITY_WEIGHT: Final[float] = 0.70
# Peso complementar da prevalência relativa do aspecto no semestre.
PREVALENCE_WEIGHT: Final[float] = 0.30
# Escala de prevalência: com 7 aspectos, a prevalência média por aspecto ≈ 1/7 das
# avaliações; multiplicar por ~3 leva a prevalência típica de volta à faixa [0, 1].
PREVALENCE_SCALE: Final[float] = 3.0
# Limiar de inclinação linear (por semestre) para declarar tendência crescente/decrescente;
# abaixo disso em módulo, a tendência é "estavel". Calibrado para sensibilidade a mudanças
# de ~0,09 de intensidade ao longo da janela de 7 semestres.
TREND_SLOPE_THRESHOLD: Final[float] = 0.015
# Expoente de amortecimento do volume negativo no peso bruto do aspecto
# (sqrt via ** 0.5): reduz dominância de aspectos hiper-mencionados.
NEG_VOLUME_DAMPING_EXPONENT: Final[float] = 0.5


def _assign_semester(date_val: pd.Timestamp) -> str:
    """Classifica uma data em seu semestre correspondente (fail loud fora do dominio)."""
    year = date_val.year
    sem = "S1" if date_val.month <= 6 else "S2"
    label = f"{year}-{sem}"
    if label not in SEMESTERS:
        raise ValueError(
            f"Data {date_val} fora do dominio de semestres do mapa de atritos "
            f"({SEMESTERS[0]} a {SEMESTERS[-1]}): rotular '{label}' exigiria falha silenciosa. "
            "Ajuste SEMESTERS ou a janela do corpus."
        )
    return label


def compute_friction_map(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Calcula o mapa analítico de atritos e os pesos para WS2.

    Args:
        df: DataFrame do corpus de avaliações (sentiment_reviews).

    Returns:
        Tupla com (friction_df, friction_weights_dict).
    """
    logger.info("Calculando mapa de atritos a partir de %d avaliações...", len(df))
    df = df.copy()
    df["review_date"] = pd.to_datetime(df["review_date"])
    df["semester"] = df["review_date"].apply(_assign_semester)

    # 1. Contagens básicas por aspecto e semestre
    aspect_sem_stats: dict[str, dict[str, dict[str, Any]]] = {asp: {} for asp in ASPECTS}

    total_neg_by_aspect: dict[str, int] = {asp: 0 for asp in ASPECTS}
    total_mentions_by_aspect: dict[str, int] = {asp: 0 for asp in ASPECTS}

    for sem in SEMESTERS:
        sem_df = df[df["semester"] == sem]
        if sem_df.empty:
            logger.warning(
                "Semestre %s sem avaliações no corpus: intensidades do semestre "
                "serão 0 — verificar janela do corpus (semestres vazios são anômalos).",
                sem,
            )
        n_sem = max(1, len(sem_df))

        for asp in ASPECTS:
            has_col = f"has_{asp}"
            pol_col = f"polarity_{asp}"

            mentioned = sem_df[sem_df[has_col] == 1]
            n_mentions = len(mentioned)
            n_neg = (mentioned[pol_col] == "negativo").sum()
            n_neu = (mentioned[pol_col] == "neutro").sum()
            n_pos = (mentioned[pol_col] == "positivo").sum()

            neg_rate = float(n_neg / n_mentions) if n_mentions > 0 else 0.0
            prevalence = float(n_mentions / n_sem)

            # Intensidade: fórmula de design documentada (premissa calibrada):
            # 70% severidade negativa + 30% prevalência relativa. A prevalência é
            # escalada por PREVALENCE_SCALE para retornar à faixa [0, 1] dado que
            # há 7 aspectos (menções por aspecto ≈ 1/7 das avaliações).
            intensity = float(
                np.clip(
                    NEG_SEVERITY_WEIGHT * neg_rate
                    + PREVALENCE_WEIGHT * min(1.0, prevalence * PREVALENCE_SCALE),
                    0.0,
                    1.0,
                )
            )

            aspect_sem_stats[asp][sem] = {
                "mention_count": int(n_mentions),
                "negative_count": int(n_neg),
                "neutral_count": int(n_neu),
                "positive_count": int(n_pos),
                "negative_rate": round(neg_rate, 4),
                "semester_intensity": round(intensity, 4),
            }

            total_neg_by_aspect[asp] += int(n_neg)
            total_mentions_by_aspect[asp] += int(n_mentions)

    # 2. Médias globais, tendências e deltas
    mean_intensities: dict[str, float] = {}
    trend_directions: dict[str, str] = {}
    raw_weights: dict[str, float] = {}

    for asp in ASPECTS:
        intensities = [aspect_sem_stats[asp][s]["semester_intensity"] for s in SEMESTERS]
        mean_int = float(np.mean(intensities))
        mean_intensities[asp] = round(mean_int, 4)

        # Tendência via inclinação linear simples ao longo dos semestres mapeados
        x = np.arange(len(SEMESTERS))
        slope = float(np.polyfit(x, intensities, 1)[0])

        if slope > TREND_SLOPE_THRESHOLD:
            trend = "crescente"
        elif slope < -TREND_SLOPE_THRESHOLD:
            trend = "decrescente"
        else:
            trend = "estavel"
        trend_directions[asp] = trend

        # Peso bruto do aspecto: intensidade media ponderada pelo volume negativo
        # (amortecido com NEG_VOLUME_DAMPING_EXPONENT)
        raw_weights[asp] = mean_int * (total_neg_by_aspect[asp] ** NEG_VOLUME_DAMPING_EXPONENT)

    # 3. Normalização dos pesos para soma exata = 1.0
    weight_sum = sum(raw_weights.values())
    norm_weights = {asp: round(raw_weights[asp] / weight_sum, 4) for asp in ASPECTS}
    # Ajusta eventual resíduo de arredondamento no aspecto de maior peso
    residual = round(1.0 - sum(norm_weights.values()), 4)
    top_aspect = max(norm_weights, key=norm_weights.get)  # type: ignore[arg-type]
    norm_weights[top_aspect] = round(norm_weights[top_aspect] + residual, 4)

    # 4. Montagem das linhas do DataFrame de saída
    rows: list[dict[str, Any]] = []
    for asp in ASPECTS:
        for idx, sem in enumerate(SEMESTERS):
            stats = aspect_sem_stats[asp][sem]
            curr_intensity = stats["semester_intensity"]

            if idx == 0:
                delta = 0.0
            else:
                prev_intensity = aspect_sem_stats[asp][SEMESTERS[idx - 1]]["semester_intensity"]
                delta = round(curr_intensity - prev_intensity, 4)

            fid = f"{asp}_{sem.replace('-', '')}"
            rows.append(
                {
                    "friction_id": fid,
                    "aspect": asp,
                    "semester": sem,
                    "mention_count": stats["mention_count"],
                    "negative_count": stats["negative_count"],
                    "neutral_count": stats["neutral_count"],
                    "positive_count": stats["positive_count"],
                    "negative_rate": stats["negative_rate"],
                    "semester_intensity": curr_intensity,
                    "mean_intensity": mean_intensities[asp],
                    "delta_previous": delta,
                    "trend_direction": trend_directions[asp],
                    "aspect_weight": norm_weights[asp],
                }
            )

    friction_df = pd.DataFrame(rows)

    # Tipagem estrita
    friction_df["friction_id"] = friction_df["friction_id"].astype(str)
    friction_df["aspect"] = friction_df["aspect"].astype(str)
    friction_df["semester"] = friction_df["semester"].astype(str)
    friction_df["mention_count"] = friction_df["mention_count"].astype(int)
    friction_df["negative_count"] = friction_df["negative_count"].astype(int)
    friction_df["neutral_count"] = friction_df["neutral_count"].astype(int)
    friction_df["positive_count"] = friction_df["positive_count"].astype(int)
    friction_df["negative_rate"] = friction_df["negative_rate"].astype(float)
    friction_df["semester_intensity"] = friction_df["semester_intensity"].astype(float)
    friction_df["mean_intensity"] = friction_df["mean_intensity"].astype(float)
    friction_df["delta_previous"] = friction_df["delta_previous"].astype(float)
    friction_df["trend_direction"] = friction_df["trend_direction"].astype(str)
    friction_df["aspect_weight"] = friction_df["aspect_weight"].astype(float)

    # 5. Estruturação do JSON para WS2 com metadados auto-descritivos
    weights_json: dict[str, Any] = {
        "_meta": {
            "title": "Azul Fidelidade - Friction Aspect Weights (WS2 / WS6)",
            "description": (
                "Pesos calibrados de atrito por aspecto para o gerador sintético (WS2, hazard de evasão) "
                "e contexto de causas de churn para o agente (WS7)."
            ),
            "version": "1.0",
            "generated_at": dt.datetime.now(dt.UTC).isoformat(),
            "source": "ml/sentiment/friction_map.py (processamento do corpus sintético rotulado)",
            "methodology": (
                "Intensidade semestral combinando severidade de sentimento negativo e prevalência de menções, "
                "normalizada ao longo da janela sintética de 36 meses."
            ),
            "synthetic_honesty_statement": (
                "Pesos calibrados a partir de corpus SINTÉTICO PT-BR rotulado. Validam o pipeline e "
                "a integração entre frentes de trabalho; não medem prevalência empírica no mundo real."
            ),
            "normalization": "Soma de todos os aspect_weights = 1.0",
            "aspects": ASPECTS,
        },
        "weights": norm_weights,
        "aspect_stats": {
            asp: {
                "mean_intensity": mean_intensities[asp],
                "trend_direction": trend_directions[asp],
                "total_mentions": total_mentions_by_aspect[asp],
                "total_negative_mentions": total_neg_by_aspect[asp],
                "negative_share": round(
                    total_neg_by_aspect[asp] / max(1, total_mentions_by_aspect[asp]),
                    4,
                ),
                "weight": norm_weights[asp],
            }
            for asp in ASPECTS
        },
    }

    return friction_df, weights_json


def save_friction_outputs(
    friction_df: pd.DataFrame,
    weights_json: dict[str, Any],
    parquet_out: str | Path | None = None,
    json_out: str | Path | None = None,
) -> tuple[Path, Path]:
    """Salva os artefatos nos caminhos definidos e valida contra o contrato schemas/friction_map.yaml.

    Args:
        friction_df: DataFrame com o mapa analítico de atritos.
        weights_json: Dicionário contendo os pesos e metadados.
        parquet_out: Caminho do arquivo Parquet (default: data/analytics/friction_map.parquet).
        json_out: Caminho do arquivo JSON (default: data/curated/friction_weights.json).

    Returns:
        Tupla com os Paths absolutos dos arquivos salvos.
    """
    p_parquet = path(parquet_out or "data/analytics/friction_map.parquet")
    p_json = path(json_out or "data/curated/friction_weights.json")

    ensure_dir(p_parquet.parent)
    ensure_dir(p_json.parent)

    # 1. Grava Parquet
    friction_df.to_parquet(p_parquet, index=False)
    logger.info("Gravou Parquet em %s", p_parquet)

    # 2. Valida contra contrato
    contract = load_contract("friction_map")
    validate_or_raise(contract, p_parquet)
    logger.info("Contrato de friction_map validado com sucesso.")

    # 3. Grava JSON
    with open(p_json, "w", encoding="utf-8") as f:
        json.dump(weights_json, f, indent=2, ensure_ascii=False)
    logger.info("Gravou JSON de pesos em %s", p_json)

    return p_parquet, p_json


def main() -> int:
    """Executa o cálculo do mapa de atritos a partir do Parquet de avaliações."""
    target_reviews = path("data/curated/sentiment_reviews.parquet")

    if not target_reviews.exists():
        raise FileNotFoundError(
            f"Arquivo de avaliações não encontrado em {target_reviews}. Execute ml.sentiment.corpus primeiro!"
        )

    df_reviews = pd.read_parquet(target_reviews)
    friction_df, weights_json = compute_friction_map(df_reviews)
    p_parquet, p_json = save_friction_outputs(friction_df, weights_json)

    print(f"Mapa de atritos gerado: {p_parquet} ({len(friction_df)} linhas)")
    print(f"Pesos de atrito gravados: {p_json}")
    print("\nPesos por Aspecto (WS2):")
    for asp, w in weights_json["weights"].items():
        trend = weights_json["aspect_stats"][asp]["trend_direction"]
        print(f"  - {asp:<16}: {w:.4f} (tendência: {trend})")

    return 0


if __name__ == "__main__":
    main()
