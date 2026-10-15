"""Interface de Linha de Comando (CLI) para o Agente Autônomo Aura Concierge.

Permite execução nos modos:
- --customer-id <ID>: Avaliação profunda e resolução autônoma para um cliente específico.
- --scan: Varredura proativa da carteira de alto valor em risco de churn com resolução autônoma.
- --interactive: Sessão interativa de chat no terminal com o Concierge corporativo.
- Flags adicionais: --limit, --min-churn, --dry-run, --max-turns.

Exemplos de uso:
  python -m agent.autonomous_agent --customer-id C000004
  python -m agent.autonomous_agent --scan --limit 5 --min-churn 0.50
  python -m agent.autonomous_agent --scan --dry-run
  python -m agent.autonomous_agent --interactive
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

# Garante saída UTF-8 no terminal Windows para evitar UnicodeEncodeError em cp1252
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from agent.autonomous import AuraConciergeAgent
from agent.models import AgentTurnResult


# Estilização ANSI para saída rica no terminal
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def print_banner() -> None:
    """Exibe banner oficial do PROJETO AURA Concierge."""
    print(f"{CYAN}{BOLD}")
    print("+" + "=" * 80 + "+")
    print("|                 PROJETO AURA -- AGENTE AUTÔNOMO DE CRM DE ALTO VALOR             |")
    print("|                    Aura Concierge • Autonomia L1/L2 • Governança                 |")
    print("+" + "=" * 80 + "+")
    print(f"{RESET}")


def format_turn_result(res: AgentTurnResult) -> None:
    """Formata e imprime de maneira estruturada e rica o resultado de um turno."""
    print(f"\n{BOLD}{'-' * 80}{RESET}")
    print(f"{BOLD}>> RESULTADO DO CICLO AUTÔNOMO -- CLIENTE: {CYAN}{res.customer_id or 'N/A'}{RESET}")
    print(f"{DIM}Turnos ReAct: {res.turns} | Motivo Término: {res.finish_reason}{RESET}\n")

    # 1. Raciocínio (Thought Process)
    if res.thought_process:
        print(f"{MAGENTA}{BOLD}[*] Raciocínio Analítico (Thought Process):{RESET}")
        for thought in res.thought_process:
            print(f"  {DIM}•{RESET} {thought}")
        print()

    # 2. Ferramentas Invocadas
    if res.tool_calls_executed:
        print(f"{CYAN}{BOLD}[*] Ferramentas Corporativas Executadas ({len(res.tool_calls_executed)}):{RESET}")
        for t in res.tool_calls_executed:
            tool_name = t.get("tool", "")
            turn = t.get("turn", 1)
            args = t.get("arguments", {})
            summary = t.get("result_summary", "")
            print(f"  {BOLD}[Turno {turn}]{RESET} {CYAN}{tool_name}{RESET}({args})")
            if summary:
                print(f"    {DIM}--> Retorno: {summary[:160]}...{RESET}")
        print()

    # 3. Decisões Tomadas
    if res.decisions_taken:
        print(f"{GREEN}{BOLD}[*] Decisões Registradas no Kanban / Auditoria ({len(res.decisions_taken)}):{RESET}")
        for dec in res.decisions_taken:
            status_color = GREEN if dec.status == "approved" else YELLOW
            status_tag = f"{status_color}[{dec.status.upper()}]{RESET}"
            level_str = "L1 (Automático)" if dec.status == "approved" else "L2 (Revisão Humana)"

            print(f"  • Ação: {BOLD}{dec.action_name}{RESET} (ID: {dec.action_id})")
            print(f"    Status: {status_tag} | Nível: {level_str}")
            print(f"    Operador: {dec.operator} | Timestamp: {dec.timestamp}")
            if dec.notes:
                print(f"    Notas: {DIM}{dec.notes}{RESET}")
            if dec.hash_signature:
                print(f"    Hash SHA-256: {DIM}{dec.hash_signature}{RESET}")
        print()

    # 4. Status de Revisão Humana
    if res.human_review_required:
        print(f"{YELLOW}{BOLD}[!] ALERTA DE GOVERNANÇA: Ação de Autonomia L2 requer homologação de supervisor.{RESET}")
    else:
        print(f"{GREEN}[OK] Conformidade total: Ações dentro da alçada de Autonomia L1 automática.{RESET}")
    print()

    # 5. Mensagem Final
    print(f"{BOLD}[>] Síntese do Concierge:{RESET}")
    for line in res.final_message.splitlines():
        print(f"  {line}")
    print(f"{BOLD}{'-' * 80}{RESET}\n")


def run_interactive(agent: AuraConciergeAgent) -> None:
    """Inicia loop de chat interativo no terminal."""
    print_banner()
    print(f"{GREEN}Iniciando sessão interativa com o Aura Concierge.{RESET}")
    print(f"{DIM}Digite 'sair', 'exit' ou 'quit' para encerrar.{RESET}\n")

    history: list[dict[str, Any]] = []

    while True:
        try:
            user_input = input(f"{BOLD}{CYAN}Aura Concierge > {RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nEncerrando sessão interativa.")
            break

        if not user_input:
            continue

        if user_input.lower() in {"sair", "exit", "quit"}:
            print("Sessão encerrada.")
            break

        try:
            res = agent.chat(user_input, history=history)
            format_turn_result(res)

            # Atualiza histórico da conversa
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": res.final_message})
        except Exception as e:
            print(f"{RED}Erro ao processar mensagem: {e}{RESET}")


def run_scan(
    agent: AuraConciergeAgent,
    limit: int = 5,
    min_churn: float = 0.50,
    dry_run: bool = False,
) -> None:
    """Executa varredura proativa de clientes em risco."""
    print_banner()
    mode_str = f"{YELLOW}[MODO DRY-RUN SIMULADO]{RESET}" if dry_run else f"{GREEN}[MODO EXECUÇÃO REAL]{RESET}"
    print(f"Iniciando Varredura Proativa de Carteira {mode_str}")
    print(f"Parâmetros: Limite={limit} clientes | Churn Mínimo={min_churn:.0%}\n")

    results = agent.scan_and_resolve(limit=limit, min_churn=min_churn, dry_run=dry_run)

    if not results:
        print(f"{YELLOW}Nenhum cliente atendeu aos critérios de risco do scan.{RESET}")
        return

    print(f"\n{BOLD}{'=' * 80}{RESET}")
    print(f"{BOLD}RESUMO DA VARREDURA PROATIVA -- {len(results)} CLIENTES AVALIADOS{RESET}")
    print(f"{BOLD}{'=' * 80}{RESET}\n")

    total_decisions = 0
    total_l1 = 0
    total_l2 = 0

    for i, res in enumerate(results, 1):
        print(f"{BOLD}[{i}/{len(results)}] Cliente: {CYAN}{res.customer_id}{RESET}")
        format_turn_result(res)

        for dec in res.decisions_taken:
            total_decisions += 1
            if dec.status == "approved":
                total_l1 += 1
            elif dec.status == "in_review":
                total_l2 += 1

    print(f"{BOLD}📊 CONSOLIDAÇÃO DO SCAN:{RESET}")
    print(f"  • Clientes Processados: {len(results)}")
    print(f"  • Total de Decisões Registradas: {total_decisions}")
    print(f"  • Autonomia L1 (Aprovadas Automaticamente): {GREEN}{total_l1}{RESET}")
    print(f"  • Autonomia L2 (Encaminhadas p/ Revisão Humana): {YELLOW}{total_l2}{RESET}")
    if dry_run:
        print(f"  {YELLOW}• Nenhuma alteração foi gravada em disco (Dry-Run).{RESET}")
    print()


def run_single_customer(agent: AuraConciergeAgent, customer_id: str) -> None:
    """Executa diagnóstico e resolução para um único cliente."""
    print_banner()
    print(f"Iniciando Diagnóstico e Ação de Retenção para o cliente: {CYAN}{BOLD}{customer_id}{RESET}\n")
    res = agent.evaluate_and_act(customer_id)
    format_turn_result(res)


def main() -> None:
    """Ponto de entrada do script CLI."""
    parser = argparse.ArgumentParser(
        description="Aura Concierge — Agente Autônomo de CRM de Alto Valor (Azul Fidelidade)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--customer-id",
        type=str,
        default=None,
        help="ID de um cliente específico para avaliação detalhada (ex: C000004).",
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Executa varredura proativa em clientes de alto valor com risco de churn.",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Inicia sessão conversacional interativa no terminal.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Quantidade máxima de clientes a processar na varredura (padrão: 5).",
    )
    parser.add_argument(
        "--min-churn",
        type=float,
        default=0.50,
        help="Probabilidade mínima de churn no scan (padrão: 0.50).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Executa em modo de simulação, sem persistir registros em decisions.jsonl.",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=8,
        help="Número máximo de turnos por ciclo ReAct (padrão: 8).",
    )

    args = parser.parse_args()

    agent = AuraConciergeAgent(max_turns=args.max_turns)

    if args.interactive:
        run_interactive(agent)
    elif args.scan:
        run_scan(agent, limit=args.limit, min_churn=args.min_churn, dry_run=args.dry_run)
    elif args.customer_id:
        run_single_customer(agent, args.customer_id)
    else:
        # Padrão amigável: se nenhum modo especificado, mostra o help ou avalia cliente modelo
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
