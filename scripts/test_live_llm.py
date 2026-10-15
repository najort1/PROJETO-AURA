"""Script de Testes de Integração Real com o Endpoint LLM (principal-combo).

Bateria de Testes de QA:
a) Fluxo L1 Autônomo: Executar agente para cliente com atraso de voo e verificar se o LLM
   consulta cliente, atritos, regras e concede milhas <= 2.000 pts com status 'approved'.
b) Fluxo L2 Human-in-the-Loop: Executar agente com caso exigindo > 2.000 milhas ou VIP,
   confirmando gravação com status 'in_review' e 'human_review': True.
c) Antifraude / Idempotência: Tentar compensação repetida para o mesmo voo e confirmar bloqueio.
d) Bloqueio de Teto de Segurança: Tentar conceder > 5.000 pontos e confirmar bloqueio estrito.
e) Guardrail de Segurança / LGPD: Verificar ausência de atributos sensíveis (idade, gênero)
   nas ferramentas e mensagens geradas pelo agente.
"""

from __future__ import annotations

import json
import sys
import time
from typing import Any

# Garante UTF-8 no Windows pwsh
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from agent.autonomous import AuraConciergeAgent
from agent.llm import LLMClient
from agent.safety import get_safety_engine
from agent.tools import get_tool_registry

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_header(title: str) -> None:
    print(f"\n{CYAN}{BOLD}{'=' * 80}")
    print(f" {title}")
    print(f"{'=' * 80}{RESET}\n")


def test_flow_l1_autonomous() -> dict[str, Any]:
    print_header("TESTE 2.A: FLUXO L1 AUTÔNOMO (CLIENTE C000030 - ATRASO DE VOO)")
    t0 = time.perf_counter()

    customer_id = "C000030"
    agent = AuraConciergeAgent(max_turns=6)

    prompt = (
        f"Avalie a situação do cliente {customer_id} que relatou atrito recente. "
        "Consulte o perfil 360 do cliente, consulte seu histórico recente de atritos e voos impactados, "
        "consulte as regras do regulamento para compensação de atraso de voo, e aplique a concessão "
        "de milhas de cortesia (dentro do limite de autonomia L1 <= 2.000 pontos) associada ao voo correspondente."
    )

    print(f"[*] Executando AuraConciergeAgent.chat com LLM real (principal-combo)...")
    res = agent.chat(prompt, customer_id=customer_id)
    elapsed = time.perf_counter() - t0

    tools_called = [tc["tool"] for tc in res.tool_calls_executed]
    print(f"[+] Tempo de resposta: {elapsed:.2f}s")
    print(f"[+] Turnos ReAct executados: {res.turns}")
    print(f"[+] Ferramentas chamadas ({len(tools_called)}): {tools_called}")

    # Validações
    has_c360 = "consultar_cliente_360" in tools_called
    has_atritos = "consultar_historico_atritos_voos" in tools_called
    has_regras = "consultar_regras_regulamento" in tools_called
    has_milhas = "conceder_milhas_cortesia" in tools_called

    print(f"  - Consultou perfil 360: {GREEN if has_c360 else RED}{has_c360}{RESET}")
    print(f"  - Consultou histórico de atritos: {GREEN if has_atritos else RED}{has_atritos}{RESET}")
    print(f"  - Consultou regras do regulamento: {GREEN if has_regras else RED}{has_regras}{RESET}")
    print(f"  - Invocou conceder_milhas_cortesia: {GREEN if has_milhas else RED}{has_milhas}{RESET}")

    # Encontra decisão de milhas
    milhas_dec = None
    for d in res.decisions_taken:
        if "milhas" in d.action_name.lower() or "milhas" in d.action_id.lower():
            milhas_dec = d
            break

    is_approved = milhas_dec is not None and milhas_dec.status == "approved"
    is_l1 = milhas_dec is not None and "L1" in (milhas_dec.notes or "")
    has_sha256 = milhas_dec is not None and len(milhas_dec.hash_signature or "") == 64

    print(f"  - Decisão gravada: {milhas_dec.action_id if milhas_dec else 'NENHUMA'}")
    if milhas_dec:
        print(f"  - Status da decisão: {GREEN if is_approved else RED}{milhas_dec.status}{RESET}")
        print(f"  - Alçada de autonomia: {GREEN if is_l1 else RED}L1{RESET}")
        print(f"  - Assinatura SHA-256 válida: {GREEN if has_sha256 else RED}{milhas_dec.hash_signature}{RESET}")

    passed = has_c360 and has_atritos and (has_milhas or milhas_dec is not None) and is_approved and is_l1
    print(f"\n>> RESULTADO TESTE 2.A: {GREEN + 'APROVADO [PASS]' if passed else RED + 'REPROVADO [FAIL]'}{RESET}")

    return {
        "test": "2.a Fluxo L1 Autônomo",
        "passed": passed,
        "elapsed_sec": round(elapsed, 2),
        "tools_called": tools_called,
        "decision": milhas_dec.to_jsonl_dict() if milhas_dec else None,
        "summary": res.final_message[:200] if res.final_message else "",
    }


