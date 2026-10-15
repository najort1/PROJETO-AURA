"""Bridge de execução do AuraConciergeAgent para consumo por interfaces web (Next.js / API).

Suporta invocação via linha de comando ou arquivo JSON temporário para evitar
problemas de escape no Windows. Retorna sempre saída estruturada em JSON UTF-8.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Força codificação UTF-8 na saída padrão do Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from agent.autonomous import AuraConciergeAgent
from agent.models import AgentTurnResult, DecisionRecord


def _serialize_decision(dec: DecisionRecord) -> dict[str, Any]:
    return {
        "timestamp": dec.timestamp,
        "customer_id": dec.customer_id,
        "action_id": dec.action_id,
        "action_name": dec.action_name,
        "status": dec.status,
        "operator": dec.operator,
        "original_message": dec.original_message,
        "final_message": dec.final_message,
        "edited": dec.edited,
        "notes": dec.notes,
        "hash_signature": dec.hash_signature,
    }


def _serialize_turn_result(res: AgentTurnResult) -> dict[str, Any]:
    return {
        "success": True,
        "customer_id": res.customer_id,
        "reply": res.final_message,
        "turns": res.turns,
        "thought_process": res.thought_process,
        "tools_executed": res.tool_calls_executed,
        "decisions_taken": [_serialize_decision(d) for d in res.decisions_taken],
        "finish_reason": res.finish_reason,
        "human_review_required": res.human_review_required,
        "metadata": res.metadata,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Aura Concierge Web Bridge")
    parser.add_argument("--input-file", type=str, help="Caminho para arquivo JSON com payload de entrada")
    parser.add_argument("--input-json", type=str, help="String JSON com payload de entrada")
    parser.add_argument("--output-file", type=str, help="Caminho para arquivo de saída JSON (opcional)")

    args = parser.parse_args()

    payload: dict[str, Any] = {}
    if args.input_file:
        content = Path(args.input_file).read_text(encoding="utf-8")
        payload = json.loads(content)
    elif args.input_json:
        payload = json.loads(args.input_json)
    else:
        # Tenta ler do stdin
        raw_in = sys.stdin.read()
        if raw_in.strip():
            payload = json.loads(raw_in)
        else:
            payload = {"action": "status"}

    action = payload.get("action", "chat")
    agent = AuraConciergeAgent()

    try:
        if action == "chat":
            message = payload.get("message", "Olá")
            history = payload.get("history", [])
            # Se vier customer_id opcional no contexto do chat, insere lembrete inicial se histórico estiver vazio
            customer_id = payload.get("customer_id")
            if customer_id and not history:
                augmented_message = f"[Contexto do Operador: Cliente selecionado na tela = {customer_id}]\n{message}"
            else:
                augmented_message = message

            res = agent.chat(message=augmented_message, history=history)
            out_data = _serialize_turn_result(res)

        elif action == "evaluate":
            customer_id = payload.get("customer_id")
            if not customer_id:
                raise ValueError("customer_id é obrigatório para a ação 'evaluate'")
            res = agent.evaluate_and_act(customer_id=customer_id)
            out_data = _serialize_turn_result(res)

        elif action == "scan":
            limit = int(payload.get("limit", 5))
            min_churn = float(payload.get("min_churn", 0.50))
            dry_run = bool(payload.get("dry_run", False))
            results = agent.scan_and_resolve(limit=limit, min_churn=min_churn, dry_run=dry_run)
            out_data = {
                "success": True,
                "action": "scan",
                "processed_count": len(results),
                "dry_run": dry_run,
                "results": [_serialize_turn_result(r) for r in results],
            }

        elif action == "status":
            out_data = {
                "success": True,
                "status": "online",
                "model": agent.engine.llm_client.model,
                "base_url": agent.engine.llm_client.base_url,
                "tools_available": [
                    "consultar_cliente_360",
                    "consultar_historico_atritos_voos",
                    "consultar_regras_regulamento",
                    "conceder_milhas_cortesia",
                    "emitir_voucher_servico",
                    "propor_acao_retencao_kanban",
                    "escalar_atendimento_vip",
                    "listar_clientes_em_risco_ou_atrito",
                ],
            }
        else:
            raise ValueError(f"Ação desconhecida: {action}")

    except Exception as exc:
        out_data = {
            "success": False,
            "error": str(exc),
            "error_type": exc.__class__.__name__,
        }

    output_str = json.dumps(out_data, ensure_ascii=False, indent=2)

    if args.output_file:
        Path(args.output_file).write_text(output_str, encoding="utf-8")

    print(output_str)


if __name__ == "__main__":
    main()
