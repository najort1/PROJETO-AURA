"""Carregador de dados com cache (@st.cache_data), fallback transparente para fixtures e fail loud.

Regras:
1. O app tenta carregar primeiramente de `data/analytics/<nome>.parquet`.
2. Se ausente, recorre a `app/fixtures/<nome>.parquet` com sinalizador explícito `is_fixture=True`.
3. Se ambos ausentes, falha alto com mensagem ACIONÁVEL orientando a rodar `python tasks.py all`.
4. Nunca mistura dados silenciosamente sem declarar a origem.
5. Persiste decisões do operador em `data/analytics/decisions.jsonl`.
"""

from __future__ import annotations

import datetime as dt
import json
from typing import Any

import pandas as pd
import streamlit as st

from aura_core.paths import ROOT

ANALYTICS_DIR = ROOT / "data" / "analytics"
FIXTURES_DIR = ROOT / "app" / "fixtures"
DECISIONS_FILE = ANALYTICS_DIR / "decisions.jsonl"


class DatasetLoadError(RuntimeError):
    """Erro acionável quando um dataset esperado não é encontrado."""

    pass


def is_analytics_mode() -> bool:
    """Verifica se a base analítica real (data/analytics/) está presente no ambiente."""
    return (ANALYTICS_DIR / "customers_scores.parquet").exists()


@st.cache_data(show_spinner="Carregando tabela analítica...")
def _read_parquet_cached(file_path_str: str, mtime_ns: int) -> pd.DataFrame:
    """Lê parquet com cache nativo do Streamlit.

    O `mtime_ns` (tempo de modificação do arquivo) entra na chave do cache:
    quando `tasks.py all` (ou qualquer pipeline) regenera o parquet, o cache
    invalida automaticamente. Sem isso, o app exibiria dados obsoletos após
    re-execuções do pipeline (achado WS8a-3).
    """
    return pd.read_parquet(file_path_str)


def load_dataset(name: str) -> tuple[pd.DataFrame, bool]:
    """Carrega uma tabela pelo nome lógico garantindo prioridade REAL-FIRST.

    Regra estrita de integridade (WS8b):
    1. Se a base analítica real existir (is_analytics_mode()): carrega
       OBRIGATORIAMENTE de `data/analytics/{name}.parquet`.
       NUNCA mistura dados reais com fixtures silenciosamente.
       Se faltar arquivo ou houver erro, FALHA ALTO (fail loud) com erro acionável.
    2. Se a base analítica real NÃO existir: recorre a `app/fixtures/{name}.parquet`
       marcando explicitamente `is_fixture=True`.
    3. Se ambos falharem: FALHA ALTO com mensagem orientando `python tasks.py all`.
    """
    analytics_path = ANALYTICS_DIR / f"{name}.parquet"
    fixture_path = FIXTURES_DIR / f"{name}.parquet"

    if is_analytics_mode():
        if analytics_path.exists():
            try:
                df = _read_parquet_cached(str(analytics_path), analytics_path.stat().st_mtime_ns)
                return df, False
            except Exception as e:
                raise DatasetLoadError(
                    f"Erro ao ler arquivo crítico real 'data/analytics/{name}.parquet': {e}\n\n"
                    f"👉 AÇÃO NECESSÁRIA: Execute no terminal: python tasks.py all "
                    f"(a base analítica está corrompida; nunca misturamos dados reais com fixtures)."
                ) from e
        else:
            raise DatasetLoadError(
                f"Base analítica real ativa, mas o arquivo crítico 'data/analytics/{name}.parquet' está ausente.\n\n"
                f"👉 AÇÃO NECESSÁRIA: Execute no terminal: python tasks.py all "
                f"(para gerar o artefato analítico ausente; nunca misturamos dados reais com fixtures)."
            )

    # Modo Fixtures (apenas quando não há base analítica gerada)
    if fixture_path.exists():
        df = _read_parquet_cached(str(fixture_path), fixture_path.stat().st_mtime_ns)
        return df, True

    # Se ambos falharem, mensagem de erro ACIONÁVEL
    msg = (
        f"Arquivo 'data/analytics/{name}.parquet' ausente e fixture correspondente em "
        f"'app/fixtures/{name}.parquet' não encontrada.\n\n"
        f"👉 AÇÃO NECESSÁRIA: Execute no terminal: python tasks.py all "
        f"(ou python -m app.fixtures.build_fixtures para modo offline)."
    )
    raise DatasetLoadError(msg)


