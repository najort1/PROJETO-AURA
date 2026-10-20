"""Pipeline ponta a ponta do agente de retenção e explicabilidade (WS7).

Fluxo:
client_state -> elegíveis -> Próxima Melhor Ação (ranking determinístico)
             -> mensagem (compositor offline / LLM opcional)
             -> guardrails
             -> saída validada por Pydantic e compatível com schemas/recommendations.yaml

Executável via:
    python -m agent.pipeline
    python -m agent.pipeline --precompute-demo (ou python tasks.py agent-precompute)
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
from pathlib import Path
from typing import Any

import pandas as pd

from agent.composer import (
    compose_recommendation,
    validate_known_benefit,
    validate_route_format,
)
from agent.eligibility import ClientState, EligibilityEngine, EligibilityResult
from agent.guardrails import (
    RecommendationPayload,
    check_guardrails,
    sanitize_input_text,
    validate_or_raise_guardrails,
)
from agent.llm import LLMClient
from aura_core.config import child_seed, program_rules, settings
from aura_core.log import get_logger
from aura_core.paths import ensure_dir, path
from schemas.load import load_contract, validate_or_raise

logger = get_logger("agent.pipeline")


def _calculate_action_score(
    action: EligibilityResult,
    client: ClientState,
) -> float:
    """Calcula score determinístico para ranking da Próxima Melhor Ação (Next Best Action).

    Score = VaR (churn_prob * CLV) * fit_persona * fit_atrito * fit_especifico * eficiencia_custo
    """
    var = max(client.churn_prob * client.clv_12m_previsto, 10.0)

    # Fit de Persona
    fit_persona = 1.0
    act_name = action.action_name
    exec_match = (
        act_name in {"contato_proativo_relacionamento", "antecipacao_de_nivel"}
        and client.persona == "executivo_recorrente"
    )
    milhas_match = (
        act_name in {"oferta_resgate_especial", "missao_acumulo_parceiro"}
        and client.persona == "maximizador_milhas"
    )
    lazer_match = act_name in {
        "oferta_rota_favorita",
        "pacote_experiencia_destino",
    } and client.persona in {"lazer_premium", "eventual_promocional"}
    regional_match = (
        act_name == "aviso_antecipado_prioridade" and client.persona == "regional_dependente"
    )
    ascendente_match = (
        act_name in {"antecipacao_de_nivel", "gesto_reconhecimento_bonus_pontos"}
        and client.persona == "eventual_ascendente"
    )

    if exec_match or milhas_match or lazer_match or regional_match or ascendente_match:
        fit_persona = 1.5

    # Fit de Atrito Observado
    atritos = client.get_atritos_set()
    fit_atrito = 1.0
    atraso_match = "atraso" in atritos and act_name == "reencaminhamento_atraso"
    resgate_match = "resgate" in atritos and act_name == "oferta_resgate_especial"

    if atraso_match:
        fit_atrito = 2.4
    elif resgate_match:
        fit_atrito = 1.8
    elif act_name == "educacao_beneficio_existente" and bool(client.beneficio_nao_utilizado):
        fit_atrito = 1.3

    # Fit Específico de Ação (diferenciação entre alternativas de mesmo segmento)
    fit_especifico = 1.0
    if act_name == "oferta_rota_favorita" and bool(client.rota_favorita):
        # Personalização em rota favorita definida tem prioridade sobre pacote genérico
        fit_especifico = 2.4
    elif act_name == "antecipacao_de_nivel" and client.meta_proximo_nivel_pct >= 0.80:
        fit_especifico = 1.5
    elif act_name == "pacote_experiencia_destino" and client.persona == "lazer_premium":
        fit_especifico = 1.2

    # Eficiência de Custo (ROI score)
    cost_efficiency = 100.0 / (float(action.cost_brl) + 10.0)

    return float(var * fit_persona * fit_atrito * fit_especifico * cost_efficiency)


def select_next_best_action(
    eligible_actions: list[EligibilityResult],
    client: ClientState,
) -> EligibilityResult:
    """Seleciona a melhor ação de forma 100% determinística."""
    if not eligible_actions:
        raise ValueError(f"Nenhuma ação elegível para o cliente {client.customer_id}")

    # Ordenação por (-score, action_id) garante desempate determinístico
    scored = [
        (_calculate_action_score(act, client), act.action_id, act) for act in eligible_actions
    ]
    scored.sort(key=lambda item: (-item[0], item[1]))
    return scored[0][2]


class RetentionAgentPipeline:
    """Orquestrador do ciclo completo de retenção."""

    def __init__(self) -> None:
        self.eligibility_engine = EligibilityEngine()
        self.llm_client = LLMClient()
        self.base_seed = settings().get("seed", 42)
        self.stage_seed = child_seed(self.base_seed, "agent_pipeline")

    def run_for_client(self, client: ClientState) -> RecommendationPayload:
        """Executa recomendação, redação e guardrails para um único cliente."""
        # 1. Sanitização prévia e validação estrita de formato de campos livres (ACH-02)
        sanitized_atritos = (
            sanitize_input_text(str(client.atritos_dominantes))
            if client.atritos_dominantes
            else None
        )

        sanitized_rota = None
        if client.rota_favorita:
            clean_rota = sanitize_input_text(client.rota_favorita)
            sanitized_rota = validate_route_format(clean_rota)

        sanitized_ben = None
        if client.beneficio_nao_utilizado:
            clean_ben = sanitize_input_text(client.beneficio_nao_utilizado)
            sanitized_ben = validate_known_benefit(clean_ben, client.tier)

        sanitized_client = ClientState(
            customer_id=client.customer_id,
            tier=client.tier,
            persona=client.persona,
            risk_state=client.risk_state,
            pontos_qualificaveis_12m=client.pontos_qualificaveis_12m,
            trechos_12m=client.trechos_12m,
            gastos_12m_brl=client.gastos_12m_brl,
            saldo_pontos=client.saldo_pontos,
            pontos_expirando_30d=client.pontos_expirando_30d,
            meta_proximo_nivel_pct=client.meta_proximo_nivel_pct,
            churn_prob=client.churn_prob,
            clv_12m_previsto=client.clv_12m_previsto,
            alto_valor=client.alto_valor,
            atritos_dominantes=sanitized_atritos,
            rota_favorita=sanitized_rota,
            beneficio_nao_utilizado=sanitized_ben,
            shap_top3=client.shap_top3,
        )

        # 2. Avaliação determinística de elegibilidade
        eligible_actions = self.eligibility_engine.get_eligible_actions(sanitized_client)

        if not eligible_actions:
            # ACH-01: NUNCA seleciona ação do inventário para cliente inelegível.
            # Emite resultado explícito de ACT-NO-ACTION / nenhuma_acao_elegivel com human_review=True.
            logger.info(
                "Cliente %s sem ações elegíveis no inventário. Emitindo ACT-NO-ACTION.",
                sanitized_client.customer_id,
            )
            all_results = self.eligibility_engine.evaluate_all(sanitized_client)
            ineligibility_reasons: list[str] = []
            for a in all_results:
                if a.reasons:
                    ineligibility_reasons.append(f"{a.action_name}: {'; '.join(a.reasons)}")

            rules_triggered = ["sem_acoes_elegiveis_no_inventario"]
            shap_list = (
                [str(x) for x in sanitized_client.shap_top3]
                if isinstance(sanitized_client.shap_top3, list)
                else []
            )

            raw_rec = {
                "customer_id": sanitized_client.customer_id,
                "action_id": "ACT-NO-ACTION",
                "action_name": "nenhuma_acao_elegivel",
                "channel": "nenhum",
                "message": (
                    "Olá! No momento, não identificamos ações ou ofertas ativas disponíveis para o seu perfil no "
                    "programa Azul Fidelidade. Continuamos à disposição em nossos canais oficiais de atendimento "
                    "para qualquer suporte que você precisar."
                ),
                "justification": {
                    "shap_top3": shap_list,
                    "atritos": sorted(list(sanitized_client.get_atritos_set())),
                    "regras_acionadas": rules_triggered + ineligibility_reasons[:6],
                    "motivo_resumo": (
                        f"Nenhuma ação elegível para persona={sanitized_client.persona}, "
                        f"risco={sanitized_client.risk_state}, tier={sanitized_client.tier}."
                    ),
                },
                "citations": [],
                "confidence": 1.0,
                "human_review": True,
                "mode": "offline",
                "snapshot_version": program_rules()
                .get("meta", {})
                .get("snapshot_version", "research-2026-10-12"),
            }
            # Guardrails DEVEM SEMPRE receber eligible_action_names=[] (ACH-01)
            return validate_or_raise_guardrails(raw_rec, eligible_action_names=[])

        # 3. Seleção determinística da Próxima Melhor Ação
        best_action = select_next_best_action(eligible_actions, sanitized_client)

        # 4. Composição da mensagem
        # Modo padrão e documentado: Compositor offline determinístico
        raw_rec = compose_recommendation(best_action, sanitized_client)

        # Se houver LLM configurado com chave real no ambiente:
        if self.llm_client.is_available() and os.getenv("AURA_LLM_API_KEY"):
            try:
                # Tenta LLM mantendo as restrições estritas
                system_prompt = (
                    "Você é o agente de retenção do Azul Fidelidade. Responda em JSON. "
                    "NUNCA invente benefícios fora do regulamento. Use tom respeitoso e sem urgência manipulativa."
                )
                user_prompt = f"Cliente: {sanitized_client.model_dump_json()}\nAção: {best_action.action_name}\nBase: {raw_rec}"
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
                llm_response = self.llm_client.generate_chat_completion(messages)
                parsed_llm = json.loads(llm_response)
                # Mescla respeitando os campos obrigatórios
                candidate_rec = dict(raw_rec)
                if "message" in parsed_llm and str(parsed_llm["message"]).strip():
                    candidate_rec["message"] = str(parsed_llm["message"])
                    candidate_rec["mode"] = "llm"

                # Guardrail gate no LLM: se violar qualquer regra, fallback offline automático
                check = check_guardrails(
                    candidate_rec, eligible_action_names=[a.action_name for a in eligible_actions]
                )
                if check.passed:
                    raw_rec = candidate_rec
                else:
                    logger.warning(
                        "Resposta do LLM violou guardrails (%s). Fallback offline ativado.",
                        check.violations,
                    )
            except Exception as exc:
                logger.warning(
                    "Falha na chamada LLM (%s). Executando fallback determinístico offline.", exc
                )

        # 5. Validação final de Guardrails (bloqueia se violar)
        eligible_names = {a.action_name for a in eligible_actions}
        validated = validate_or_raise_guardrails(raw_rec, eligible_action_names=eligible_names)
        return validated


def create_demo_fixtures() -> list[ClientState]:
    """Conjunto curado de fixtures representando personas, níveis e casos de borda."""
    return [
        ClientState(
            customer_id="C000101",
            tier="safira",
            persona="maximizador_milhas",
            risk_state="risco_alto_valor_alto",
            pontos_qualificaveis_12m=11000,
            trechos_12m=11,
            gastos_12m_brl=6200.0,
            saldo_pontos=85000,
            pontos_expirando_30d=5000,
            meta_proximo_nivel_pct=0.91,
            churn_prob=0.74,
            clv_12m_previsto=5800.0,
            alto_valor=True,
            atritos_dominantes="resgate",
            shap_top3=["queda_frequencia_voos", "atrito_resgate", "dias_desde_ultimo_resgate"],
        ),
        ClientState(
            customer_id="C000102",
            tier="topazio",
            persona="executivo_recorrente",
            risk_state="risco_alto_valor_alto",
            pontos_qualificaveis_12m=8500,
            trechos_12m=9,
            gastos_12m_brl=5100.0,
            saldo_pontos=22000,
            pontos_expirando_30d=0,
            meta_proximo_nivel_pct=0.85,
            churn_prob=0.68,
            clv_12m_previsto=7400.0,
            alto_valor=True,
            atritos_dominantes="atraso",
            shap_top3=["atrasos_recorrentes", "reducao_gastos_ corporativos", "inatividade_30d"],
        ),
        ClientState(
            customer_id="C000103",
            tier="diamante",
            persona="lazer_premium",
            risk_state="risco_baixo_potencial_alto",
            pontos_qualificaveis_12m=14500,
            trechos_12m=14,
            gastos_12m_brl=12500.0,
            saldo_pontos=120000,
            pontos_expirando_30d=0,
            meta_proximo_nivel_pct=0.55,
            churn_prob=0.18,
            clv_12m_previsto=14200.0,
            alto_valor=True,
            rota_favorita="VCP-REC",
            atritos_dominantes=None,
            shap_top3=["alta_frequencia_feriados", "alto_ticket_medio"],
        ),
        ClientState(
            customer_id="C000104",
            tier="azul",
            persona="regional_dependente",
            risk_state="risco_medio_valor_alto",
            pontos_qualificaveis_12m=4800,
            trechos_12m=5,
            gastos_12m_brl=2900.0,
            saldo_pontos=15000,
            pontos_expirando_30d=1200,
            meta_proximo_nivel_pct=0.80,
            churn_prob=0.42,
            clv_12m_previsto=3800.0,
            alto_valor=False,
            rota_favorita="CNF-MOC",
            atritos_dominantes=None,
            shap_top3=["dependencia_conexao_regional"],
        ),
        ClientState(
            customer_id="C000105",
            tier="safira",
            persona="eventual_ascendente",
            risk_state="risco_medio_valor_alto",
            pontos_qualificaveis_12m=9800,
            trechos_12m=10,
            gastos_12m_brl=5900.0,
            saldo_pontos=45000,
            pontos_expirando_30d=0,
            meta_proximo_nivel_pct=0.82,
            churn_prob=0.35,
            clv_12m_previsto=6100.0,
            alto_valor=True,
            beneficio_nao_utilizado="marcacao_antecipada_assento",
            shap_top3=["crescimento_rapido_gastos", "proximidade_diamante"],
        ),
        ClientState(
            customer_id="C000106",
            tier="diamante_unique",
            persona="executivo_recorrente",
            risk_state="risco_alto_valor_alto",
            pontos_qualificaveis_12m=28000,
            trechos_12m=28,
            gastos_12m_brl=54000.0,
            saldo_pontos=350000,
            pontos_expirando_30d=0,
            meta_proximo_nivel_pct=1.0,
            churn_prob=0.62,
            clv_12m_previsto=28000.0,
            alto_valor=True,
            atritos_dominantes="atraso",
            shap_top3=["atraso_voo_troncal", "alto_gasto_em_risco"],
        ),
    ]


def precompute_recommendations(
    output_path: Path | None = None,
    input_table_path: Path | None = None,
) -> Path:
    """Gera o arquivo analítico data/analytics/agent_recommendations.parquet validado contra o contrato."""
    out_file = output_path or path("data/analytics/agent_recommendations.parquet")
    ensure_dir(out_file.parent)

    in_file = input_table_path or path("data/analytics/agent_input.parquet")

    pipeline = RetentionAgentPipeline()
    clients: list[ClientState] = []

    if in_file.exists():
        logger.info("Carregando tabela analítica de entrada: %s", in_file)
        df_in = pd.read_parquet(in_file)
        for row_dict in df_in.to_dict(orient="records"):
            clients.append(ClientState(**row_dict))
    else:
        logger.info(
            "Tabela analítica de entrada (%s) ausente. Utilizando fixtures declaradas de demonstração.",
            in_file,
        )
        clients = create_demo_fixtures()

    logger.info("Processando recomendações para %d clientes...", len(clients))
    records: list[dict[str, Any]] = []
    now_iso = datetime.datetime.now(datetime.UTC).isoformat()

    for c in clients:
        rec = pipeline.run_for_client(c)
        records.append(
            {
                "customer_id": rec.customer_id,
                "action_id": rec.action_id,
                "action_name": rec.action_name,
                "channel": rec.channel,
                "message": rec.message,
                "justification_json": json.dumps(
                    rec.justification.model_dump(), ensure_ascii=False
                ),
                "citations_json": json.dumps(
                    [cit.model_dump() for cit in rec.citations], ensure_ascii=False
                ),
                "confidence": float(rec.confidence),
                "human_review": bool(rec.human_review),
                "mode": str(rec.mode),
                "snapshot_version": str(rec.snapshot_version),
                "recommended_at": now_iso,
            }
        )

    df_out = pd.DataFrame(records)
    df_out.to_parquet(out_file, index=False)
    logger.info("Salvo arquivo de recomendações em %s", out_file)

    # Validação estrita de contrato schemas/recommendations.yaml
    contract = load_contract("recommendations")
    validate_or_raise(contract, out_file)
    logger.info("Contrato schemas/recommendations.yaml validado com SUCESSO (0 violações).")

    return out_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline de Recomendações do Agente Aura 2.0")
    parser.add_argument(
        "--precompute-demo",
        action="store_true",
        help="Pré-computa recomendações e grava data/analytics/agent_recommendations.parquet",
    )
    args = parser.parse_args()

    if args.precompute_demo:
        out_p = precompute_recommendations()
        print("=" * 60)
        print("AURA 2.0 :: AGENT PRECOMPUTE CONCLUÍDO COM SUCESSO")
        print(f"Arquivo gerado: {out_p}")
        print("Contrato: schemas/recommendations.yaml -> VALIDADO (0 violações)")
        print("=" * 60)
    else:
        # Execução de amostra no console
        pipeline = RetentionAgentPipeline()
        fixtures = create_demo_fixtures()
        print(f"Executando agente para {len(fixtures)} perfis de demonstração...")
        for c in fixtures:
            res = pipeline.run_for_client(c)
            print(f"\n[Cliente {res.customer_id} | Tier: {c.tier} | Persona: {c.persona}]")
            print(f"  -> Ação: {res.action_name} ({res.action_id}) | Canal: {res.channel}")
            print(f"  -> Mensagem: {res.message[:120]}...")
            print(f"  -> Citações ({len(res.citations)}): {[cit.fact_id for cit in res.citations]}")
            print(f"  -> Human Review: {res.human_review} | Modo: {res.mode}")


if __name__ == "__main__":
    main()