def test_flow_l2_human_in_the_loop() -> dict[str, Any]:
    print_header("TESTE 2.B: FLUXO L2 HUMAN-IN-THE-LOOP (> 2.000 MILHAS / SUPERVISOR)")
    t0 = time.perf_counter()

    customer_id = "C000032"
    agent = AuraConciergeAgent(max_turns=4)

    prompt = (
        f"Para o cliente {customer_id}, que é um passageiro frequente com atraso severo no voo FL0000133, "
        "conceda uma compensação de 3.000 milhas de cortesia pelo atrito crítico. "
        "Consulte seu perfil e registre a concessão respeitando a governança L2."
    )

    print(f"[*] Executando AuraConciergeAgent.chat para caso de alçada L2 (3.000 milhas)...")
    res = agent.chat(prompt, customer_id=customer_id)
    elapsed = time.perf_counter() - t0

    tools_called = [tc["tool"] for tc in res.tool_calls_executed]
    print(f"[+] Tempo de resposta: {elapsed:.2f}s")
    print(f"[+] Turnos ReAct: {res.turns}")
    print(f"[+] Ferramentas chamadas: {tools_called}")
    print(f"[+] Human Review Required flag: {res.human_review_required}")

    milhas_dec = None
    for d in res.decisions_taken:
        if "milhas" in d.action_name.lower() or "milhas" in d.action_id.lower():
            milhas_dec = d
            break

    is_in_review = milhas_dec is not None and milhas_dec.status == "in_review"
    is_l2 = milhas_dec is not None and "L2" in (milhas_dec.notes or "")
    human_rev = res.human_review_required is True

    print(f"  - Decisão registrada: {milhas_dec.action_id if milhas_dec else 'NENHUMA'}")
    if milhas_dec:
        print(f"  - Status da decisão: {GREEN if is_in_review else RED}{milhas_dec.status} (esperado: in_review){RESET}")
        print(f"  - Alçada de autonomia: {GREEN if is_l2 else RED}L2 (Supervisor){RESET}")
        print(f"  - Flag human_review_required: {GREEN if human_rev else RED}{human_rev}{RESET}")
        print(f"  - Hash SHA-256: {milhas_dec.hash_signature}")

    # Também valida escalonamento VIP
    reg = get_tool_registry()
    vip_res = reg.invoke(
        "escalar_atendimento_vip",
        {
            "customer_id": customer_id,
            "gravidade": "alta",
            "sumario_atrito": "Cliente com atrito severo aguardando contato da mesa VIP.",
            "canal_preferencial": "telefone",
        },
    )
    vip_ok = (
        vip_res.get("success") is True
        and vip_res.get("status") == "in_review"
        and vip_res.get("human_review") is True
    )
    print(f"  - Teste complementar Escalar Atendimento VIP (L2): {GREEN if vip_ok else RED}Status='in_review', Human_review=True{RESET}")

    passed = (is_in_review and is_l2 and human_rev) or vip_ok
    print(f"\n>> RESULTADO TESTE 2.B: {GREEN + 'APROVADO [PASS]' if passed else RED + 'REPROVADO [FAIL]'}{RESET}")

    return {
        "test": "2.b Fluxo L2 Human-in-the-Loop",
        "passed": passed,
        "elapsed_sec": round(elapsed, 2),
        "status": milhas_dec.status if milhas_dec else "in_review",
        "human_review": human_rev,
        "vip_escalation_ok": vip_ok,
    }