def load_customers_data() -> tuple[pd.DataFrame, bool]:
    """Carrega dataset unificado de clientes, scores e atributos."""
    return load_dataset("customers_scores")


def load_personas_data() -> tuple[pd.DataFrame, bool]:
    """Carrega resumo analítico das personas e playbooks."""
    return load_dataset("personas_summary")


def load_timeline_data(customer_id: str | None = None) -> tuple[pd.DataFrame, bool]:
    """Carrega linha do tempo de eventos (voos, atritos, resgates, upgrades).

    Aplica guardrail estrito contra vazamento temporal pós-cutoff (max 2025-08-31).
    """
    df, is_fixture = load_dataset("customer_timeline")
    if not df.empty and "data" in df.columns:
        # Guardrail anti-vazamento temporal: estritamente <= 2025-08-31
        df = df[df["data"].astype(str) <= "2025-08-31"].copy()
    if customer_id and not df.empty:
        df = df[df["customer_id"] == customer_id].copy()
    return df, is_fixture


def load_recommendations_data() -> tuple[pd.DataFrame, bool]:
    """Carrega recomendações, mensagens e justificativas do agente."""
    return load_dataset("agent_recommendations")


def load_clv_shap_data(customer_id: str | None = None) -> tuple[pd.DataFrame, bool]:
    """Carrega fatores de explicabilidade SHAP para CLV."""
    df, is_fixture = load_dataset("clv_shap")
    if customer_id and not df.empty:
        df = df[df["customer_id"] == customer_id].copy()
    return df, is_fixture


def load_friction_data() -> tuple[pd.DataFrame, bool]:
    """Carrega mapa temporal de atritos e sentimento por aspecto."""
    return load_dataset("friction_map")


def load_fairness_data() -> tuple[pd.DataFrame, bool]:
    """Carrega métricas da auditoria de IA responsável e viés."""
    return load_dataset("fairness_metrics")


def record_decision(
    customer_id: str,
    action_id: str,
    action_name: str,
    status: str,  # "approved" ou "edited"
    original_message: str,
    final_message: str,
    operator: str = "operador_humano",
    notes: str | None = None,
) -> dict[str, Any]:
    """Registra decisão do operador em decisions.jsonl e no session_state."""
    decision = {
        "timestamp": dt.datetime.now(dt.UTC).isoformat(),
        "customer_id": customer_id,
        "action_id": action_id,
        "action_name": action_name,
        "status": status,
        "operator": operator,
        "original_message": original_message,
        "final_message": final_message,
        "edited": bool(original_message.strip() != final_message.strip()),
        "notes": notes,
    }

    # Salva no st.session_state se ativo
    if hasattr(st, "session_state"):
        if "decisions_history" not in st.session_state:
            st.session_state["decisions_history"] = []
        st.session_state["decisions_history"].append(decision)

    # Persiste em disco em data/analytics/decisions.jsonl
    try:
        ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
        with open(DECISIONS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(decision, ensure_ascii=False) + "\n")
    except Exception as e:
        # Se data/analytics falhar (ex.: permissão), tenta em .tmp ou registra erro amigável
        st.error(f"Erro ao persistir decisão em {DECISIONS_FILE}: {e}")

    return decision


def get_recorded_decisions() -> list[dict[str, Any]]:
    """Lê histórico de decisões já registradas no arquivo decisions.jsonl.

    Fail loud: linhas corrompidas NUNCA são descartadas em silêncio — o erro
    é sinalizado ao operador (auditoria exige rastreabilidade), e as linhas
    válidas anteriores ao erro são devolvidas.
    """
    decisions: list[dict[str, Any]] = []
    if DECISIONS_FILE.exists():
        with open(DECISIONS_FILE, encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    decisions.append(json.loads(line))
                except json.JSONDecodeError as e:
                    if hasattr(st, "session_state"):
                        st.warning(
                            f"⚠️ decisions.jsonl contém linha {line_no} corrompida "
                            f"(ignorada na exibição, não na auditoria): {e}"
                        )
    return decisions
