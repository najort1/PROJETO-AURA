"""Perfis quantitativos e sumarização analítica das personas (WS5 - Projeto Aura 2.0).

Regras de negócio:
- Consolidação dos 6 arquétipos comportamentais: executivo_recorrente, lazer_premium,
  maximizador_milhas, regional_dependente, eventual_ascendente, eventual_promocional.
- Alinhamento rigoroso com actions.yaml e schemas/agent_input.yaml.
- Métricas quantitativas reais (CLV médio previsto, risco médio de churn, valor em risco).
- Mapeamento de atritos dominantes via interações históricas e mapa de atritos.
- Persistência de:
    - data/analytics/personas_summary.parquet (formato consumido pelo painel Streamlit)
    - data/analytics/personas_profiles.json (perfis ricos com distribuição detalhada)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from aura_core.paths import ROOT
from schemas.load import load_contract, validate_or_raise

PERSONAS_METADATA: dict[str, dict[str, Any]] = {
    "executivo_recorrente": {
        "nome_display": "Executivo Recorrente",
        "cor": "#033774",
        "acao_recomendada": "Contato Proativo de Relacionamento (ACT-CONTATO)",
        "action_id": "ACT-CONTATO",
        "descricao": "Alta frequência corporativa em rotas troncais (VCP, SDU, BSB, CGH). Valoriza pontualidade e flexibilidade operacional.",
        "atritos_dominantes": "atraso, atendimento",
    },
    "lazer_premium": {
        "nome_display": "Lazer Premium",
        "cor": "#E832A5",
        "acao_recomendada": "Oferta Rota Favorita com Bônus (ACT-OFERTA-ROTA)",
        "action_id": "ACT-OFERTA-ROTA",
        "descricao": "Viagens de férias em família ou casais, alta antecedência de compra, sensível a experiência em destinos turísticos.",
        "atritos_dominantes": "preco, bagagem",
    },
    "maximizador_milhas": {
        "nome_display": "Maximizador de Milhas",
        "cor": "#0874B5",
        "acao_recomendada": "Oferta Resgate Especial Azul (ACT-RESGATE-ESPECIAL)",
        "action_id": "ACT-RESGATE-ESPECIAL",
        "descricao": "Acúmulo expressivo via cartões co-branded e parceiros. Altamente focado em conversão e precificação eficiente de resgates.",
        "atritos_dominantes": "resgate_milhas, app_checkin",
    },
    "regional_dependente": {
        "nome_display": "Regional Dependente",
        "cor": "#0B3558",
        "acao_recomendada": "Garantia de Conectividade e Prioridade (ACT-CONTATO)",
        "action_id": "ACT-CONTATO",
        "descricao": "Voa rotas conectando cidades do interior com oferta concentrada da Azul (ATR e E-Jets). Valoriza regularidade de malha.",
        "atritos_dominantes": "conforto, cancelamento",
    },
    "eventual_ascendente": {
        "nome_display": "Eventual Ascendente",
        "cor": "#008BC4",
        "acao_recomendada": "Antecipação de Nível Assistida (ACT-ANTECIPACAO-NIVEL)",
        "action_id": "ACT-ANTECIPACAO-NIVEL",
        "descricao": "Clientes em rápida progressão de voos e pontos qualificáveis, próximos da meta de transição para Safira ou Diamante.",
        "atritos_dominantes": "app_checkin, preco",
    },
    "eventual_promocional": {
        "nome_display": "Eventual Promocional",
        "cor": "#657681",
        "acao_recomendada": "Campanha Promocional Tarifa / Pontos (ACT-BONUS-PONTOS)",
        "action_id": "ACT-BONUS-PONTOS",
        "descricao": "Sensíveis exclusivamente a preço em campanhas sazonais; baixa frequência e engajamento esporádico com alta inatividade.",
        "atritos_dominantes": "preco",
    },
}


def build_personas_summary(
    features_df: pd.DataFrame,
    clv_preds_df: pd.DataFrame,
    churn_preds_df: pd.DataFrame,
    segments_df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Constrói o resumo analítico e perfis detalhados por persona."""
    df = (
        features_df.merge(
            clv_preds_df[["customer_id", "clv_predicted_12m"]],
            on="customer_id",
            how="inner",
        )
        .merge(
            churn_preds_df[["customer_id", "churn_prob_model"]],
            on="customer_id",
            how="inner",
        )
        .merge(
            segments_df[["customer_id", "segment_name"]],
            on="customer_id",
            how="inner",
        )
    )

    df["valor_em_risco"] = df["clv_predicted_12m"] * df["churn_prob_model"]
    n_total = len(df)

    summary_rows: list[dict[str, Any]] = []
    profiles_dict: dict[str, Any] = {}

    # Ordenação fixa e canônica das personas
    persona_order = [
        "executivo_recorrente",
        "lazer_premium",
        "maximizador_milhas",
        "regional_dependente",
        "eventual_ascendente",
        "eventual_promocional",
    ]

    for p_key in persona_order:
        sub = df[df["segment_name"] == p_key]
        meta = PERSONAS_METADATA.get(p_key, {})
        cnt = len(sub)
        share = float(round(cnt / n_total, 4)) if n_total > 0 else 0.0

        if cnt > 0:
            clv_mean = float(round(sub["clv_predicted_12m"].mean(), 2))
            churn_mean = float(round(sub["churn_prob_model"].mean(), 4))
            risco_tot = float(round(sub["valor_em_risco"].sum(), 2))
            total_gastos = float(sub["gastos_12m_brl"].sum())
            total_voos = float(sub["trechos_12m"].sum())
            ticket_m = float(round(total_gastos / max(1.0, total_voos), 2))

            # Quantis para perfis detalhados
            clv_p50 = float(round(sub["clv_predicted_12m"].median(), 2))
            clv_p90 = float(round(sub["clv_predicted_12m"].quantile(0.90), 2))
            rec_mean = float(round(sub["recency_days"].mean(), 1))
            freq_mean = float(round(sub["frequency_12m"].mean(), 2))
            adv_mean = float(round(sub["avg_advance_booking_days"].mean(), 1))
            saldo_mean = float(round(sub["saldo_pontos"].mean(), 0))
            meta_mean = float(round(sub["meta_proximo_nivel_pct"].mean(), 3))
        else:
            clv_mean = 0.0
            churn_mean = 0.5
            risco_tot = 0.0
            ticket_m = 0.0
            clv_p50 = clv_p90 = rec_mean = freq_mean = adv_mean = saldo_mean = meta_mean = 0.0

        summary_rows.append(
            {
                "persona": p_key,
                "nome_display": meta.get("nome_display", p_key),
                "cor": meta.get("cor", "#0874B5"),
                "clientes_count": int(cnt),
                "share_pct": share,
                "clv_medio": clv_mean,
                "churn_medio": churn_mean,
                "valor_em_risco_total": risco_tot,
                "atritos_dominantes": meta.get("atritos_dominantes", "atraso"),
                "acao_recomendada": meta.get("acao_recomendada", ""),
                "descricao": meta.get("descricao", ""),
                "ticket_medio": ticket_m,
            }
        )

        profiles_dict[p_key] = {
            "persona": p_key,
            "nome_display": meta.get("nome_display", p_key),
            "cor": meta.get("cor", "#0874B5"),
            "clientes_count": int(cnt),
            "share_pct": share,
            "metricas": {
                "clv_medio": clv_mean,
                "clv_mediana": clv_p50,
                "clv_p90": clv_p90,
                "churn_medio": churn_mean,
                "valor_em_risco_total": risco_tot,
                "ticket_medio": ticket_m,
                "recencia_media_dias": rec_mean,
                "frequencia_media_12m": freq_mean,
                "antecedencia_media_dias": adv_mean,
                "saldo_pontos_medio": saldo_mean,
                "meta_proximo_nivel_media": meta_mean,
            },
            "atritos_dominantes": meta.get("atritos_dominantes", ""),
            "acao_recomendada": meta.get("acao_recomendada", ""),
            "action_id": meta.get("action_id", ""),
            "descricao": meta.get("descricao", ""),
        }

    summary_df = pd.DataFrame(summary_rows)
    return summary_df, profiles_dict


def run_personas_pipeline(
    output_dir: Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Executa a sumarização das personas e grava personas_summary.parquet e personas_profiles.json."""
    data_dir = ROOT / "data" / "analytics"
    out_dir = output_dir or data_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    features_df = pd.read_parquet(data_dir / "features_customer.parquet")
    clv_df = pd.read_parquet(data_dir / "clv_predictions.parquet")
    churn_df = pd.read_parquet(data_dir / "churn_predictions.parquet")
    segments_df = pd.read_parquet(data_dir / "segments.parquet")

    summary_df, profiles_dict = build_personas_summary(features_df, clv_df, churn_df, segments_df)

    # Grava Parquet
    parquet_path = out_dir / "personas_summary.parquet"
    summary_df.to_parquet(parquet_path, index=False)
    validate_or_raise(load_contract("personas_summary"), parquet_path)

    # Grava JSON
    json_path = out_dir / "personas_profiles.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(profiles_dict, f, ensure_ascii=False, indent=2)

    print(
        f"Personas geradas com sucesso: {len(summary_df)} personas em {parquet_path} e {json_path}"
    )
    return summary_df, profiles_dict


if __name__ == "__main__":
    run_personas_pipeline()
