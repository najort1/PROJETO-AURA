"""Orquestrador do pipeline de segmentação, ScoreAV, personas e timeline (WS5).

Executado via:
    python tasks.py score
    ou
    python -m ml.segmentation.train

Etapas ordenadas:
1. Clusterização KMeans + GMM -> data/analytics/segments.parquet
2. Sumarização das Personas e Perfis -> personas_summary.parquet, personas_profiles.json
3. Score de Alto Valor e Visão Consolidada -> score_av.parquet, customers_scores.parquet
4. Linha do Tempo de Relacionamento -> customer_timeline.parquet
5. Contrato de Entrada do Agente -> agent_input.parquet
"""

from __future__ import annotations

from pathlib import Path

from ml.segmentation.agent_input import run_agent_input_pipeline
from ml.segmentation.cluster import run_clustering_pipeline
from ml.segmentation.personas import run_personas_pipeline
from ml.segmentation.score_av import run_score_pipeline
from ml.segmentation.timeline import run_timeline_pipeline


def train_segmentation(output_dir: Path | None = None) -> None:
    """Executa o pipeline completo de segmentação de ponta a ponta."""
    print("=" * 70)
    print("=== WS5 :: PIPELINE DE SEGMENTAÇÃO E SCORE DE ALTO VALOR ===")
    print("=" * 70)

    # 1. Clusterização
    print("\n[1/5] Executando clusterização comportamental (KMeans + GMM)...")
    run_clustering_pipeline(output_dir=output_dir)

    # 2. Personas
    print("\n[2/5] Consolidando resumo e perfis quantitativos das personas...")
    run_personas_pipeline(output_dir=output_dir)

    # 3. ScoreAV e customers_scores
    print("\n[3/5] Calculando ScoreAV canônico e construindo customers_scores...")
    run_score_pipeline(output_dir=output_dir)

    # 4. Timeline
    print("\n[4/5] Gerando histórico de eventos da linha do tempo (customer_timeline)...")
    run_timeline_pipeline(output_dir=output_dir)

    # 5. Agent Input
    print("\n[5/5] Construindo contrato de entrada do agente (agent_input)...")
    run_agent_input_pipeline(output_dir=output_dir)

    print("\n" + "=" * 70)
    print("=== PIPELINE WS5 (SCORE/SEGMENTAÇÃO) CONCLUÍDO COM SUCESSO ===")
    print("=" * 70)


if __name__ == "__main__":
    train_segmentation()