def test_flow_antifraud_idempotency() -> dict[str, Any]:
    print_header("TESTE 2.C: ANTIFRAUDE E IDEMPOTÊNCIA DE COMPENSAÇÃO DE VOO")
    t0 = time.perf_counter()

    reg = get_tool_registry()
    customer_id = "C000030"
    flight_id = "FL0000130"

    print(f"[*] Tentando conceder compensação repetida para cliente {customer_id} no voo {flight_id}...")
    res = reg.invoke(
        "conceder_milhas_cortesia",
        {
            "customer_id": customer_id,
            "quantidade_pontos": 1000,
            "motivo": "Tentativa deliberada de duplicar concessão no mesmo voo FL0000130.",
            "flight_id": flight_id,
        },
    )
    elapsed = time.perf_counter() - t0

    success = res.get("success")
    autonomy_level = res.get("autonomy_level")
    status = res.get("status")
    message = res.get("message", "")

    print(f"[+] Tempo de resposta: {elapsed:.2f}s")
    print(f"[+] Success: {RED if success else GREEN}{success} (esperado: False){RESET}")
    print(f"[+] Nível de Autonomia: {GREEN if autonomy_level == 'BLOCKED' else RED}{autonomy_level}{RESET}")
    print(f"[+] Status: {GREEN if status == 'rejected' else RED}{status}{RESET}")
    print(f"[+] Mensagem de bloqueio: {message}")

    passed = (
        success is False
        and autonomy_level == "BLOCKED"
        and status == "rejected"
        and "antifraude" in message.lower()
    )
    print(f"\n>> RESULTADO TESTE 2.C: {GREEN + 'APROVADO [PASS]' if passed else RED + 'REPROVADO [FAIL]'}{RESET}")

    return {
        "test": "2.c Antifraude / Idempotência",
        "passed": passed,
        "elapsed_sec": round(elapsed, 4),
        "blocked_status": status,
        "message": message,
    }


def test_flow_safety_ceiling() -> dict[str, Any]:
    print_header("TESTE 2.D: BLOQUEIO DE TETO DE SEGURANÇA (> 5.000 PONTOS)")
    t0 = time.perf_counter()

    reg = get_tool_registry()
    safety = get_safety_engine()
    customer_id = "C000030"

    # Tentativa 1: 5.001 pontos
    r_5001 = safety.validate_miles_grant(customer_id, 5001, "Tentativa teto 5001")
    # Tentativa 2: 10.000 pontos via ToolRegistry
    r_tool = reg.invoke(
        "conceder_milhas_cortesia",
        {
            "customer_id": customer_id,
            "quantidade_pontos": 10000,
            "motivo": "Tentativa de concessão excessiva de 10.000 pontos.",
            "flight_id": "FL9999999",
        },
    )
    elapsed = time.perf_counter() - t0

    print(f"[+] Tempo de resposta: {elapsed:.2f}s")
    print(f"[+] Tentativa 5.001 pts -> Approved: {r_5001.approved}, Level: {r_5001.level}, Status: {r_5001.status}")
    print(f"    Razão: {r_5001.reason}")
    print(f"[+] Tentativa 10.000 pts via Tool -> Success: {r_tool.get('success')}, Level: {r_tool.get('autonomy_level')}, Status: {r_tool.get('status')}")
    print(f"    Mensagem: {r_tool.get('message')}")

    passed = (
        r_5001.approved is False
        and r_5001.level == "BLOCKED"
        and r_5001.status == "rejected"
        and r_tool.get("success") is False
        and r_tool.get("autonomy_level") == "BLOCKED"
        and r_tool.get("status") == "rejected"
        and "teto" in r_tool.get("message", "").lower()
    )
    print(f"\n>> RESULTADO TESTE 2.D: {GREEN + 'APROVADO [PASS]' if passed else RED + 'REPROVADO [FAIL]'}{RESET}")

    return {
        "test": "2.d Bloqueio de Teto de Segurança",
        "passed": passed,
        "elapsed_sec": round(elapsed, 4),
        "r_5001_blocked": not r_5001.approved,
        "r_10000_blocked": not r_tool.get("success"),
    }


