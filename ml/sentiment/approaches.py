"""Comparação de abordagens de NLP para análise de sentimento por aspecto (WS6).

Abordagens implementadas e comparadas:
1. Lexicon / regras PT-BR:
   - Dicionários de termos por aspecto
   - Léxico de sentimento com polaridades
   - Detecção de negações em janela contextual e intensificadores
   - Marcadores de ironia / sarcasmo
2. TF-IDF + LogisticRegression One-vs-Rest:
   - Extração combinada: word n-grams (1-2) + char_wb (3-5)
   - Regressão Logística por aspecto (sklearn, seed determinística)

Avaliação:
- Holdout temporal estratificado (treino <= cutoff, teste > cutoff)
- Métricas: Macro-F1 por aspecto e global, matrizes de confusão, precisão e revocação
- Proxy de concordância (Kappa) entre abordagens e ground truth
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Final

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.pipeline import FeatureUnion

from aura_core.config import child_seed, settings
from aura_core.log import get_logger
from aura_core.paths import path
from ml.sentiment.corpus import ASPECTS

logger = get_logger("sentiment.approaches")

# Termos-chave por aspecto para abordagem Lexicon
ASPECT_LEXICON: Final[dict[str, list[str]]] = {
    "atraso": [
        "atraso",
        "atrasou",
        "atrasar",
        "atrasaram",
        "atrasados",
        "decolagem",
        "decolar",
        "conexao",
        "horario",
        "espera",
        "esperando",
        "embarque",
        "pousou",
        "pouso",
        "pontual",
        "pontualidade",
        "pontualissimo",
        "cronograma",
        "remarcado",
        "remarcacao",
        "pista",
        "esperar",
    ],
    "bagagem": [
        "bagagem",
        "bagagens",
        "mala",
        "malas",
        "extravio",
        "extraviada",
        "extraviado",
        "extraviaram",
        "esteira",
        "despacho",
        "despachar",
        "despachada",
        "despachadas",
        "avaria",
        "avarias",
        "danificada",
        "quebrada",
        "alca",
        "ziper",
        "franquia",
        "pertences",
    ],
    "atendimento": [
        "atendimento",
        "atendente",
        "atendentes",
        "comissario",
        "comissarios",
        "comissaria",
        "tripulacao",
        "balcao",
        "sac",
        "suporte",
        "equipe",
        "funcionario",
        "funcionarios",
        "cordial",
        "educado",
        "educados",
        "grosseiro",
        "grosseiros",
        "rispido",
        "rispidos",
        "descaso",
        "empatia",
        "prestativo",
        "prestativa",
        "solicito",
        "solicita",
    ],
    "app_checkin": [
        "app",
        "aplicativo",
        "check-in",
        "checkin",
        "cartao de embarque",
        "login",
        "desloga",
        "trava",
        "travando",
        "travamento",
        "tela",
        "bug",
        "bugs",
        "sistema",
        "carteira digital",
        "online",
        "interface",
        "celular",
        "atualizacao",
    ],
    "resgate_milhas": [
        "milha",
        "milhas",
        "ponto",
        "pontos",
        "resgate",
        "resgatar",
        "tabela",
        "fidelidade",
        "saldo",
        "extrato",
        "expiraram",
        "expirar",
        "emissao",
        "emitir",
        "acumulo",
        "acumular",
        "acumulado",
        "superfaturada",
        "desvalorizacao",
    ],
    "preco": [
        "preco",
        "precos",
        "tarifa",
        "tarifas",
        "passagem",
        "passagens",
        "valor",
        "valores",
        "caro",
        "cara",
        "carissimo",
        "carissima",
        "custo",
        "custo-beneficio",
        "barato",
        "barata",
        "promocao",
        "promocional",
        "taxa",
        "taxas",
        "cobranca",
        "cobraram",
    ],
    "conforto": [
        "conforto",
        "confortavel",
        "desconforto",
        "desconfortavel",
        "poltrona",
        "poltronas",
        "assento",
        "assentos",
        "espaco",
        "perna",
        "pernas",
        "cabine",
        "reclinava",
        "reclinar",
        "aperto",
        "apertado",
        "ergonomica",
        "silenciosa",
        "acolchoamento",
        "fileira",
    ],
}

POSITIVE_WORDS: Final[set[str]] = {
    "excelente",
    "otimo",
    "otima",
    "otimos",
    "otimas",
    "bom",
    "boa",
    "bons",
    "boas",
    "pontual",
    "pontualissimo",
    "rapido",
    "rapida",
    "ageis",
    "agil",
    "intacta",
    "intacto",
    "educado",
    "educada",
    "cordial",
    "atencioso",
    "atenciosa",
    "fluido",
    "fluida",
    "intuitivo",
    "intuitiva",
    "vantajoso",
    "vantajosa",
    "justo",
    "justa",
    "confortavel",
    "espacoso",
    "espacosa",
    "limpo",
    "limpa",
    "maravilha",
    "maravilhoso",
    "show",
    "dez",
    "perfeito",
    "perfeita",
    "solicito",
    "prestativo",
    "moderno",
    "exemplar",
    "economico",
    "generoso",
}

NEGATIVE_WORDS: Final[set[str]] = {
    "pessimo",
    "pessima",
    "horrivel",
    "ruim",
    "atraso",
    "atrasou",
    "absurdo",
    "absurda",
    "descaso",
    "grosseiro",
    "grosseira",
    "rispido",
    "rispida",
    "extraviada",
    "extraviado",
    "quebrada",
    "quebrado",
    "trava",
    "travou",
    "travando",
    "lenta",
    "lento",
    "caro",
    "cara",
    "carissimo",
    "inflacionada",
    "dura",
    "duro",
    "estreito",
    "aperto",
    "dor",
    "falha",
    "fiasco",
    "perrengue",
    "prejuizo",
    "caiu",
    "despreparado",
    "despreparados",
    "superfaturada",
    "abusiva",
    "abusivo",
    "proibitivo",
    "desconfortavel",
    "transtorno",
}

NEGATIONS: Final[set[str]] = {
    "nao",
    "n",
    "nunca",
    "jamais",
    "sem",
    "nem",
    "pouco",
    "poucos",
}

INTENSIFIERS: Final[set[str]] = {
    "muito",
    "mt",
    "demais",
    "super",
    "extremamente",
    "totalmente",
    "completamente",
    "pura",
    "puro",
    "drastico",
}

IRONY_MARKERS: Final[list[str]] = [
    "sqn",
    "so que nao",
    "so que n",
    "parabens pela",
    "parabens pelo",
    "parabens aos",
    "maravilha sqn",
    "otimo servico, sqn",
]


def _normalize_text(text: str) -> str:
    """Normaliza o texto removendo acentos e convertendo para minúsculas."""
    text_lower = text.lower()
    nfkd = unicodedata.normalize("NFKD", text_lower)
    ascii_text = "".join([c for c in nfkd if not unicodedata.combining(c)])
    # Mantém apenas caracteres alfanuméricos e espaços para tokenização
    clean = re.sub(r"[^\w\s-]", " ", ascii_text)
    return clean


class LexiconSentimentApproach:
    """Classificador baseado em regras e léxico PT-BR para detecção de aspecto e polaridade."""

    def __init__(self) -> None:
        self.aspects = ASPECTS

    def _is_ironic(self, text: str) -> bool:
        norm = _normalize_text(text)
        return any(marker in norm for marker in IRONY_MARKERS)

    def _score_tokens(self, tokens: list[str]) -> float:
        """Calcula o score de polaridade com negação e intensificadores."""
        score = 0.0
        for i, token in enumerate(tokens):
            weight = 1.0
            # Checa intensificador anterior
            if i > 0 and tokens[i - 1] in INTENSIFIERS:
                weight = 1.8

            # Checa negação na janela de até 3 tokens anteriores
            negated = False
            for lookback in range(max(0, i - 3), i):
                if tokens[lookback] in NEGATIONS:
                    negated = True
                    break

            val = 0.0
            if token in POSITIVE_WORDS:
                val = 1.0 * weight
            elif token in NEGATIVE_WORDS:
                val = -1.0 * weight

            if negated:
                val = -val * 0.9

            score += val
        return score

    def predict_single(self, text: str) -> dict[str, Any]:
        """Classifica uma única avaliação."""
        norm = _normalize_text(text)
        tokens = norm.split()
        ironic = self._is_ironic(text)

        result: dict[str, Any] = {"is_ironic": ironic}
        aspects_found: list[str] = []

        for aspect in self.aspects:
            keywords = ASPECT_LEXICON[aspect]
            # Verifica se alguma palavra-chave do aspecto está no texto
            matched = any(kw in norm for kw in keywords)
            if matched:
                result[f"has_{aspect}"] = 1
                aspects_found.append(aspect)

                # Avalia polaridade local
                # Encontra sentenças ou janelas que contenham a palavra-chave
                score = self._score_tokens(tokens)
                if ironic:
                    pol = "negativo"
                elif score > 0.4:
                    pol = "positivo"
                elif score < -0.4:
                    pol = "negativo"
                else:
                    pol = "neutro"
                result[f"polarity_{aspect}"] = pol
            else:
                result[f"has_{aspect}"] = 0
                result[f"polarity_{aspect}"] = "ausente"

        # Sentimento geral
        neg_count = sum(1 for a in aspects_found if result[f"polarity_{a}"] == "negativo")
        pos_count = sum(1 for a in aspects_found if result[f"polarity_{a}"] == "positivo")
        if ironic or neg_count > pos_count:
            result["overall_sentiment"] = "negativo"
        elif pos_count > neg_count:
            result["overall_sentiment"] = "positivo"
        else:
            result["overall_sentiment"] = "neutro"

        result["aspects_mentioned"] = ",".join(aspects_found)
        return result

    def predict(self, texts: list[str] | pd.Series) -> pd.DataFrame:
        """Classifica uma lista de textos e retorna DataFrame de predições."""
        records = [self.predict_single(t) for t in texts]
        return pd.DataFrame(records)


class TfidfLogisticApproach:
    """Classificador baseado em TF-IDF (word 1-2g + char_wb 3-5g) + Logistic Regression One-vs-Rest."""

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.aspects = ASPECTS

        # Pipeline de vetorização: word n-grams (1, 2) + char_wb (3, 5)
        self.vectorizer = FeatureUnion(
            [
                (
                    "word",
                    TfidfVectorizer(
                        ngram_range=(1, 2),
                        min_df=2,
                        sublinear_tf=True,
                    ),
                ),
                (
                    "char",
                    TfidfVectorizer(
                        analyzer="char_wb",
                        ngram_range=(3, 5),
                        min_df=2,
                        sublinear_tf=True,
                    ),
                ),
            ]
        )

        self.aspect_presence_models: dict[str, LogisticRegression] = {}
        self.aspect_polarity_models: dict[str, LogisticRegression] = {}
        self.overall_model: LogisticRegression | None = None
        self.is_fitted = False

    def fit(self, texts: list[str] | pd.Series, train_df: pd.DataFrame) -> TfidfLogisticApproach:
        """Ajusta os modelos TF-IDF e LogisticRegression nos dados de treino."""
        logger.info("Ajustando vetorizador TF-IDF (word 1-2 + char_wb 3-5)...")
        X = self.vectorizer.fit_transform(texts)

        logger.info("Treinando modelos Logistic Regression One-vs-Rest por aspecto...")
        for aspect in self.aspects:
            # Modelo de presenca binaria
            y_pres = train_df[f"has_{aspect}"].values
            clf_pres = LogisticRegression(
                random_state=self.seed,
                max_iter=1000,
                class_weight="balanced",
                solver="lbfgs",
            )
            clf_pres.fit(X, y_pres)
            self.aspect_presence_models[aspect] = clf_pres

            # Modelo de polaridade (4 classes: ausente, negativo, neutro, positivo)
            y_pol = train_df[f"polarity_{aspect}"].values
            clf_pol = LogisticRegression(
                random_state=self.seed,
                max_iter=1000,
                class_weight="balanced",
                solver="lbfgs",
            )
            clf_pol.fit(X, y_pol)
            self.aspect_polarity_models[aspect] = clf_pol

        # Modelo de sentimento geral
        y_overall = train_df["overall_sentiment"].values
        clf_overall = LogisticRegression(
            random_state=self.seed,
            max_iter=1000,
            class_weight="balanced",
            solver="lbfgs",
        )
        clf_overall.fit(X, y_overall)
        self.overall_model = clf_overall

        self.is_fitted = True
        logger.info("Treinamento TF-IDF + LogisticRegression concluído com sucesso.")
        return self

    def predict(self, texts: list[str] | pd.Series) -> pd.DataFrame:
        """Gera predições para uma lista de textos."""
        if not self.is_fitted:
            raise RuntimeError("O modelo TfidfLogisticApproach deve ser treinado antes de predict.")

        X = self.vectorizer.transform(texts)
        records: list[dict[str, Any]] = []

        n_samples = X.shape[0]
        pres_preds: dict[str, np.ndarray] = {}
        pol_preds: dict[str, np.ndarray] = {}

        for aspect in self.aspects:
            pres_preds[aspect] = self.aspect_presence_models[aspect].predict(X)
            pol_preds[aspect] = self.aspect_polarity_models[aspect].predict(X)

        assert self.overall_model is not None
        overall_pred = self.overall_model.predict(X)

        for i in range(n_samples):
            row: dict[str, Any] = {}
            aspects_found: list[str] = []

            for aspect in self.aspects:
                has_val = int(pres_preds[aspect][i])
                pol_val = str(pol_preds[aspect][i])

                # Harmonização: se pres_val == 1 mas pol_val == 'ausente', seleciona a polaridade
                # dominante de atrito (negativo) — com WARNING explícito (nunca silencioso).
                if has_val == 1 and pol_val == "ausente":
                    logger.warning(
                        "Polaridade 'ausente' com presença=1 para aspecto '%s' (amostra %d): "
                        "aplicando fallback 'negativo' de atrito.",
                        aspect,
                        i,
                    )
                    pol_val = "negativo"  # fallback de polaridade mais provável para atrito
                elif has_val == 0:
                    pol_val = "ausente"

                row[f"has_{aspect}"] = has_val
                row[f"polarity_{aspect}"] = pol_val
                if has_val == 1:
                    aspects_found.append(aspect)

            row["aspects_mentioned"] = ",".join(aspects_found)
            row["overall_sentiment"] = str(overall_pred[i])
            records.append(row)

        return pd.DataFrame(records)


def evaluate_approach(
    y_true_df: pd.DataFrame,
    y_pred_df: pd.DataFrame,
    approach_name: str,
) -> dict[str, Any]:
    """Calcula métricas rigorosas de desempenho: macro-F1, matriz de confusão, precisão, revocação."""
    results: dict[str, Any] = {
        "approach_name": approach_name,
        "n_samples": len(y_true_df),
        "aspect_metrics": {},
    }

    f1_list: list[float] = []

    for aspect in ASPECTS:
        y_true_pres = y_true_df[f"has_{aspect}"].values
        y_pred_pres = y_pred_df[f"has_{aspect}"].values

        p_pres = float(precision_score(y_true_pres, y_pred_pres, zero_division=0))
        r_pres = float(recall_score(y_true_pres, y_pred_pres, zero_division=0))
        f1_pres = float(f1_score(y_true_pres, y_pred_pres, zero_division=0))
        cm_pres = confusion_matrix(y_true_pres, y_pred_pres, labels=[0, 1]).tolist()

        f1_list.append(f1_pres)

        # Métricas de polaridade para esse aspecto (macro-F1 sobre 4 classes)
        y_true_pol = y_true_df[f"polarity_{aspect}"].astype(str).values
        y_pred_pol = y_pred_df[f"polarity_{aspect}"].astype(str).values
        labels_pol = ["ausente", "negativo", "neutro", "positivo"]
        f1_pol = float(
            f1_score(y_true_pol, y_pred_pol, labels=labels_pol, average="macro", zero_division=0)
        )
        cm_pol = confusion_matrix(y_true_pol, y_pred_pol, labels=labels_pol).tolist()

        results["aspect_metrics"][aspect] = {
            "presence_precision": p_pres,
            "presence_recall": r_pres,
            "presence_f1": f1_pres,
            "confusion_matrix_presence": cm_pres,
            "polarity_macro_f1": f1_pol,
            "confusion_matrix_polarity": cm_pol,
        }

    # Macro-F1 global de presença de aspectos
    results["global_aspect_macro_f1"] = float(np.mean(f1_list))

    # Sentimento geral
    y_true_ov = y_true_df["overall_sentiment"].astype(str).values
    y_pred_ov = y_pred_df["overall_sentiment"].astype(str).values
    ov_labels = ["negativo", "neutro", "positivo"]
    results["overall_macro_f1"] = float(
        f1_score(y_true_ov, y_pred_ov, labels=ov_labels, average="macro", zero_division=0)
    )
    results["overall_precision"] = float(
        precision_score(y_true_ov, y_pred_ov, labels=ov_labels, average="macro", zero_division=0)
    )
    results["overall_recall"] = float(
        recall_score(y_true_ov, y_pred_ov, labels=ov_labels, average="macro", zero_division=0)
    )
    results["overall_confusion_matrix"] = confusion_matrix(
        y_true_ov, y_pred_ov, labels=ov_labels
    ).tolist()

    # Kappa de Cohen vs Ground Truth (proxy de concordancia)
    results["kappa_vs_ground_truth"] = float(cohen_kappa_score(y_true_ov, y_pred_ov))

    return results


def compare_approaches(
    eval_lexicon: dict[str, Any],
    eval_tfidf: dict[str, Any],
    y_pred_lex: pd.DataFrame,
    y_pred_tfidf: pd.DataFrame,
) -> dict[str, Any]:
    """Compara as duas abordagens, mede o Kappa inter-abordagens e indica o vencedor."""
    # Kappa inter-abordagens (concordância entre as abordagens como proxy de anotadores)
    inter_kappa = float(
        cohen_kappa_score(
            y_pred_lex["overall_sentiment"].astype(str).values,
            y_pred_tfidf["overall_sentiment"].astype(str).values,
        )
    )

    comparison_table: list[dict[str, Any]] = []
    lex_wins = 0
    tfidf_wins = 0

    for aspect in ASPECTS:
        lex_f1 = eval_lexicon["aspect_metrics"][aspect]["presence_f1"]
        tfidf_f1 = eval_tfidf["aspect_metrics"][aspect]["presence_f1"]
        delta = tfidf_f1 - lex_f1
        winner = "TF-IDF + LogReg" if tfidf_f1 >= lex_f1 else "Lexicon/Regras"
        if winner == "TF-IDF + LogReg":
            tfidf_wins += 1
        else:
            lex_wins += 1

        comparison_table.append(
            {
                "aspect": aspect,
                "lexicon_f1": round(lex_f1, 4),
                "tfidf_f1": round(tfidf_f1, 4),
                "delta_tfidf_minus_lex": round(delta, 4),
                "winner": winner,
            }
        )

    global_lex_f1 = eval_lexicon["global_aspect_macro_f1"]
    global_tfidf_f1 = eval_tfidf["global_aspect_macro_f1"]
    overall_winner = "TF-IDF + LogReg" if global_tfidf_f1 >= global_lex_f1 else "Lexicon/Regras"

    return {
        "comparison_table": comparison_table,
        "global_lexicon_macro_f1": round(global_lex_f1, 4),
        "global_tfidf_macro_f1": round(global_tfidf_f1, 4),
        "delta_global": round(global_tfidf_f1 - global_lex_f1, 4),
        "overall_winner": overall_winner,
        "inter_approach_kappa": round(inter_kappa, 4),
        "lex_aspect_wins": lex_wins,
        "tfidf_aspect_wins": tfidf_wins,
    }


def run_evaluation(
    df: pd.DataFrame | None = None,
    cutoff_date: str = "2025-08-31",
) -> dict[str, Any]:
    """Executa a validação cruzada temporal comparando as duas abordagens.

    Args:
        df: DataFrame do corpus (se None, carrega de data/curated/sentiment_reviews.parquet).
        cutoff_date: Data de corte do holdout temporal (default: timeline.feature_cutoff).

    Returns:
        Dicionário com métricas completas e tabelas comparativas.
    """
    if df is None:
        reviews_path = path("data/curated/sentiment_reviews.parquet")
        df = pd.read_parquet(reviews_path)

    df["review_date"] = pd.to_datetime(df["review_date"], errors="raise")

    # Fail loud: datas nulas (NaT) jamais podem ser descartadas silenciosamente no split.
    n_nat = int(df["review_date"].isna().sum())
    if n_nat > 0:
        raise ValueError(
            f"{n_nat} datas nulas (NaT) no corpus — correção obrigatória antes do split."
        )

    # Normalização de fuso: tz-aware -> naive (comparação com cutoff naive).
    if getattr(df["review_date"].dt, "tz", None) is not None:
        df["review_date"] = df["review_date"].dt.tz_localize(None)

    # Holdout temporal: treino <= cutoff, teste > cutoff
    cutoff_ts = pd.to_datetime(f"{cutoff_date} 23:59:59")
    train_mask = df["review_date"] <= cutoff_ts
    test_mask = df["review_date"] > cutoff_ts

    # Assegura que o split cobre 100% das linhas (zero perda silenciosa).
    if int(train_mask.sum()) + int(test_mask.sum()) != len(df):
        raise AssertionError(
            f"Split temporal perdeu linhas: {int(train_mask.sum()) + int(test_mask.sum())} "
            f"de {len(df)} — investigar NaT/fuso antes de prosseguir."
        )

    train_df = df[train_mask].copy().reset_index(drop=True)
    test_df = df[test_mask].copy().reset_index(drop=True)

    logger.info(
        "Holdout temporal aplicado: Treino (%d amostras até %s) | Teste (%d amostras pós %s)",
        len(train_df),
        cutoff_date,
        len(test_df),
        cutoff_date,
    )

    if len(train_df) == 0 or len(test_df) == 0:
        raise ValueError("Divisão temporal resultou em conjunto de treino ou teste vazio!")

    # 1. Abordagem Lexicon
    logger.info("Executando abordagem 1: Lexicon/Regras PT-BR...")
    lex_approach = LexiconSentimentApproach()
    pred_lex_test = lex_approach.predict(test_df["text"])
    eval_lex = evaluate_approach(test_df, pred_lex_test, "Lexicon/Regras PT-BR")

    # 2. Abordagem TF-IDF + LogisticRegression
    logger.info("Executando abordagem 2: TF-IDF + Logistic Regression...")
    seed = child_seed(settings().get("seed", 42), "sentiment_models")
    tfidf_approach = TfidfLogisticApproach(seed=seed)
    tfidf_approach.fit(train_df["text"], train_df)
    pred_tfidf_test = tfidf_approach.predict(test_df["text"])
    eval_tfidf = evaluate_approach(test_df, pred_tfidf_test, "TF-IDF + Logistic Regression")

    # 3. Comparação direta
    comparison = compare_approaches(eval_lex, eval_tfidf, pred_lex_test, pred_tfidf_test)

    return {
        "cutoff_date": cutoff_date,
        "n_train": len(train_df),
        "n_test": len(test_df),
        "lexicon_evaluation": eval_lex,
        "tfidf_evaluation": eval_tfidf,
        "comparison": comparison,
    }


def main() -> int:
    """Executa a avaliação e imprime o resumo de métricas no console."""
    results = run_evaluation()
    comp = results["comparison"]
    print("=== RESULTADOS DA AVALIAÇÃO DE SENTIMENTO (HOLDOUT TEMPORAL) ===")
    print(
        f"Treino: {results['n_train']} | Teste: {results['n_test']} (Cutoff: {results['cutoff_date']})"
    )
    print(f"Global Macro-F1 Lexicon: {comp['global_lexicon_macro_f1']:.4f}")
    print(f"Global Macro-F1 TF-IDF:  {comp['global_tfidf_macro_f1']:.4f}")
    print(f"Vencedor Global:         {comp['overall_winner']} (Delta: {comp['delta_global']:+.4f})")
    print(f"Kappa inter-abordagens:  {comp['inter_approach_kappa']:.4f}")
    print("\n--- Comparação por Aspecto (Macro-F1 Presença) ---")
    for row in comp["comparison_table"]:
        print(
            f"  {row['aspect']:<16}: Lexicon={row['lexicon_f1']:.4f} | TF-IDF={row['tfidf_f1']:.4f} | Vencedor={row['winner']}"
        )
    return 0


if __name__ == "__main__":
    main()
