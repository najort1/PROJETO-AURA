"""Motor do Agente Autônomo de CRM de Alto Valor (Aura Concierge).

Implementa:
- AuraConciergeEngine: Loop ReAct multi-turn (até 8 turnos), system prompt corporativo,
  execução defensiva de chamadas de ferramentas e integração com SafetyEngine.
- AuraConciergeAgent: Interface de alto nível com métodos:
  - evaluate_and_act(customer_id)
  - chat(message, history)
  - scan_and_resolve(limit, min_churn, dry_run)
"""

from __future__ import annotations

import json
from typing import Any

from agent.guardrails import sanitize_input_text
from agent.llm import LLMClient
from agent.models import (
    AgentTurnResult,
    DecisionRecord,
)
from agent.safety import get_safety_engine
from agent.tools import ToolRegistry, get_tool_registry
from aura_core.log import get_logger

logger = get_logger("agent.autonomous")

SYSTEM_PROMPT = """Você é o Aura Concierge, Agente Autônomo Especialista de CRM de Alto Valor e Relacionamento do programa Azul Fidelidade.
Sua missão é atuar com proatividade, empatia e máxima precisão técnica para reter clientes valiosos (Diamante, Safira e Top-Tier), resolver atritos e garantir conformidade regulatória incondicional.

IDIOMA E TOM:
- Responda SEMPRE em Português do Brasil (pt-BR).
- Mantenha um tom profissional, cordial, executivo e acolhedor.

DIRETRIZES FUNDAMENTAIS DE ATUAÇÃO:
1. ANÁLISE 360° E DIAGNÓSTICO:
   - Sempre consulte o perfil 360° (`consultar_cliente_360`) e o histórico recente (`consultar_historico_atritos_voos`) antes de decidir qualquer ação.
   - Analise fatores SHAP de propensão a churn e CLV em risco para fundamentar suas ações.

2. GOVERNANÇA E NÍVEIS DE AUTONOMIA:
   - AUTONOMIA L1 (Aprovação Automática):
     * Concessão de milhas de cortesia/compensação até 2.000 pontos (`conceder_milhas_cortesia`).
     * Emissão de vouchers de conveniência (`emitir_voucher_servico`) de lounge, bagagem, wi-fi ou refeição.
   - AUTONOMIA L2 (Requer Revisão Humana de Supervisor - status 'in_review'):
     * Concessão de milhas entre 2.001 e 5.000 pontos.
     * Escalonamento para mesa de atendimento VIP (`escalar_atendimento_vip`).
   - TETO MÁXIMO E GOVERNANÇA:
     * Concessões acima de 5.000 pontos são ESTRITAMENTE PROIBIDAS e bloqueadas.
   - ANTIFRAUDE E IDEMPOTÊNCIA:
     * Sempre que houver um atrito originado em um voo específico, identifique e informe o `flight_id` (ex: FL0000015) para impedir duplicidades de compensação.

3. CONHECIMENTO REGULATÓRIO (RAG):
   - Em caso de dúvidas sobre benefícios da categoria (validade de pontos, bagagem gratuita, salas VIP), consulte a base de conhecimento oficial com `consultar_regras_regulamento`.

4. PROPOSTA DE RETENÇÃO E KANBAN:
   - Sempre proponha uma ação de retenção clara com `propor_acao_retencao_kanban`, `conceder_milhas_cortesia` ou `emitir_voucher_servico` adequada ao perfil e ao atrito encontrado.

5. GUARDRAILS ÉTICOS E LGPD:
   - NUNCA mencione idade, faixa etária, gênero, sexo, região de moradia ou dados sensíveis em suas comunicações.
   - Adote tom acolhedor, profissional e prestativo. JAMAIS use escassez manipulativa ("última chance", "tempo esgotando") ou faça falsas promessas de vantagens inexistentes.

FLUXO DE RACIOCÍNIO (ReAct):
- Seja objetivo e direto nas decisões. Evite deliberações redundantes.
- Ao identificar um atrito e o perfil do cliente, execute prontamente a ação recomendada (ex: `conceder_milhas_cortesia`, `emitir_voucher_servico` ou `propor_acao_retencao_kanban`).
- Final: Ao concluir as ferramentas, produza em Português (pt-BR) um resumo executivo claro contendo:
  1. Diagnóstico do cliente (Tier, risco, principais causas de atrito).
  2. Ações tomadas e status de governança (L1 Aprovado / L2 Homologação Pendente).
  3. Próximos passos recomendados.
"""


