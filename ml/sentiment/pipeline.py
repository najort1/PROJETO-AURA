"""Pipeline ponta a ponta de Análise de Sentimento por Aspecto (WS6).

Orquestra:
1. Geração e validação do corpus sintético rotulado (sentiment_reviews.parquet)
2. Treinamento e avaliação comparativa (Lexicon vs TF-IDF + LogisticRegression)
3. Cálculo do mapa analítico de atritos (friction_map.parquet)
4. Exportação dos pesos de atrito calibrados (friction_weights.json)

Executado via:
    python -m ml.sentiment.pipeline
    python tasks.py sentiment
"""

from __future__ import annotations

import sys
from typing import Any

from aura_core.log import get_logger
from ml.sentiment.approaches import run_evaluation
from ml.sentiment.corpus import generate_corpus, save_corpus
from ml.sentiment.friction_map import compute_friction_map, save_friction_outputs

logger = get_logger("sentiment.pipeline")


def run_sentiment_pipeline() -> dict[str, Any]:
    """Executa o pipeline completo de ponta a ponta."""
    logger.info("=== INICIANDO PIPELINE DE SENTIMENTO E ATRITOS (WS6) ===")

    # 1. Corpus sintético
    logger.info("[Etapa 1/3] Gerando e validando corpus sintético PT-BR...")
    df_corpus = generate_corpus()
    corpus_path = save_corpus(df_corpus)
    logger.info("Corpus salvo e validado em: %s", corpus_path)

    # 2. Avaliação comparativa das abordagens de NLP
    logger.info(
        "[Etapa 2/3] Avaliando abordagens (Lexicon vs TF-IDF + LogReg) em holdout temporal..."
    )
    eval_results = run_evaluation(df_corpus)
    comp = eval_results["comparison"]
    logger.info(
        "Avaliação concluída. Macro-F1 Lexicon: %.4f | Macro-F1 TF-IDF: %.4f | Vencedor: %s",
        comp["global_lexicon_macro_f1"],
        comp["global_tfidf_macro_f1"],
        comp["overall_winner"],
    )

    # 3. Mapa analítico de atritos e pesos para WS2
    logger.info("[Etapa 3/3] Calculando mapa de atritos e pesos calibrados para WS2...")
    friction_df, weights_json = compute_friction_map(df_corpus)
    p_parquet, p_json = save_friction_outputs(friction_df, weights_json)
    logger.info("Mapa de atritos gravado em: %s", p_parquet)
    logger.info("Pesos de atrito gravados em: %s", p_json)

    logger.info("=== PIPELINE DE SENTIMENTO CONCLUÍDO COM SUCESSO ===")

    return {
        "corpus_path": str(corpus_path),
        "friction_parquet_path": str(p_parquet),
        "friction_json_path": str(p_json),
        "eval_results": eval_results,
        "friction_weights": weights_json["weights"],
    }


def main() -> int:
    """Ponto de entrada do script."""
    try:
        results = run_sentiment_pipeline()
        comp = results["eval_results"]["comparison"]
        print("\n" + "=" * 65)
        print("PROJETO AURA 2.0 - WS6 SENTIMENTO E MAPA DE ATRITOS")
        print("=" * 65)
        print("Artefatos gerados:")
        print(f"  - Corpus:   {results['corpus_path']}")
        print(f"  - Mapa:     {results['friction_parquet_path']}")
        print(f"  - Pesos:    {results['friction_json_path']}")
        print("\nDesempenho no Holdout Temporal (Cutoff: 2025-08-31):")
        print(f"  - Lexicon Macro-F1:   {comp['global_lexicon_macro_f1']:.4f}")
        print(f"  - TF-IDF Macro-F1:    {comp['global_tfidf_macro_f1']:.4f}")
        print(
            f"  - Abordagem vencedora: {comp['overall_winner']} (Delta: {comp['delta_global']:+.4f})"
        )
        print(f"  - Kappa Inter-Abordagens (proxy): {comp['inter_approach_kappa']:.4f}")
        print("\nPesos de Atrito Calibrados para WS2 (hazard de evasão):")
        for asp, w in results["friction_weights"].items():
            print(f"  - {asp:<16}: {w:.4f}")
        print("=" * 65 + "\n")
        return 0
    except Exception as exc:
        logger.exception("Falha no pipeline de sentimento: %s", exc)
        print(f"ERRO CRÍTICO no pipeline de sentimento: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
