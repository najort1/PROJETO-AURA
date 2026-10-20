"""Catálogo de Ferramentas Corporativas (Tools) do Aura Concierge.

Implementa as 8 ferramentas corporativas de atendimento e retenção:
1. consultar_cliente_360(customer_id)
2. consultar_historico_atritos_voos(customer_id, limite_eventos, apenas_com_atrito)
3. consultar_regras_regulamento(termo_ou_pergunta, top_k, fact_id)
4. conceder_milhas_cortesia(customer_id, quantidade_pontos, motivo, flight_id)
5. emitir_voucher_servico(customer_id, tipo_servico, motivo, flight_id)
6. propor_acao_retencao_kanban(customer_id, action_id, action_name, mensagem_proposta, justificativa, status, canal)
7. escalar_atendimento_vip(customer_id, gravidade, sumario_atrito, canal_preferencial)
8. listar_clientes_em_risco_ou_atrito(top_n, min_churn_prob, apenas_alto_valor, tipo_atrito)

Inclui a classe ToolRegistry para geração de schemas OpenAI nativos e despacho de chamadas.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import uuid
from collections.abc import Callable
from typing import Any

import duckdb
import pandas as pd
from pydantic import BaseModel

from agent.models import (
    AcaoKanbanArgs,
    AcaoKanbanResult,
    Cliente360Result,
    ClienteRiscoItem,
    ConcederMilhasArgs,
    ConcessaoMilhasResult,
    ConsultarAtritosArgs,
    ConsultarCliente360Args,
    ConsultarRegulamentoArgs,
    DecisionRecord,
    EmissaoVoucherResult,
    EmitirVoucherArgs,
    EscalacaoVipResult,
    EscalarVipArgs,
    EventoHistorico,
    HistoricoAtritosResult,
    ListarClientesRiscoArgs,
    ListarClientesRiscoResult,
    RegraRegulamentoResult,
)
from agent.rag.retriever import get_retriever
from agent.safety import get_safety_engine
from aura_core.log import get_logger
from aura_core.paths import ROOT

logger = get_logger("agent.tools")

ANALYTICS_DIR = ROOT / "data" / "analytics"
DUCKDB_PATH = ANALYTICS_DIR / "aura_analytics.duckdb"

# Cache em memória para DataFrames analíticos
_CACHE_DFS: dict[str, pd.DataFrame] = {}
_VALID_CUSTOMER_IDS: set[str] | None = None


def _get_analytics_df(name: str) -> pd.DataFrame:
    """Lê Parquet analítico com cache em memória."""
    if name not in _CACHE_DFS:
        path = ANALYTICS_DIR / f"{name}.parquet"
        if not path.exists():
            raise FileNotFoundError(
                f"Arquivo de dados '{name}.parquet' não encontrado em {ANALYTICS_DIR}."
            )
        _CACHE_DFS[name] = pd.read_parquet(path)
    return _CACHE_DFS[name]


def _is_customer_valid_and_exists(customer_id: str) -> tuple[bool, str]:
    """Valida formato do customer_id ('C' seguido de dígitos) e sua existência nas bases analíticas oficiais [FIN-02]."""
    global _VALID_CUSTOMER_IDS
    norm_cid = customer_id.strip()

    if not re.match(r"^C\d+$", norm_cid):
        return (
            False,
            f"Formato de customer_id inválido: '{customer_id}'. Deve iniciar com 'C' seguido exclusivamente de dígitos numéricos (ex: 'C038454').",
        )

    try:
        if _VALID_CUSTOMER_IDS is None:
            # União dos IDs de AMBAS as bases (projeção de coluna única: leitura
            # barata mesmo com dois arquivos). Sem break: preserva a semântica de
            # união da implementação original. Se ambos falharem → set vazio →
            # fail-closed (nenhum cliente validado).
            cids: set[str] = set()
            for name in ("customers_scores", "agent_input"):
                file_path = ANALYTICS_DIR / f"{name}.parquet"
                if file_path.exists():
                    try:
                        df_proj = pd.read_parquet(file_path, columns=["customer_id"])
                        cids.update(df_proj["customer_id"].astype(str).str.strip())
                    except Exception as ex:
                        logger.debug("Leitura de customer_id em %s falhou: %s", file_path, ex)
            _VALID_CUSTOMER_IDS = cids

        if norm_cid not in _VALID_CUSTOMER_IDS:
            return (
                False,
                f"Cliente '{norm_cid}' não foi localizado nas bases analíticas oficiais de CRM.",
            )
    except Exception as e:
        logger.error("Erro ao validar existência do cliente %s: %s", norm_cid, e)
        # Fail-closed
        return False, f"Falha no sistema de validação cadastral para o cliente '{norm_cid}': {e}"

    return True, ""


def _get_duckdb_conn() -> duckdb.DuckDBPyConnection | None:
    """Abre conexão somente-leitura com aura_analytics.duckdb."""
    if DUCKDB_PATH.exists():
        try:
            return duckdb.connect(str(DUCKDB_PATH), read_only=True)
        except Exception as e:
            logger.warning("Falha ao abrir DuckDB em modo read_only: %s", e)
    return None


# -----------------------------------------------------------------------------
# 1. consultar_cliente_360
# -----------------------------------------------------------------------------
def consultar_cliente_360(customer_id: str) -> dict[str, Any]:
    """Consulta visão 360° do cliente: cadastrais, fidelidade, scores analíticos e SHAP."""
    norm_cid = customer_id.strip()

    try:
        df_input = _get_analytics_df("agent_input")
        df_scores = _get_analytics_df("customers_scores")
    except Exception as e:
        logger.error("Erro ao carregar datasets para consultar_cliente_360: %s", e)
        return {"found": False, "customer_id": norm_cid, "error": str(e)}

    match_input = df_input[df_input["customer_id"] == norm_cid]
    match_scores = df_scores[df_scores["customer_id"] == norm_cid]

    if match_input.empty and match_scores.empty:
        return {
            "found": False,
            "customer_id": norm_cid,
            "message": f"Cliente '{norm_cid}' não foi localizado na base analítica.",
        }

    row_in = match_input.iloc[0].to_dict() if not match_input.empty else {}
    row_sc = match_scores.iloc[0].to_dict() if not match_scores.empty else {}

    # SHAP parsing seguro
    shap_top3: list[dict[str, Any]] = []
    raw_shap = row_sc.get("shap_top3") or row_in.get("shap_top3")
    if isinstance(raw_shap, str):
        try:
            parsed_shap = json.loads(raw_shap)
            if isinstance(parsed_shap, list):
                if parsed_shap and isinstance(parsed_shap[0], dict):
                    shap_top3 = parsed_shap
                else:
                    shap_top3 = [{"factor": item} for item in parsed_shap]
        except Exception:
            shap_top3 = [{"raw": raw_shap}]
    elif isinstance(raw_shap, list):
        shap_top3 = [{"factor": str(x)} if not isinstance(x, dict) else x for x in raw_shap]

    # Higienização estrita LGPD: nunca expõe faixa_etaria, genero ou regiao na resposta para LLM
    result = Cliente360Result(
        found=True,
        customer_id=norm_cid,
        tier=row_in.get("tier") or row_sc.get("tier"),
        persona=row_in.get("persona") or row_sc.get("persona"),
        risk_state=row_in.get("risk_state") or row_sc.get("risk_state"),
        churn_prob=float(row_in.get("churn_prob", row_sc.get("churn_prob", 0.0))),
        clv_12m_previsto=float(row_in.get("clv_12m_previsto", row_sc.get("clv_12m_previsto", 0.0))),
        valor_em_risco=float(row_sc.get("valor_em_risco", 0.0)),
        alto_valor=bool(row_in.get("alto_valor", row_sc.get("alto_valor", False))),
        score_av=float(row_sc.get("score_av", 0.0)),
        saldo_pontos=int(row_in.get("saldo_pontos", row_sc.get("saldo_pontos", 0))),
        pontos_expirando_30d=int(
            row_in.get("pontos_expirando_30d", row_sc.get("pontos_expirando_30d", 0))
        ),
        pontos_qualificaveis_12m=int(
            row_in.get("pontos_qualificaveis_12m", row_sc.get("pontos_qualificaveis_12m", 0))
        ),
        meta_proximo_nivel_pct=float(
            row_in.get("meta_proximo_nivel_pct", row_sc.get("meta_proximo_nivel_pct", 0.0))
        ),
        trechos_12m=int(row_in.get("trechos_12m", row_sc.get("trechos_12m", 0))),
        gastos_12m_brl=float(row_in.get("gastos_12m_brl", row_sc.get("gastos_12m_brl", 0.0))),
        rota_favorita=row_in.get("rota_favorita"),
        beneficio_nao_utilizado=row_in.get("beneficio_nao_utilizado"),
        atritos_dominantes=row_in.get("atritos_dominantes"),
        shap_top3=shap_top3,
    )
    return result.model_dump()


# -----------------------------------------------------------------------------
# 2. consultar_historico_atritos_voos
# -----------------------------------------------------------------------------
def consultar_historico_atritos_voos(
    customer_id: str,
    limite_eventos: int = 10,
    apenas_com_atrito: bool = False,
) -> dict[str, Any]:
    """Consulta histórico de voos, atritos, reclamações e resgates de pontos."""
    norm_cid = customer_id.strip()

    try:
        df_timeline = _get_analytics_df("customer_timeline")
    except Exception as e:
        logger.error("Erro ao carregar customer_timeline: %s", e)
        return {"customer_id": norm_cid, "total_eventos_encontrados": 0, "eventos": []}

    match_events = df_timeline[df_timeline["customer_id"] == norm_cid].copy()

    # Guardrail anti-vazamento temporal pós-cutoff (estritamente <= 2025-08-31)
    if not match_events.empty and "data" in match_events.columns:
        match_events = match_events[match_events["data"].astype(str) <= "2025-08-31"]

    if apenas_com_atrito:
        match_events = match_events[
            (match_events["impacto"] == "negativo") | (match_events["tipo"] == "atrito")
        ]

    # Ordenação decrescente por data
    if not match_events.empty and "data" in match_events.columns:
        match_events = match_events.sort_values(by="data", ascending=False)

    match_events = match_events.head(limite_eventos)

    # Enriquecimento com voos de aura_analytics.duckdb (permite múltiplos voos por data [DAT-01])
    flights_by_date: dict[str, list[dict[str, Any]]] = {}
    conn = _get_duckdb_conn()
    if conn:
        try:
            q = """
                SELECT t.customer_id, t.flight_id, strftime(f.departure_date, '%Y-%m-%d') as flight_date,
                       f.flight_number, f.origin_airport, f.destination_airport, f.delay_minutes, f.is_cancelled
                FROM stg_transactions t
                JOIN stg_flights f ON t.flight_id = f.flight_id
                WHERE t.customer_id = ?
            """
            f_df = conn.execute(q, [norm_cid]).df()
            for r in f_df.to_dict(orient="records"):
                f_date = str(r["flight_date"])
                fl_data = {
                    "flight_id": str(r["flight_id"]),
                    "flight_number": str(r["flight_number"]),
                    "origin_airport": str(r.get("origin_airport") or ""),
                    "destination_airport": str(r.get("destination_airport") or ""),
                    "delay_minutes": int(r["delay_minutes"]),
                    "is_cancelled": bool(r["is_cancelled"]),
                }
                flights_by_date.setdefault(f_date, []).append(fl_data)
        except Exception as e:
            logger.debug("Consulta auxiliar de voos no DuckDB falhou: %s", e)
        finally:
            conn.close()

    used_flight_ids: set[str] = set()
    eventos: list[EventoHistorico] = []
    for row in match_events.to_dict(orient="records"):
        event_date = str(row.get("data", ""))
        titulo = str(row.get("titulo", ""))
        detalhe = str(row.get("detalhe", ""))
        fl_list = flights_by_date.get(event_date, [])
        fl_info: dict[str, Any] = {}

        if fl_list:
            text_context = f"{titulo} {detalhe}".upper()
            candidate = None
            for fl in fl_list:
                orig = fl["origin_airport"].upper()
                dest = fl["destination_airport"].upper()
                f_num = fl["flight_number"].upper()
                if (
                    orig
                    and dest
                    and (
                        f"{orig}-{dest}" in text_context
                        or f"{orig} -> {dest}" in text_context
                        or (orig in text_context and dest in text_context)
                    )
                ) or (f_num and f_num in text_context):
                    candidate = fl
                    break

            if not candidate:
                is_negative = (
                    str(row.get("impacto", "")) == "negativo"
                    or str(row.get("tipo", "")) == "atrito"
                )
                if is_negative:
                    for fl in fl_list:
                        if (fl["is_cancelled"] or fl["delay_minutes"] > 0) and fl[
                            "flight_id"
                        ] not in used_flight_ids:
                            candidate = fl
                            break

            if not candidate:
                unused = [fl for fl in fl_list if fl["flight_id"] not in used_flight_ids]
                candidate = unused[0] if unused else fl_list[0]

            fl_info = candidate
            used_flight_ids.add(fl_info["flight_id"])

        eventos.append(
            EventoHistorico(
                data=event_date,
                tipo=str(row.get("tipo", "geral")),
                titulo=titulo,
                detalhe=detalhe,
                impacto=str(row.get("impacto", "neutro")),
                flight_id=fl_info.get("flight_id"),
                flight_number=fl_info.get("flight_number"),
            )
        )

    res = HistoricoAtritosResult(
        customer_id=norm_cid,
        total_eventos_encontrados=len(eventos),
        eventos=eventos,
    )
    return res.model_dump()


# -----------------------------------------------------------------------------
# 3. consultar_regras_regulamento
# -----------------------------------------------------------------------------
def consultar_regras_regulamento(
    termo_ou_pergunta: str,
    top_k: int = 3,
    fact_id: str | None = None,
) -> dict[str, Any]:
    """Consulta a base de conhecimento regulatória (RAG) para obter regras e citações formais."""
    retriever = get_retriever()
    citacoes_out: list[dict[str, Any]] = []

    if fact_id and fact_id.strip():
        try:
            cit = retriever.get_citation_for_fact(fact_id.strip())
            citacoes_out.append(cit.to_dict())
        except Exception as e:
            logger.warning("Falha ao recuperar fact_id '%s': %s", fact_id, e)

    if not citacoes_out and termo_ou_pergunta and termo_ou_pergunta.strip():
        try:
            results = retriever.search(termo_ou_pergunta.strip(), top_k=top_k)
            for c in results:
                citacoes_out.append(c.to_dict())
        except Exception as e:
            logger.error("Erro na busca semântica RAG: %s", e)

    res = RegraRegulamentoResult(
        query=termo_ou_pergunta,
        total_encontrados=len(citacoes_out),
        citacoes=citacoes_out,
    )
    return res.model_dump()


# -----------------------------------------------------------------------------
# 4. conceder_milhas_cortesia
# -----------------------------------------------------------------------------
def conceder_milhas_cortesia(
    customer_id: str,
    quantidade_pontos: int,
    motivo: str,
    flight_id: str | None = None,
) -> dict[str, Any]:
    """Concede milhas de cortesia ou compensação com governança de autonomia L1/L2."""
    norm_cid = customer_id.strip()
    norm_flight = flight_id.strip() if flight_id else None
    safety = get_safety_engine()

    # Validação cadastral do cliente antes de qualquer decisão financeira [FIN-02]
    is_valid_cust, err_cust = _is_customer_valid_and_exists(norm_cid)
    if not is_valid_cust:
        return ConcessaoMilhasResult(
            success=False,
            customer_id=norm_cid,
            pontos_concedidos=0,
            autonomy_level="BLOCKED",
            status="rejected",
            human_review=False,
            motivo=motivo,
            flight_id=norm_flight,
            decision=None,
            message=f"Concessão bloqueada por validação cadastral: {err_cust}",
        ).model_dump()

    # Validação de segurança e antifraude
    safety_check = safety.validate_miles_grant(
        customer_id=norm_cid,
        quantidade_pontos=quantidade_pontos,
        motivo=motivo,
        flight_id=norm_flight,
    )

    if not safety_check.approved:
        return ConcessaoMilhasResult(
            success=False,
            customer_id=norm_cid,
            pontos_concedidos=0,
            autonomy_level=safety_check.level,
            status=safety_check.status,
            human_review=safety_check.human_review,
            motivo=motivo,
            flight_id=norm_flight,
            decision=None,
            message=f"Concessão bloqueada pela governança: {safety_check.reason}",
        ).model_dump()

    # Construção da decisão
    action_id = f"ACT-MILHAS-{norm_flight}" if norm_flight else f"ACT-MILHAS-{quantidade_pontos}PTS"
    msg_texto = (
        f"Concedidas {quantidade_pontos} milhas de cortesia em compensação por atrito operacional. "
        f"Motivo: {motivo}." + (f" Voo: {norm_flight}." if norm_flight else "")
    )
    notes_payload = (
        f"Autonomia: {safety_check.level}. Voo: {norm_flight or 'N/A'}. Motivo: {motivo}. "
        f"Regras: {safety_check.reason}"
    )

    record = DecisionRecord(
        customer_id=norm_cid,
        action_id=action_id,
        action_name=f"concessao_milhas_{quantidade_pontos}",
        status=safety_check.status,
        operator="aura_concierge_agent",
        original_message=msg_texto,
        final_message=msg_texto,
        edited=False,
        notes=notes_payload,
    )

    # Persistência em decisions.jsonl com assinatura SHA-256
    persisted = safety.persist_decision(record)

    msg_status = (
        "Milhas creditadas automaticamente (Autonomia L1)."
        if safety_check.level == "L1"
        else "Milhas enviadas para revisão e aprovação humana de supervisor (Autonomia L2)."
    )

    return ConcessaoMilhasResult(
        success=True,
        customer_id=norm_cid,
        pontos_concedidos=quantidade_pontos,
        autonomy_level=safety_check.level,
        status=safety_check.status,
        human_review=safety_check.human_review,
        motivo=motivo,
        flight_id=norm_flight,
        decision=persisted,
        message=f"{msg_status} Assinatura SHA-256 gerada.",
    ).model_dump()


# -----------------------------------------------------------------------------
# 5. emitir_voucher_servico
# -----------------------------------------------------------------------------
def emitir_voucher_servico(
    customer_id: str,
    tipo_servico: str,
    motivo: str,
    flight_id: str | None = None,
) -> dict[str, Any]:
    """Emite voucher de conveniência/serviço (Lounge, Bagagem, etc.) com validade de 90 dias."""
    norm_cid = customer_id.strip()
    norm_flight = flight_id.strip() if flight_id else None
    safety = get_safety_engine()

    # Validação cadastral do cliente antes de qualquer decisão financeira [FIN-02]
    is_valid_cust, err_cust = _is_customer_valid_and_exists(norm_cid)
    if not is_valid_cust:
        return EmissaoVoucherResult(
            success=False,
            customer_id=norm_cid,
            codigo_voucher="",
            tipo_servico=tipo_servico,
            validade_dias=90,
            data_expiracao="",
            status="rejected",
            human_review=False,
            motivo=motivo,
            flight_id=norm_flight,
            decision=None,
            message=f"Emissão de voucher bloqueada por validação cadastral: {err_cust}",
        ).model_dump()

    safety_check = safety.validate_voucher_issue(
        customer_id=norm_cid,
        tipo_servico=tipo_servico,
        motivo=motivo,
        flight_id=norm_flight,
    )

    if not safety_check.approved:
        return EmissaoVoucherResult(
            success=False,
            customer_id=norm_cid,
            codigo_voucher="",
            tipo_servico=tipo_servico,
            validade_dias=90,
            data_expiracao="",
            status=safety_check.status,
            human_review=safety_check.human_review,
            motivo=motivo,
            flight_id=norm_flight,
            decision=None,
            message=f"Emissão de voucher bloqueada: {safety_check.reason}",
        ).model_dump()

    voucher_code = f"AURA-VCH-{uuid.uuid4().hex[:8].upper()}"
    exp_date = (dt.date.today() + dt.timedelta(days=90)).isoformat()
    action_id = f"ACT-VOUCHER-{tipo_servico.upper().replace(' ', '_')}"

    msg_texto = (
        f"Voucher de cortesia para {tipo_servico.title()} emitido com sucesso (Código: {voucher_code}). "
        f"Válido até {exp_date}. Motivo: {motivo}."
    )
    notes_payload = f"Código: {voucher_code}. Validade: 90 dias ({exp_date}). Voo: {norm_flight or 'N/A'}. Motivo: {motivo}."

    record = DecisionRecord(
        customer_id=norm_cid,
        action_id=action_id,
        action_name=f"voucher_{tipo_servico.lower()}",
        status=safety_check.status,  # approved (L1)
        operator="aura_concierge_agent",
        original_message=msg_texto,
        final_message=msg_texto,
        edited=False,
        notes=notes_payload,
    )

    persisted = safety.persist_decision(record)

    return EmissaoVoucherResult(
        success=True,
        customer_id=norm_cid,
        codigo_voucher=voucher_code,
        tipo_servico=tipo_servico,
        validade_dias=90,
        data_expiracao=exp_date,
        status=safety_check.status,
        human_review=safety_check.human_review,
        motivo=motivo,
        flight_id=norm_flight,
        decision=persisted,
        message=f"Voucher emitido com sucesso e gravado no Kanban. Código: {voucher_code}.",
    ).model_dump()


# -----------------------------------------------------------------------------
# 6. propor_acao_retencao_kanban
# -----------------------------------------------------------------------------
def propor_acao_retencao_kanban(
    customer_id: str,
    action_id: str,
    action_name: str,
    mensagem_proposta: str,
    justificativa: str,
    status: str = "suggested",
    canal: str = "whatsapp",
) -> dict[str, Any]:
    """Cria proposta de ação e insere novo card na esteira Kanban de retenção."""
    norm_cid = customer_id.strip()
    safety = get_safety_engine()

    # Validação cadastral do cliente [FIN-02]
    is_valid_cust, err_cust = _is_customer_valid_and_exists(norm_cid)
    if not is_valid_cust:
        return AcaoKanbanResult(
            success=False,
            card_id="",
            customer_id=norm_cid,
            action_id=action_id,
            action_name=action_name,
            status="rejected",
            decision=None,
            message=f"Ação no Kanban bloqueada por validação cadastral: {err_cust}",
        ).model_dump()

    safety_check = safety.validate_kanban_proposal(
        customer_id=norm_cid,
        action_id=action_id,
        action_name=action_name,
        mensagem=mensagem_proposta,
        justificativa=justificativa,
        status_proposto=status,
    )

    if not safety_check.approved:
        return AcaoKanbanResult(
            success=False,
            card_id="",
            customer_id=norm_cid,
            action_id=action_id,
            action_name=action_name,
            status=safety_check.status,
            decision=None,
            message=f"Ação no Kanban bloqueada pela governança: {safety_check.reason}",
        ).model_dump()

    card_id = f"KBN-{uuid.uuid4().hex[:6].upper()}"
    notes_payload = (
        f"Card: {card_id}. Canal: {canal}. Justificativa: {justificativa}. "
        f"Governança: {safety_check.reason}"
    )

    record = DecisionRecord(
        customer_id=norm_cid,
        action_id=action_id,
        action_name=action_name,
        status=safety_check.status,
        operator="aura_concierge_agent",
        original_message=mensagem_proposta,
        final_message=mensagem_proposta,
        edited=False,
        notes=notes_payload,
    )

    persisted = safety.persist_decision(record)

    return AcaoKanbanResult(
        success=True,
        card_id=card_id,
        customer_id=norm_cid,
        action_id=action_id,
        action_name=action_name,
        status=safety_check.status,
        decision=persisted,
        message=f"Ação proposta registrada no Kanban com status '{safety_check.status}' e SHA-256 verificado.",
    ).model_dump()


# -----------------------------------------------------------------------------
# 7. escalar_atendimento_vip
# -----------------------------------------------------------------------------
def escalar_atendimento_vip(
    customer_id: str,
    gravidade: str,
    sumario_atrito: str,
    canal_preferencial: str = "telefone",
) -> dict[str, Any]:
    """Escalona o caso para atendimento prioritário na mesa de concierges VIP humanos (L2)."""
    norm_cid = customer_id.strip()
    safety = get_safety_engine()

    # Validação cadastral do cliente [FIN-02]
    is_valid_cust, err_cust = _is_customer_valid_and_exists(norm_cid)
    if not is_valid_cust:
        return EscalacaoVipResult(
            success=False,
            protocolo="",
            customer_id=norm_cid,
            gravidade=gravidade,
            status="rejected",
            human_review=False,
            decision=None,
            message=f"Escalonamento VIP bloqueado por validação cadastral: {err_cust}",
        ).model_dump()

    safety_check = safety.validate_vip_escalation(
        customer_id=norm_cid,
        gravidade=gravidade,
        sumario_atrito=sumario_atrito,
    )

    if not safety_check.approved:
        return EscalacaoVipResult(
            success=False,
            protocolo="",
            customer_id=norm_cid,
            gravidade=gravidade,
            status=safety_check.status,
            human_review=False,
            decision=None,
            message=f"Escalonamento VIP bloqueado pela governança: {safety_check.reason}",
        ).model_dump()

    protocolo = f"VIP-{dt.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    action_id = f"ACT-VIP-{gravidade.upper()}"
    msg_texto = (
        f"Encaminhamento emergencial para mesa de atendimento VIP (Protocolo: {protocolo}). "
        f"Gravidade: {gravidade.upper()}. Canal preferencial: {canal_preferencial}. "
        f"Sumário: {sumario_atrito}"
    )
    notes_payload = (
        f"Protocolo: {protocolo}. Gravidade: {gravidade}. Canal: {canal_preferencial}. "
        f"Sumário: {sumario_atrito}. Status: in_review."
    )

    record = DecisionRecord(
        customer_id=norm_cid,
        action_id=action_id,
        action_name=f"escalonamento_vip_{gravidade.lower()}",
        status="in_review",  # Autonomia L2 obrigatória
        operator="aura_concierge_agent",
        original_message=msg_texto,
        final_message=msg_texto,
        edited=False,
        notes=notes_payload,
    )

    persisted = safety.persist_decision(record)

    return EscalacaoVipResult(
        success=True,
        protocolo=protocolo,
        customer_id=norm_cid,
        gravidade=gravidade,
        status="in_review",
        human_review=True,
        decision=persisted,
        message=f"Caso escalonado para Mesa VIP humana sob protocolo {protocolo}.",
    ).model_dump()


# -----------------------------------------------------------------------------
# 8. listar_clientes_em_risco_ou_atrito
# -----------------------------------------------------------------------------
def listar_clientes_em_risco_ou_atrito(
    top_n: int = 10,
    min_churn_prob: float = 0.50,
    apenas_alto_valor: bool = True,
    tipo_atrito: str | None = None,
) -> dict[str, Any]:
    """Varredura proativa de clientes em alto risco de churn ou atrito severo."""
    try:
        df_scores = _get_analytics_df("customers_scores")
        df_input = _get_analytics_df("agent_input")
    except Exception as e:
        logger.error("Erro ao carregar dados para listar clientes em risco: %s", e)
        return {"total_encontrados": 0, "clientes": []}

    df = df_scores.copy()

    # Filtro de probabilidade de churn
    df = df[df["churn_prob"] >= min_churn_prob]

    # Filtro de alto valor
    if apenas_alto_valor:
        df = df[
            (df["alto_valor"].astype(bool))
            | (df["score_av"] >= 0.70)
            | (df["tier"].isin(["Diamante", "Safira", "diamante", "safira"]))
        ]

    # Filtro de atrito dominante [ROB-02: regex=False para prevenir ReDoS e falhas de parser]
    if tipo_atrito and "atritos_dominantes" in df_input.columns:
        matching_cids = df_input[
            df_input["atritos_dominantes"].str.contains(
                tipo_atrito, case=False, na=False, regex=False
            )
        ]["customer_id"]
        df = df[df["customer_id"].isin(matching_cids)]

    # Ordenação por valor em risco decrescente
    if "valor_em_risco" in df.columns:
        df = df.sort_values(by="valor_em_risco", ascending=False)
    else:
        df = df.sort_values(by="churn_prob", ascending=False)

    df_top = df.head(top_n)

    # Dicionário de atritos dominantes de agent_input
    input_friction_map = {}
    if "atritos_dominantes" in df_input.columns:
        sub_input = df_input[df_input["customer_id"].isin(df_top["customer_id"])]
        input_friction_map = dict(
            zip(
                sub_input["customer_id"].astype(str),
                sub_input["atritos_dominantes"].astype(str),
                strict=False,
            )
        )

    items: list[ClienteRiscoItem] = []
    for row in df_top.to_dict(orient="records"):
        cid = str(row["customer_id"])
        items.append(
            ClienteRiscoItem(
                customer_id=cid,
                tier=str(row.get("tier", "azul")),
                persona=str(row.get("persona", "geral")),
                churn_prob=float(row.get("churn_prob", 0.0)),
                clv_12m_previsto=float(row.get("clv_12m_previsto", 0.0)),
                valor_em_risco=float(row.get("valor_em_risco", 0.0)),
                saldo_pontos=int(row.get("saldo_pontos", 0)),
                risk_state=str(row.get("risk_state", "medio")),
                atritos_dominantes=input_friction_map.get(cid),
            )
        )

    res = ListarClientesRiscoResult(
        total_encontrados=len(items),
        clientes=items,
    )
    return res.model_dump()


_TOOL_SCHEMAS: dict[str, type[BaseModel]] = {
    "consultar_cliente_360": ConsultarCliente360Args,
    "consultar_historico_atritos_voos": ConsultarAtritosArgs,
    "consultar_regras_regulamento": ConsultarRegulamentoArgs,
    "conceder_milhas_cortesia": ConcederMilhasArgs,
    "emitir_voucher_servico": EmitirVoucherArgs,
    "propor_acao_retencao_kanban": AcaoKanbanArgs,
    "escalar_atendimento_vip": EscalarVipArgs,
    "listar_clientes_em_risco_ou_atrito": ListarClientesRiscoArgs,
}


# =============================================================================
# Registro Central de Ferramentas (ToolRegistry)
# =============================================================================
class ToolRegistry:
    """Registro e orquestrador de execução das ferramentas do Aura Concierge."""

    def __init__(self) -> None:
        self._tools: dict[str, Callable[..., Any]] = {
            "consultar_cliente_360": consultar_cliente_360,
            "consultar_historico_atritos_voos": consultar_historico_atritos_voos,
            "consultar_regras_regulamento": consultar_regras_regulamento,
            "conceder_milhas_cortesia": conceder_milhas_cortesia,
            "emitir_voucher_servico": emitir_voucher_servico,
            "propor_acao_retencao_kanban": propor_acao_retencao_kanban,
            "escalar_atendimento_vip": escalar_atendimento_vip,
            "listar_clientes_em_risco_ou_atrito": listar_clientes_em_risco_ou_atrito,
        }

    def get_openai_schemas(self) -> list[dict[str, Any]]:
        """Retorna as definições no formato OpenAI Tool / Function Calling."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "consultar_cliente_360",
                    "description": (
                        "Consulta a visão 360 do cliente Azul Fidelidade: tier, persona, scores de churn, "
                        "CLV, saldo de pontos, trechos voados e explicabilidade SHAP."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_id": {
                                "type": "string",
                                "description": "ID do cliente (ex: 'C000004' ou 'C038454').",
                            }
                        },
                        "required": ["customer_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "consultar_historico_atritos_voos",
                    "description": (
                        "Consulta o histórico de voos, atritos, atrasos, cancelamentos e resgates do cliente. "
                        "Retorna o identificador de voo (flight_id) quando disponível para compensações."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_id": {
                                "type": "string",
                                "description": "ID do cliente a ser consultado.",
                            },
                            "limite_eventos": {
                                "type": "integer",
                                "description": "Número máximo de eventos retornados (padrão: 10).",
                                "default": 10,
                            },
                            "apenas_com_atrito": {
                                "type": "boolean",
                                "description": "Se verdadeiro, filtra apenas eventos com atrito ou impacto negativo.",
                                "default": False,
                            },
                        },
                        "required": ["customer_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "consultar_regras_regulamento",
                    "description": (
                        "Recupera trechos e citações oficiais do Regulamento Azul Fidelidade "
                        "através do mecanismo RAG. Retorna fact_id, score e resumo normativo."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "termo_ou_pergunta": {
                                "type": "string",
                                "description": "Termo de busca, pergunta ou tema normativo (ex: 'validade de pontos Diamante').",
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Quantidade máxima de regras a retornar.",
                                "default": 3,
                            },
                            "fact_id": {
                                "type": "string",
                                "description": "Consulta exata de citação por fact_id se conhecido.",
                            },
                        },
                        "required": ["termo_ou_pergunta"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "conceder_milhas_cortesia",
                    "description": (
                        "Concede milhas de cortesia/compensação ao cliente. "
                        "Autonomia L1: <= 2.000 pts (auto-aprovado). "
                        "Autonomia L2: > 2.000 até 5.000 pts (requer revisão humana). "
                        "Teto: acima de 5.000 pts é bloqueado. "
                        "Possui verificação antifraude de voo duplicado."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_id": {
                                "type": "string",
                                "description": "ID do cliente beneficiário.",
                            },
                            "quantidade_pontos": {
                                "type": "integer",
                                "description": "Quantidade de pontos a conceder (máximo 5000).",
                            },
                            "motivo": {
                                "type": "string",
                                "description": "Justificativa operacional e transparente da concessão.",
                            },
                            "flight_id": {
                                "type": "string",
                                "description": "Identificador do voo que originou o atrito (opcional, para idempotência).",
                            },
                        },
                        "required": ["customer_id", "quantidade_pontos", "motivo"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "emitir_voucher_servico",
                    "description": (
                        "Emite voucher de conveniência/serviço com validade de 90 dias (Autonomia L1). "
                        "Tipos aceitos: lounge, bagagem, upgrade_cabine, wi-fi, refeicao_aeroporto."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_id": {
                                "type": "string",
                                "description": "ID do cliente.",
                            },
                            "tipo_servico": {
                                "type": "string",
                                "description": "Tipo de serviço ('lounge', 'bagagem', 'upgrade_cabine', 'wi-fi', 'refeicao_aeroporto').",
                            },
                            "motivo": {
                                "type": "string",
                                "description": "Contexto e motivo da emissão.",
                            },
                            "flight_id": {
                                "type": "string",
                                "description": "ID do voo relacionado se aplicável.",
                            },
                        },
                        "required": ["customer_id", "tipo_servico", "motivo"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "propor_acao_retencao_kanban",
                    "description": (
                        "Registra nova proposta de ação e insere um card na esteira Kanban de retenção. "
                        "Permite definir canal, mensagem personalizada e justificativa analítica."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_id": {
                                "type": "string",
                                "description": "ID do cliente.",
                            },
                            "action_id": {
                                "type": "string",
                                "description": "Código da ação (ex: ACT-UPGRADE-SAFIRA, ACT-DESCONTO-RENOVA).",
                            },
                            "action_name": {
                                "type": "string",
                                "description": "Nome conciso da ação proposta.",
                            },
                            "mensagem_proposta": {
                                "type": "string",
                                "description": "Texto respeitoso e personalizado para o cliente (sem dados sensíveis).",
                            },
                            "justificativa": {
                                "type": "string",
                                "description": "Justificativa embasada em risco, churn ou valor.",
                            },
                            "status": {
                                "type": "string",
                                "description": "Status inicial ('suggested' ou 'in_review'). Padrão: suggested.",
                                "default": "suggested",
                            },
                            "canal": {
                                "type": "string",
                                "description": "Canal de contato ('whatsapp', 'email', 'app_push', 'telefone'). Padrão: whatsapp.",
                                "default": "whatsapp",
                            },
                        },
                        "required": [
                            "customer_id",
                            "action_id",
                            "action_name",
                            "mensagem_proposta",
                            "justificativa",
                        ],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "escalar_atendimento_vip",
                    "description": (
                        "Encaminha o caso para a mesa de atendimento de concierges VIP humanos (Autonomia L2). "
                        "Gera protocolo formal e notifica a equipe de supervisão com status 'in_review'."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_id": {
                                "type": "string",
                                "description": "ID do cliente VIP.",
                            },
                            "gravidade": {
                                "type": "string",
                                "enum": ["media", "alta", "critica"],
                                "description": "Nível de gravidade do atrito ou risco.",
                            },
                            "sumario_atrito": {
                                "type": "string",
                                "description": "Resumo objetivo da insatisfação e histórico recente.",
                            },
                            "canal_preferencial": {
                                "type": "string",
                                "description": "Canal sugerido para contato VIP ('telefone', 'whatsapp').",
                                "default": "telefone",
                            },
                        },
                        "required": ["customer_id", "gravidade", "sumario_atrito"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "listar_clientes_em_risco_ou_atrito",
                    "description": (
                        "Realiza busca proativa por clientes prioritários em risco de churn ou com atritos recentes "
                        "para acionamento imediato."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "top_n": {
                                "type": "integer",
                                "description": "Quantidade máxima de clientes a retornar (padrão: 10).",
                                "default": 10,
                            },
                            "min_churn_prob": {
                                "type": "number",
                                "description": "Probabilidade mínima de churn (padrão: 0.50).",
                                "default": 0.50,
                            },
                            "apenas_alto_valor": {
                                "type": "boolean",
                                "description": "Filtrar apenas clientes de alto valor (padrão: true).",
                                "default": True,
                            },
                            "tipo_atrito": {
                                "type": "string",
                                "description": "Filtrar por atrito dominante específico (ex: 'atraso', 'bagagem', 'preco').",
                            },
                        },
                    },
                },
            },
        ]

    def invoke(self, name: str, arguments: dict[str, Any]) -> Any:
        """Executa a ferramenta pelo nome com validação estrita de schema Pydantic [ROB-01]."""
        if name not in self._tools:
            raise ValueError(
                f"Ferramenta desconhecida: {name!r}. Disponíveis: {list(self._tools.keys())}"
            )

        schema = _TOOL_SCHEMAS.get(name)
        if schema is not None:
            try:
                coerced_args = schema(**arguments).model_dump()
            except Exception as e:
                logger.error(
                    "Erro de validação Pydantic para tool '%s' com args %s: %s", name, arguments, e
                )
                return {"error": f"Argumentos inválidos para {name}: {e}"}
        else:
            coerced_args = arguments

        func = self._tools[name]
        try:
            return func(**coerced_args)
        except TypeError as e:
            logger.error(
                "Erro de assinatura ao invocar tool '%s' com args %s: %s", name, coerced_args, e
            )
            return {"error": f"Argumentos inválidos para {name}: {e}"}
        except Exception as e:
            logger.error("Exceção não tratada ao invocar tool '%s': %s", name, e)
            return {"error": f"Falha na execução de {name}: {e}"}


_DEFAULT_TOOL_REGISTRY: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    """Retorna instância singleton do ToolRegistry."""
    global _DEFAULT_TOOL_REGISTRY
    if _DEFAULT_TOOL_REGISTRY is None:
        _DEFAULT_TOOL_REGISTRY = ToolRegistry()
    return _DEFAULT_TOOL_REGISTRY