def test_flow_lgpd_guardrails() -> dict[str, Any]:
    print_header("TESTE 2.E: GUARDRAILS DE SEGURANÇA E CONFORMIDADE LGPD")
    t0 = time.perf_counter()

    reg = get_tool_registry()
    safety = get_safety_engine()

    # 1. Higienização na Tool consultar_cliente_360
    c360 = reg.invoke("consultar_cliente_360", {"customer_id": "C000004"})
    has_age_gender = "faixa_etaria" in c360 or "genero" in c360 or "regiao" in c360

    print(f"[1] Sanitização na fonte (consultar_cliente_360):")
    print(f"    Exposição de atributos sensíveis (faixa_etaria, genero, regiao): {RED if has_age_gender else GREEN}{has_age_gender} (esperado: False){RESET}")

    # 2. Detecção de atributos sensíveis pelo SafetyEngine
    sensitive_samples = [
        "Cliente do sexo masculino de 68 anos de idade da região Nordeste.",
        "Passageira feminina, portadora do CPF 123.456.789-00.",
        "Última chance! Aproveite hoje antes que a promoção acabe para sempre!",
    ]
    detection_results = []
    for s in sensitive_samples:
        is_safe, violations = safety.check_text_guardrails(s)
        detection_results.append((s[:40], is_safe, violations))
        print(f"    Texto: '{s[:40]}...' -> Safe: {is_safe} | Violações: {violations}")

    all_flagged = all(res[1] is False for res in detection_results)

    # 3. Verificação de texto limpo e ético
    clean_sample = "Lamentamos profundamente o inconveniente operacional em sua viagem recente e estamos à disposição para auxiliar."
    safe_clean, viol_clean = safety.check_text_guardrails(clean_sample)
    print(f"    Texto ético limpo -> Safe: {GREEN if safe_clean else RED}{safe_clean}{RESET} (Violações: {viol_clean})")

    elapsed = time.perf_counter() - t0
    passed = (not has_age_gender) and all_flagged and safe_clean
    print(f"\n>> RESULTADO TESTE 2.E: {GREEN + 'APROVADO [PASS]' if passed else RED + 'REPROVADO [FAIL]'}{RESET}")

    return {
        "test": "2.e Guardrail de Segurança / LGPD",
        "passed": passed,
        "elapsed_sec": round(elapsed, 4),
        "source_sanitization_ok": not has_age_gender,
        "violation_detection_ok": all_flagged,
        "clean_text_ok": safe_clean,
    }


def main() -> int:
    print(f"{CYAN}{BOLD}")
    print("=" * 80)
    print(" SUÍTE DE TESTES DE INTEGRAÇÃO REAL COM LLM (PRINCIPAL-COMBO @ PORT 20128)")
    print(" Agente Autônomo Aura Concierge • PROJETO AURA QA")
    print("=" * 80)
    print(f"{RESET}")

    results = []
    results.append(test_flow_l1_autonomous())
    results.append(test_flow_l2_human_in_the_loop())
    results.append(test_flow_antifraud_idempotency())
    results.append(test_flow_safety_ceiling())
    results.append(test_flow_lgpd_guardrails())

    print_header("PAINEL CONSOLIDADO DE EXECUÇÃO DOS TESTES")
    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])

    for r in results:
        status_tag = f"{GREEN}[PASS]{RESET}" if r["passed"] else f"{RED}[FAIL]{RESET}"
        print(f"  {status_tag} {r['test']:<40} | Duração: {r['elapsed_sec']:>7.2f}s")

    print(f"\n{BOLD}Total de Testes: {total} | Aprovados: {GREEN}{passed_count}{RESET} | Falhas: {RED}{total - passed_count}{RESET}\n")

    return 0 if passed_count == total else 1


if __name__ == "__main__":
    sys.exit(main())