class AuraConciergeEngine:
    """Motor de execução ReAct multi-turn do Aura Concierge."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        tool_registry: ToolRegistry | None = None,
        max_turns: int = 8,
    ) -> None:
        self.llm_client = llm_client or LLMClient()
        self.tool_registry = tool_registry or get_tool_registry()
        self.safety_engine = get_safety_engine()
        self.max_turns = max_turns

    def run_turn(
        self,
        messages: list[dict[str, Any]],
        customer_id: str | None = None,
    ) -> AgentTurnResult:
        """Executa o ciclo iterativo ReAct com o modelo LLM e o catálogo de ferramentas."""
        thought_process: list[str] = []
        tools_executed: list[dict[str, Any]] = []
        decisions_taken: list[DecisionRecord] = []
        human_review_required = False

        conversation: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}] + [
            m for m in messages if m.get("role") != "system"
        ]

        schemas = self.tool_registry.get_openai_schemas()
        turn_count = 0
        final_text = ""
        finish_reason = "stop"

        while turn_count < self.max_turns:
            turn_count += 1
            logger.info("Executando turno ReAct %d/%d...", turn_count, self.max_turns)

            try:
                resp = self.llm_client.chat_completion_with_tools(
                    messages=conversation,
                    tools=schemas,
                    tool_choice="auto",
                )
            except Exception as e:
                logger.error("Erro na chamada LLM durante turno %d: %s", turn_count, e)
                return AgentTurnResult(
                    customer_id=customer_id,
                    turns=turn_count,
                    thought_process=thought_process,
                    tool_calls_executed=tools_executed,
                    decisions_taken=decisions_taken,
                    final_message=f"Erro durante a execução do agente: {e}",
                    finish_reason="error",
                    human_review_required=human_review_required,
                )

            msg = resp.get("message", {})
            finish_reason = resp.get("finish_reason", "stop")

            # Captura raciocínio interno (reasoning_content)
            reasoning = msg.get("reasoning_content")
            if reasoning and reasoning.strip():
                thought_process.append(f"[Turno {turn_count}] {reasoning.strip()}")

            content = msg.get("content") or ""
            tool_calls = msg.get("tool_calls") or []

            # Adiciona mensagem do assistente à conversa
            asst_payload: dict[str, Any] = {"role": "assistant"}
            if content:
                asst_payload["content"] = content
            if tool_calls:
                asst_payload["tool_calls"] = tool_calls
            conversation.append(asst_payload)

            if not tool_calls:
                # LLM encerrou a cadeia de chamadas de ferramentas e produziu resposta final
                final_text = content
                break

            # Processa todas as chamadas de ferramentas solicitadas
            for call in tool_calls:
                call_id = call.get("id") or f"call_{turn_count}"
                func = call.get("function", {})
                name = func.get("name", "")
                raw_args = func.get("arguments", "{}")

                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except json.JSONDecodeError as e:
                    logger.warning("Argumentos JSON inválidos na tool '%s': %s", name, e)
                    args = {}
                    tool_result = {"error": f"Argumentos JSON inválidos: {e}"}
                else:
                    logger.info("Executando ferramenta '%s' com args: %s", name, args)
                    tool_result = self.tool_registry.invoke(name, args)

                # Verifica se a ferramenta retornou registro de decisão persistido
                if isinstance(tool_result, dict):
                    dec_dict = tool_result.get("decision")
                    if dec_dict and isinstance(dec_dict, dict):
                        try:
                            rec = DecisionRecord(**dec_dict)
                            decisions_taken.append(rec)
                            if rec.status == "in_review":
                                human_review_required = True
                        except Exception as e:
                            logger.warning("Falha ao deserializar DecisionRecord: %s", e)

                    if tool_result.get("human_review") is True:
                        human_review_required = True

                record_log = {
                    "turn": turn_count,
                    "call_id": call_id,
                    "tool": name,
                    "arguments": args,
                    "result_summary": str(tool_result)[:300],
                }
                tools_executed.append(record_log)

                # Alimenta a observação de volta no diálogo
                conversation.append(
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": name,
                        "content": json.dumps(tool_result, ensure_ascii=False),
                    }
                )

            if finish_reason == "stop" and not tool_calls:
                break

        if not final_text and content:
            final_text = content

        if turn_count >= self.max_turns and not final_text.strip():
            # [ROB-03] Fallback sintético defensivo ao atingir max_turns sem texto final do LLM
            tools_summary = ", ".join([t.get("tool", "") for t in tools_executed]) or "nenhuma"
            decisions_summary = []
            for d in decisions_taken:
                decisions_summary.append(f"{d.action_name} ({d.action_id}, status: {d.status})")
            dec_str = (
                "; ".join(decisions_summary)
                if decisions_summary
                else "Nenhuma decisão financeira ou operacional foi persistida."
            )

            final_text = (
                f"Limite máximo de turnos atingido ({self.max_turns} turnos). "
                f"Sumário de execução do Aura Concierge: "
                f"Ferramentas acionadas: {tools_summary}. "
                f"Decisões registradas: {dec_str}."
            )

        return AgentTurnResult(
            customer_id=customer_id,
            turns=turn_count,
            thought_process=thought_process,
            tool_calls_executed=tools_executed,
            decisions_taken=decisions_taken,
            final_message=final_text.strip(),
            finish_reason=finish_reason if turn_count < self.max_turns else "max_turns",
            human_review_required=human_review_required,
            metadata={
                "total_decisions": len(decisions_taken),
                "total_tool_calls": len(tools_executed),
            },
        )


class AuraConciergeAgent:
    """Fachada de alto nível para operação do Aura Concierge em produção e CLI."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        tool_registry: ToolRegistry | None = None,
        max_turns: int = 8,
    ) -> None:
        self.engine = AuraConciergeEngine(
            llm_client=llm_client,
            tool_registry=tool_registry,
            max_turns=max_turns,
        )

    def evaluate_and_act(self, customer_id: str) -> AgentTurnResult:
        """Avalia de ponta a ponta a situação de um cliente e executa ações de retenção."""
        prompt = (
            f"Avalie a situação completa do cliente {customer_id}. "
            f"Consulte o perfil 360, investigue seu histórico recente de atritos ou voos impactados, "
            f"identifique a causa raiz do risco de perda e aplique as ações e compensações necessárias "
            f"(milhas, voucher ou proposta no Kanban) respeitando rigorosamente os limites L1/L2 e o regulamento."
        )
        messages = [{"role": "user", "content": prompt}]
        return self.engine.run_turn(messages, customer_id=customer_id)

    def chat(
        self,
        message: str,
        history: list[dict[str, Any]] | None = None,
        customer_id: str | None = None,
    ) -> AgentTurnResult:
        """Modo conversacional interativo com memória de diálogo e sanitização de entrada [SEC-02]."""
        sanitized_msg = sanitize_input_text(message)
        msgs = list(history or [])
        msgs.append({"role": "user", "content": sanitized_msg})
        return self.engine.run_turn(msgs, customer_id=customer_id)

    def scan_and_resolve(
        self,
        limit: int = 10,
        min_churn: float = 0.50,
        dry_run: bool = False,
    ) -> list[AgentTurnResult]:
        """Varredura proativa e resolução autônoma para clientes prioritários em risco."""
        logger.info(
            "Iniciando scan proativo: limit=%d, min_churn=%.2f, dry_run=%s...",
            limit,
            min_churn,
            dry_run,
        )

        res = self.engine.tool_registry.invoke(
            "listar_clientes_em_risco_ou_atrito",
            {
                "top_n": limit,
                "min_churn_prob": min_churn,
                "apenas_alto_valor": True,
            },
        )

        clientes = res.get("clientes", [])
        logger.info("Clientes elegíveis encontrados no scan: %d", len(clientes))

        results: list[AgentTurnResult] = []
        for item in clientes:
            cid = (
                item.get("customer_id")
                if isinstance(item, dict)
                else getattr(item, "customer_id", None)
            )
            if not cid:
                continue

            if dry_run:
                # Em modo dry-run, apenas consulta o perfil 360 sem registrar novas decisões
                c360 = self.engine.tool_registry.invoke(
                    "consultar_cliente_360", {"customer_id": cid}
                )
                simulated_result = AgentTurnResult(
                    customer_id=cid,
                    turns=1,
                    thought_process=[
                        f"[DRY-RUN] Cliente {cid} avaliado com churn={item.get('churn_prob', 0):.2f}"
                    ],
                    tool_calls_executed=[
                        {
                            "turn": 1,
                            "call_id": "dry_run_call",
                            "tool": "consultar_cliente_360",
                            "arguments": {"customer_id": cid},
                            "result_summary": str(c360)[:200],
                        }
                    ],
                    decisions_taken=[],
                    final_message=(
                        f"[DRY-RUN] Avaliação simulada para {cid}: Tier {c360.get('tier')}, "
                        f"Persona: {c360.get('persona')}, Churn: {c360.get('churn_prob', 0):.1%}. Nenhuma decisão gravada."
                    ),
                    finish_reason="stop",
                    human_review_required=False,
                    metadata={"dry_run": True},
                )
                results.append(simulated_result)
            else:
                turn_res = self.evaluate_and_act(cid)
                results.append(turn_res)

        return results
