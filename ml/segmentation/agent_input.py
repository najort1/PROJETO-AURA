"""Geração da tabela analítica agent_input para o motor de recomendação (WS5 / WS7).

Contrato: schemas/agent_input.yaml.
Granularidade: 1 registro por cliente na coorte de retenção.
Consumidores: agent.pipeline, agent.eligibility, agent.composer, app.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from aura_core.paths import ROOT
from schemas.load import load_contract, validate_or_raise


def extract_shap_factors_json(shap_raw: str | None) -> str | None:
    """Extrai uma lista serializada em JSON dos nomes dos fatores SHAP."""
    if not shap_raw or pd.isna(shap_raw):
        return None
    try:
        items = json.loads(shap_raw)
        if isinstance(items, list):
            factors = [str(x.get("factor", x) if isinstance(x, dict) else x) for x in items]
            return json.dumps(factors)
    except Exception:
        pass
    return None


def build_agent_input_dataframe(customers_scores_df: pd.DataFrame) -> pd.DataFrame:
    """Gera o DataFrame de agent_input exatamente conforme o contrato schemas/agent_input.yaml."""
    cs = customers_scores_df.copy()
    shap_factors = cs["shap_top3"].apply(extract_shap_factors_json)

    agent_input_df = pd.DataFrame(
        {
            "customer_id": cs["customer_id"].astype("string"),
            "tier": cs["tier"].astype("string"),
            "persona": cs["persona"].astype("string"),
            "risk_state": cs["risk_state"].astype("string"),
            "pontos_qualificaveis_12m": cs["pontos_qualificaveis_12m"].astype("int64"),
            "trechos_12m": cs["trechos_12m"].astype("int64"),
            "gastos_12m_brl": cs["gastos_12m_brl"].astype("float64"),
            "saldo_pontos": cs["saldo_pontos"].astype("int64"),
            "pontos_expirando_30d": cs["pontos_expirando_30d"].astype("int64"),
            "meta_proximo_nivel_pct": cs["meta_proximo_nivel_pct"].astype("float64"),
            "churn_prob": cs["churn_prob"].astype("float64"),
            "clv_12m_previsto": cs["clv_12m_previsto"].astype("float64"),
            "alto_valor": cs["alto_valor"].astype("bool"),
            "atritos_dominantes": cs["atritos_dominantes"].astype("string"),
            "rota_favorita": cs["rota_favorita"].astype("string"),
            "beneficio_nao_utilizado": cs["beneficio_nao_utilizado"].astype("string"),
            "shap_top3": shap_factors.astype("string"),
        }
    )
    return agent_input_df


def run_agent_input_pipeline(output_dir: Path | None = None) -> pd.DataFrame:
    """Executa a construção e validação do artefato agent_input.parquet."""
    data_dir = ROOT / "data" / "analytics"
    out_dir = output_dir or data_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    cs_file = data_dir / "customers_scores.parquet"
    if not cs_file.exists():
        raise FileNotFoundError(f"Arquivo {cs_file} ausente. Execute score_av e personas primeiro.")

    cs_df = pd.read_parquet(cs_file)
    ai_df = build_agent_input_dataframe(cs_df)

    out_file = out_dir / "agent_input.parquet"
    ai_df.to_parquet(out_file, index=False)
    validate_or_raise(load_contract("agent_input"), out_file)

    print(f"agent_input gerado com sucesso: {len(ai_df)} registros validados em {out_file}")
    return ai_df


if __name__ == "__main__":
    run_agent_input_pipeline()
