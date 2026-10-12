"""Testes unitários e de integração para o pipeline de sentimento e atritos (WS6).

Cobre:
1. Determinismo do gerador de corpus (mesma seed -> mesmo hash/conteúdo)
2. Métricas corretas em fixture construída manualmente com rótulos conhecidos
3. Validação dos contratos de dados (sentiment_reviews.yaml e friction_map.yaml)
4. Falha alta (fail loud) quando o contrato de dados é violado
5. Pesos de atrito (friction_weights.json) dentro de faixas plausíveis
6. Execução e integridade da comparação de abordagens
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from aura_core.paths import path
from ml.sentiment.approaches import (
    LexiconSentimentApproach,
    evaluate_approach,
    run_evaluation,
)
from ml.sentiment.corpus import ASPECTS, generate_corpus, save_corpus
from ml.sentiment.friction_map import compute_friction_map, save_friction_outputs
from schemas.load import load_contract, validate_or_raise, validate_table


def test_corpus_determinism_same_seed() -> None:
    """Verifica que a mesma seed gera exatamente o mesmo DataFrame e o mesmo hash."""
    seed = 42109
    df1 = generate_corpus(n_reviews=60, seed=seed)
    df2 = generate_corpus(n_reviews=60, seed=seed)

    pd.testing.assert_frame_equal(df1, df2)

    # Verifica hash SHA-256 do texto concatenado
    text_concat_1 = "".join(df1["text"]).encode("utf-8")
    text_concat_2 = "".join(df2["text"]).encode("utf-8")
    hash1 = hashlib.sha256(text_concat_1).hexdigest()
    hash2 = hashlib.sha256(text_concat_2).hexdigest()

    assert hash1 == hash2, "Hashes de texto gerados com a mesma seed devem ser idênticos"


def test_corpus_different_seed() -> None:
    """Verifica que seeds distintas geram dados diferentes."""
    df1 = generate_corpus(n_reviews=40, seed=111)
    df2 = generate_corpus(n_reviews=40, seed=999)

    assert not df1["text"].equals(df2["text"]), "Seeds diferentes não podem gerar o mesmo texto"


def test_manual_fixture_metrics_exact_f1() -> None:
    """Valida o cálculo de F1 e matriz de confusão em fixture manual com valores exatos conhecidos."""
    # Fixture manual com 4 exemplos para o aspecto 'atraso':
    # y_true: [1, 1, 0, 0]
    # y_pred: [1, 0, 0, 1]
    # Matriz de confusão esperada:
    #   TN (y_true=0, y_pred=0) = 1
    #   FP (y_true=0, y_pred=1) = 1
    #   FN (y_true=1, y_pred=0) = 1
    #   TP (y_true=1, y_pred=1) = 1
    # Precision = TP / (TP + FP) = 1 / 2 = 0.5
    # Recall    = TP / (TP + FN) = 1 / 2 = 0.5
    # F1        = 2 * (0.5 * 0.5) / (0.5 + 0.5) = 0.5

    data_true = {
        "overall_sentiment": ["negativo", "negativo", "positivo", "positivo"],
    }
    data_pred = {
        "overall_sentiment": ["negativo", "positivo", "positivo", "negativo"],
    }

    for asp in ASPECTS:
        if asp == "atraso":
            data_true[f"has_{asp}"] = [1, 1, 0, 0]
            data_pred[f"has_{asp}"] = [1, 0, 0, 1]
            data_true[f"polarity_{asp}"] = ["negativo", "negativo", "ausente", "ausente"]
            data_pred[f"polarity_{asp}"] = ["negativo", "ausente", "ausente", "negativo"]
        else:
            data_true[f"has_{asp}"] = [0, 0, 0, 0]
            data_pred[f"has_{asp}"] = [0, 0, 0, 0]
            data_true[f"polarity_{asp}"] = ["ausente", "ausente", "ausente", "ausente"]
            data_pred[f"polarity_{asp}"] = ["ausente", "ausente", "ausente", "ausente"]

    df_true = pd.DataFrame(data_true)
    df_pred = pd.DataFrame(data_pred)

    results = evaluate_approach(df_true, df_pred, "FixtureManual")
    atraso_metrics = results["aspect_metrics"]["atraso"]

    assert atraso_metrics["presence_precision"] == pytest.approx(0.5, abs=1e-4)
    assert atraso_metrics["presence_recall"] == pytest.approx(0.5, abs=1e-4)
    assert atraso_metrics["presence_f1"] == pytest.approx(0.5, abs=1e-4)
    assert atraso_metrics["confusion_matrix_presence"] == [[1, 1], [1, 1]]


def test_lexicon_approach_on_manual_fixture() -> None:
    """Testa a abordagem de Lexicon em 4 textos construídos manualmente com rótulos esperados."""
    manual_texts = [
        "Voo com mais de 3 horas de atraso na conexao, absurdo total.",  # atraso (neg)
        "Comissarios super atenciosos e educados durante o voo, nota dez.",  # atendimento (pos)
        "Minha mala foi extraviada na esteira e chegou danificada.",  # bagagem (neg)
        "Aplicativo muito rapido e check-in digital fluido sem travar.",  # app_checkin (pos)
    ]

    clf = LexiconSentimentApproach()
    pred_df = clf.predict(manual_texts)

    assert pred_df.loc[0, "has_atraso"] == 1
    assert pred_df.loc[0, "polarity_atraso"] == "negativo"

    assert pred_df.loc[1, "has_atendimento"] == 1
    assert pred_df.loc[1, "polarity_atendimento"] == "positivo"

    assert pred_df.loc[2, "has_bagagem"] == 1
    assert pred_df.loc[2, "polarity_bagagem"] == "negativo"

    assert pred_df.loc[3, "has_app_checkin"] == 1
    assert pred_df.loc[3, "polarity_app_checkin"] == "positivo"


def test_contract_validation_sentiment_reviews() -> None:
    """Verifica que o arquivo de reviews gravado atende 100% ao contrato schemas/sentiment_reviews.yaml."""
    target_parquet = path("data/curated/sentiment_reviews.parquet")
    if not target_parquet.exists():
        df = generate_corpus(n_reviews=100, seed=123)
        save_corpus(df, target_parquet)

    contract = load_contract("sentiment_reviews")
    violations = validate_table(contract, target_parquet)
    assert violations == [], f"Violações encontradas em sentiment_reviews: {violations}"


def test_contract_validation_friction_map() -> None:
    """Verifica que o arquivo friction_map.parquet atende 100% ao contrato schemas/friction_map.yaml."""
    target_parquet = path("data/analytics/friction_map.parquet")
    if not target_parquet.exists():
        reviews_path = path("data/curated/sentiment_reviews.parquet")
        df_rev = pd.read_parquet(reviews_path)
        friction_df, weights_json = compute_friction_map(df_rev)
        save_friction_outputs(friction_df, weights_json)

    contract = load_contract("friction_map")
    violations = validate_table(contract, target_parquet)
    assert violations == [], f"Violações encontradas em friction_map: {violations}"


def test_contract_fail_loud_on_invalid_data(tmp_path: Path) -> None:
    """Garante que qualquer inconsistência de contrato levanta erro explícito (fail loud)."""
    contract = load_contract("friction_map")

    # Carrega uma linha válida real e corrompe valores (valor fora de allowed_values e intensidade negativa)
    good_parquet = path("data/analytics/friction_map.parquet")
    df = pd.read_parquet(good_parquet).head(2).copy()
    df.loc[0, "aspect"] = "aspecto_invalido"  # violar allowed_values
    df.loc[0, "semester_intensity"] = -0.5  # violar check custom

    bad_parquet = tmp_path / "bad_table.parquet"
    df.to_parquet(bad_parquet)

    violations = validate_table(contract, bad_parquet)
    assert len(violations) > 0, "Deveria ter detectado violações no contrato"
    assert any("valores fora do domínio" in v or "check custom falhou" in v for v in violations)

    with pytest.raises(RuntimeError, match="Contrato de dados violado"):
        validate_or_raise(contract, bad_parquet)


def test_friction_weights_plausible_ranges() -> None:
    """Verifica se os pesos gerados em friction_weights.json estão em faixas plausíveis."""
    target_json = path("data/curated/friction_weights.json")
    assert target_json.exists(), f"Arquivo não encontrado: {target_json}"

    with open(target_json, encoding="utf-8") as f:
        data = json.load(f)

    # 1. Estrutura _meta
    assert "_meta" in data, "O arquivo deve conter a seção '_meta'"
    assert "description" in data["_meta"]
    assert "synthetic_honesty_statement" in data["_meta"]
    assert set(data["_meta"]["aspects"]) == set(ASPECTS)

    # 2. Pesos
    assert "weights" in data
    weights = data["weights"]
    assert len(weights) == len(ASPECTS)

    # Soma deve ser 1.0
    total_weight = sum(weights.values())
    assert total_weight == pytest.approx(1.0, abs=1e-3)

    # Cada peso deve estar dentro de uma faixa razoável (> 0.01 e < 0.45)
    for asp, w in weights.items():
        assert 0.01 <= w <= 0.45, f"Peso de {asp} fora da faixa plausível: {w}"

    # Atritos operacionais críticos devem ter peso maior que conforto
    assert weights["atraso"] > weights["conforto"]
    assert weights["atendimento"] > weights["conforto"]


def test_approaches_holdout_temporal_execution() -> None:
    """Verifica que a avaliação em holdout temporal executa e gera métricas coerentes."""
    results = run_evaluation(cutoff_date="2025-08-31")

    assert results["n_train"] > 0
    assert results["n_test"] > 0
    assert 0.0 <= results["comparison"]["global_lexicon_macro_f1"] <= 1.0
    assert 0.0 <= results["comparison"]["global_tfidf_macro_f1"] <= 1.0
    assert -1.0 <= results["comparison"]["inter_approach_kappa"] <= 1.0
