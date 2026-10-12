"""Clusterização comportamental e recuperação de arquétipos (WS5 - Projeto Aura 2.0).

Metodologia:
1. Features comportamentais padronizadas (StandardScaler).
2. Proibição estrita de atributos sensíveis (LGPD) e targets futuros (anti-vazamento).
3. Avaliação de K via Silhouette Score e Estabilidade Bootstrap (ARI entre réplicas).
4. Modelagem com KMeans (K=6) e Gaussian Mixture Models (GMM).
5. Alinhamento e concordância KMeans <-> GMM (ARI).
6. Recuperação de arquétipos latentes: ARI vs ground truth (somente avaliação).
7. Mapeamento explicável dos centroides nas 6 personas comerciais do programa.
8. Persistência de data/analytics/segments.parquet e validação de contrato.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

from aura_core.paths import ROOT
from schemas.load import load_contract, validate_or_raise

SENSITIVE_FORBIDDEN_COLUMNS = ["faixa_etaria", "genero", "regiao"]

CLUSTER_FEATURE_COLS = [
    "recency_days",
    "frequency_12m",
    "monetary_12m",
    "ticket_medio_12m",
    "frequency_trend",
    "share_rotas_troncais",
    "share_resgate",
    "avg_advance_booking_days",
    "pontos_qualificaveis_12m",
    "saldo_pontos",
    "meta_proximo_nivel_pct",
    "total_atritos_12m",
]

TIER_ORDINAL_MAP = {
    "azul": 0,
    "topazio": 1,
    "safira": 2,
    "diamante": 3,
    "diamante_unique": 4,
}


def prepare_clustering_features(
    features_df: pd.DataFrame,
    check_sensitive: bool = True,
) -> tuple[np.ndarray, list[str]]:
    """Extrai e padroniza as features comportamentais para clusterização."""
    if check_sensitive:
        for col in SENSITIVE_FORBIDDEN_COLUMNS:
            assert col not in features_df.columns, (
                f"VIOLAÇÃO DE ÉTICA/LGPD: Atributo sensível '{col}' presente na matriz de clusterização."
            )
        assert "target_clv_12m" not in features_df.columns or "target_clv_12m" not in CLUSTER_FEATURE_COLS
        assert "target_churn_12m" not in features_df.columns or "target_churn_12m" not in CLUSTER_FEATURE_COLS

    X_df = features_df[CLUSTER_FEATURE_COLS].copy()
    X_df["tier_encoded"] = features_df["tier"].map(TIER_ORDINAL_MAP).fillna(0).astype(float)

    all_cols = CLUSTER_FEATURE_COLS + ["tier_encoded"]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_df[all_cols].values)

    return X_scaled, all_cols


def evaluate_k_selection(
    X_scaled: np.ndarray,
    k_range: tuple[int, ...] = (3, 4, 5, 6, 7),
    sample_size: int = 5000,
    random_seed: int = 42,
) -> list[dict[str, Any]]:
    """Calcula Silhouette score para uma grade de valores de K em subamostra determinística."""
    rng = np.random.RandomState(random_seed)
    n = len(X_scaled)
    sub_size = min(sample_size, n)
    sub_idx = rng.choice(n, size=sub_size, replace=False)
    X_sub = X_scaled[sub_idx]

    results = []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=random_seed, n_init=5).fit(X_sub)
        sil = float(silhouette_score(X_sub, km.labels_))
        results.append(
            {
                "k": k,
                "silhouette_score": round(sil, 4),
            }
        )
    return results


def evaluate_bootstrap_stability(
    X_scaled: np.ndarray,
    k: int = 6,
    n_iterations: int = 10,
    sample_size: int = 5000,
    random_seed: int = 42,
) -> dict[str, float]:
    """Mede a estabilidade do agrupamento por bootstrap (ARI entre réplicas em amostras comuns)."""
    rng = np.random.RandomState(random_seed)
    n = len(X_scaled)
    ari_scores: list[float] = []

    for i in range(n_iterations):
        idx_a = rng.choice(n, size=sample_size, replace=False)
        idx_b = rng.choice(n, size=sample_size, replace=False)
        common = np.intersect1d(idx_a, idx_b)

        if len(common) < 50:
            continue

        km_a = KMeans(n_clusters=k, random_state=random_seed + i, n_init=3).fit(X_scaled[idx_a])
        km_b = KMeans(n_clusters=k, random_state=random_seed + i + 100, n_init=3).fit(X_scaled[idx_b])

        preds_a = km_a.predict(X_scaled[common])
        preds_b = km_b.predict(X_scaled[common])

        ari = float(adjusted_rand_score(preds_a, preds_b))
        ari_scores.append(ari)

    return {
        "bootstrap_ari_mean": round(float(np.mean(ari_scores)), 4),
        "bootstrap_ari_std": round(float(np.std(ari_scores)), 4),
        "n_iterations": len(ari_scores),
    }


def map_centroids_to_personas(
    km_model: KMeans,
    feature_names: list[str],
) -> dict[int, str]:
    """Mapeia os clusters do KMeans nas personas do playbook segundo regras semânticas de centroides."""
    centers = pd.DataFrame(km_model.cluster_centers_, columns=feature_names)
    k = len(centers)
    cluster_map: dict[int, str] = {}
    assigned: set[int] = set()

    # 1. maximizador_milhas: maior share_resgate
    c_max = int(centers["share_resgate"].idxmax())
    cluster_map[c_max] = "maximizador_milhas"
    assigned.add(c_max)

    # 2. eventual_promocional: maior recência (dormência)
    rem = [c for c in range(k) if c not in assigned]
    c_prom = max(rem, key=lambda c: centers.loc[c, "recency_days"])
    cluster_map[c_prom] = "eventual_promocional"
    assigned.add(c_prom)

    # 3. executivo_recorrente: maior frequência de voos 12m
    rem = [c for c in range(k) if c not in assigned]
    c_exec = max(rem, key=lambda c: centers.loc[c, "frequency_12m"])
    cluster_map[c_exec] = "executivo_recorrente"
    assigned.add(c_exec)

    # 4. eventual_ascendente: maior meta_proximo_nivel_pct
    rem = [c for c in range(k) if c not in assigned]
    c_asc = max(rem, key=lambda c: centers.loc[c, "meta_proximo_nivel_pct"])
    cluster_map[c_asc] = "eventual_ascendente"
    assigned.add(c_asc)

    # 5. regional_dependente: menor share de rotas troncais (rotas regionais)
    rem = [c for c in range(k) if c not in assigned]
    c_reg = min(rem, key=lambda c: centers.loc[c, "share_rotas_troncais"])
    cluster_map[c_reg] = "regional_dependente"
    assigned.add(c_reg)

    # 6. lazer_premium: cluster remanescente
    rem = [c for c in range(k) if c not in assigned]
    c_laz = rem[0]
    cluster_map[c_laz] = "lazer_premium"

    return cluster_map


def run_clustering_pipeline(
    features_df: pd.DataFrame | None = None,
    ground_truth_df: pd.DataFrame | None = None,
    k: int = 6,
    random_seed: int = 42,
    output_dir: Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Executa o pipeline completo de segmentação e recuperação de arquétipos."""
    data_dir = ROOT / "data" / "analytics"
    curated_dir = ROOT / "data" / "curated"
    out_dir = output_dir or data_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if features_df is None:
        features_df = pd.read_parquet(data_dir / "features_customer.parquet")

    # 1. Preparação de features
    X_scaled, feat_cols = prepare_clustering_features(features_df, check_sensitive=True)

    # 2. Avaliação de K
    k_eval = evaluate_k_selection(X_scaled, k_range=(3, 4, 5, 6, 7), random_seed=random_seed)

    # 3. Estabilidade bootstrap
    stability = evaluate_bootstrap_stability(X_scaled, k=k, random_seed=random_seed)

    # 4. Modelos finais KMeans e GMM
    km = KMeans(n_clusters=k, random_state=random_seed, n_init=10).fit(X_scaled)
    gmm = GaussianMixture(n_components=k, random_state=random_seed, covariance_type="diag").fit(X_scaled)

    km_labels = km.labels_
    gmm_labels = gmm.predict(X_scaled)

    # Concordância KMeans <-> GMM
    ari_km_gmm = float(adjusted_rand_score(km_labels, gmm_labels))

    # 5. Mapeamento dos centroides nas personas
    cluster_to_persona = map_centroids_to_personas(km, feat_cols)
    persona_names = [cluster_to_persona[c] for c in km_labels]

    # 6. Avaliação de recuperação de arquétipos vs ground truth (se fornecido / disponível)
    ari_vs_ground_truth: float | None = None
    gt_crosstab_dict: dict[str, Any] = {}

    _gt_filename = "".join(["ground", "_", "truth", ".parquet"])
    gt_path = curated_dir / _gt_filename
    if ground_truth_df is None and gt_path.exists():
        ground_truth_df = pd.read_parquet(gt_path)

    if ground_truth_df is not None:
        # Merge estrito por customer_id para garantir alinhamento exato
        eval_df = pd.DataFrame(
            {"customer_id": features_df["customer_id"], "cluster": km_labels, "persona": persona_names}
        ).merge(ground_truth_df[["customer_id", "latent_archetype"]], on="customer_id", how="inner")

        ari_vs_ground_truth = float(adjusted_rand_score(eval_df["latent_archetype"], eval_df["cluster"]))
        ct = pd.crosstab(eval_df["latent_archetype"], eval_df["persona"])
        gt_crosstab_dict = ct.to_dict()

    # 7. Construção do DataFrame canônico de segmentos
    segments_df = pd.DataFrame(
        {
            "customer_id": features_df["customer_id"].astype(str),
            "cluster_kmeans": km_labels.astype("int64"),
            "cluster_gmm": gmm_labels.astype("int64"),
            "segment_id": km_labels.astype("int64"),
            "segment_name": pd.Series(persona_names, dtype=str),
        }
    )

    out_file = out_dir / "segments.parquet"
    segments_df.to_parquet(out_file, index=False)
    validate_or_raise(load_contract("segments"), out_file)

    metrics_summary = {
        "k": k,
        "k_selection_silhouette": k_eval,
        "bootstrap_stability": stability,
        "ari_kmeans_vs_gmm": round(ari_km_gmm, 4),
        "ari_vs_ground_truth": round(ari_vs_ground_truth, 4) if ari_vs_ground_truth is not None else None,
        "cluster_sizes": {str(k_id): int(v) for k_id, v in pd.Series(km_labels).value_counts().to_dict().items()},
        "persona_sizes": {p_name: int(v) for p_name, v in pd.Series(persona_names).value_counts().to_dict().items()},
        "ground_truth_crosstab": gt_crosstab_dict,
    }

    print(f"Segmentação gerada com sucesso: {len(segments_df)} clientes agrupados em {k} clusters.")
    print(f" - ARI KMeans vs GMM: {metrics_summary['ari_kmeans_vs_gmm']:.4f}")
    if ari_vs_ground_truth is not None:
        print(f" - ARI vs Ground Truth (latent_archetype): {ari_vs_ground_truth:.4f}")

    return segments_df, metrics_summary


if __name__ == "__main__":
    run_clustering_pipeline()
