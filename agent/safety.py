"""Motor de Governança, Políticas de Segurança e Autonomia (SafetyEngine).

Implementa:
- Autonomia L1: milhas <= 2.000 e vouchers de serviço aprovados automaticamente (status="approved").
- Autonomia L2: milhas > 2.000 (até 5.000) e escalonamentos VIP encaminhados para revisão humana (status="in_review").
- Teto Orçamentário: concessões acima de 5.000 pontos estritamente bloqueadas.
- Idempotência Antifraude: bloqueio de compensações duplicadas para o mesmo flight_id e cliente em decisions.jsonl.
- Assinatura criptográfica SHA-256 idêntica aos contratos de Next.js e Streamlit.
- Guardrails LGPD, sanitização de linguagem manipulativa e proteção anti-injeção.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import threading
import unicodedata
from pathlib import Path
from typing import Any

from agent.guardrails import (
    FABRICATED_BENEFIT_PATTERNS,
    PROMPT_INJECTION_VARIANTS,
    SENSITIVE_PATTERNS,
    URGENCY_PATTERNS,
)
from agent.models import DecisionRecord, DecisionStatus, SafetyCheckResult
from aura_core.log import get_logger
from aura_core.paths import ROOT

logger = get_logger("agent.safety")

ANALYTICS_DIR = ROOT / "data" / "analytics"
DECISIONS_FILE = ANALYTICS_DIR / "decisions.jsonl"

# Limites corporativos inegociáveis de autonomia
MAX_POINTS_WITHOUT_FLIGHT = 1000
MAX_POINTS_L1_AUTO_APPROVE = 2000
MAX_POINTS_L2_HUMAN_REVIEW = 5000
MAX_POINTS_ABSOLUTE_CEILING = 5000


class SafetyEngine:
    """Motor central de segurança, conformidade e governança de autonomia para o Aura Concierge."""

    _file_lock = threading.Lock()

    def __init__(self, decisions_path: Path | None = None) -> None:
        self.decisions_path = decisions_path or DECISIONS_FILE
        self._compiled_sensitive = [re.compile(p, re.IGNORECASE) for p in SENSITIVE_PATTERNS]
        self._compiled_urgency = [re.compile(p, re.IGNORECASE) for p in URGENCY_PATTERNS]
        self._compiled_fabricated = [
            re.compile(p, re.IGNORECASE) for p in FABRICATED_BENEFIT_PATTERNS
        ]
        self._compiled_injection = [re.compile(p, re.IGNORECASE) for p in PROMPT_INJECTION_VARIANTS]

    @staticmethod
    def calculate_hash(
        timestamp: str,
        customer_id: str,
        action_id: str,
        status: str,
        operator: str,
        final_message: str,
    ) -> str:
        """Cálculo de hash SHA-256 criptográfico rigorosamente compatível com Next.js.

        Formula: sha256(f"{timestamp}|{customer_id}|{action_id}|{status}|{operator}|{final_message.strip()}")
        """
        payload = (
            f"{timestamp}|{customer_id}|{action_id}|{status}|{operator}|{final_message.strip()}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def check_text_guardrails(self, text: str) -> tuple[bool, list[str]]:
        """Valida o texto proposto contra violações de LGPD, urgência e promessas abusivas."""
        if not text or not text.strip():
            return True, []

        norm_text = (
            unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8").lower()
        )
        violations: list[str] = []

        # 1. Checagem de dados sensíveis (LGPD)
        for pattern in self._compiled_sensitive:
            if pattern.search(norm_text):
                violations.append(
                    "LGPD: Uso indevido de atributos sensíveis (idade, gênero, documentos ou região)."
                )
                break

        # 2. Checagem de tom abusivo / escassez artificial
        for pattern in self._compiled_urgency:
            if pattern.search(norm_text):
                violations.append(
                    "Tom Abusivo: Expressão de urgência manipulativa ou escassez artificial detectada."
                )
                break

        # 3. Promessas de benefícios inexistentes
        for pattern in self._compiled_fabricated:
            if pattern.search(norm_text):
                violations.append(
                    "Benefício Inexistente: Promessa de gratuidade vitalícia ou vantagem fora de regulamento."
                )
                break

        # 4. Injeção de prompt
        for pattern in self._compiled_injection:
            if pattern.search(norm_text):
                violations.append("Segurança: Padrão associado a prompt-injection detectado.")
                break

        is_safe = len(violations) == 0
        return is_safe, violations

    def check_antifraud_flight_id(self, customer_id: str, flight_id: str) -> tuple[bool, str]:
        """Verifica se já existe compensação prévia registrada para o mesmo voo e cliente.

        Garante idempotência estrita antifraude consultando decisions.jsonl com word-boundary regex.
        """
        if not flight_id or not flight_id.strip():
            return True, "Flight ID não informado; verificação de voo ignorada."

        norm_customer = customer_id.strip().upper()
        norm_flight = flight_id.strip().upper()
        flight_pattern = re.compile(r"\b" + re.escape(norm_flight) + r"\b")

        if not self.decisions_path.exists():
            return True, "Arquivo de decisões ainda não existe; sem registros prévios."

        with self._file_lock:
            try:
                with open(self.decisions_path, encoding="utf-8") as f:
                    for _line_no, line in enumerate(f, start=1):
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            record = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        # Se for de outro cliente, ignora
                        if str(record.get("customer_id", "")).strip().upper() != norm_customer:
                            continue

                        # Decisões rejeitadas não bloqueiam nova tentativa
                        if record.get("status") == "rejected":
                            continue

                        # Procura o flight_id em action_id, notes, original_message ou final_message com word boundary
                        rec_notes = str(record.get("notes") or "").upper()
                        rec_action = str(record.get("action_id") or "").upper()
                        rec_msg = str(record.get("final_message") or "").upper()
                        rec_orig = str(record.get("original_message") or "").upper()

                        if (
                            flight_pattern.search(rec_notes)
                            or flight_pattern.search(rec_action)
                            or flight_pattern.search(rec_msg)
                            or flight_pattern.search(rec_orig)
                        ):
                            return (
                                False,
                                f"Idempotência antifraude: Compensação já registrada anteriormente para "
                                f"o cliente {customer_id} no voo {flight_id} (ação: {record.get('action_id')}, "
                                f"status: {record.get('status')}).",
                            )
            except Exception as e:
                logger.error(
                    "Erro ao verificar duplicidade de voo em %s: %s", self.decisions_path, e
                )
                # FAIL-CLOSED [CON-01]
                return False, "Erro de I/O ao verificar duplicidade: bloqueio preventivo ativado."

        return True, "Nenhuma duplicidade encontrada para este voo."

    @staticmethod
    def _extract_points_from_record(record: dict[str, Any]) -> int:
        """Extrai a quantidade de pontos/milhas concedidos em um registro de decisão."""
        action_name = str(record.get("action_name") or "")
        m = re.match(r"^concessao_milhas_(\d+)$", action_name, re.IGNORECASE)
        if m:
            return int(m.group(1))

        action_id = str(record.get("action_id") or "")
        m2 = re.search(r"ACT-MILHAS-(\d+)(?:PTS)?", action_id, re.IGNORECASE)
        if m2:
            return int(m2.group(1))

        if "milhas" in action_name.lower() or "milhas" in action_id.lower():
            for text_field in ("final_message", "original_message", "notes"):
                txt = str(record.get(text_field) or "")
                m3 = re.search(r"(\d+)\s*(?:milhas|pontos)", txt, re.IGNORECASE)
                if m3:
                    return int(m3.group(1))

        return 0

    def check_monthly_budget_cap(
        self,
        customer_id: str,
        new_points: int,
        cap: int = 5000,
        current_time: dt.datetime | None = None,
    ) -> tuple[bool, str]:
        """Calcula a soma de pontos concedidos nos últimos 30 dias para o cliente em decisions.jsonl.

        Considera apenas decisões com status in {"approved", "completed", "in_review"}.
        Se soma + new_points > cap, retorna False (bloqueio por teto orçamentário cumulativo).
        """
        if not self.decisions_path.exists():
            if new_points > cap:
                return (
                    False,
                    f"Teto orçamentário de {cap} pontos excedido na concessão ({new_points} pontos solicitados).",
                )
            return True, "Arquivo de decisões ainda não existe; sem registros prévios."

        norm_customer = customer_id.strip().upper()
        now = current_time or dt.datetime.now(dt.UTC)
        thirty_days_ago = now - dt.timedelta(days=30)
        total_granted = 0

        with self._file_lock:
            try:
                with open(self.decisions_path, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            record = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        if str(record.get("customer_id", "")).strip().upper() != norm_customer:
                            continue

                        status = str(record.get("status", "")).lower()
                        if status not in {"approved", "completed", "in_review"}:
                            continue

                        ts_str = str(record.get("timestamp") or "")
                        in_window = True
                        if ts_str:
                            try:
                                ts = dt.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                                if ts.tzinfo is None:
                                    ts = ts.replace(tzinfo=dt.UTC)
                                if ts < thirty_days_ago:
                                    in_window = False
                            except Exception:
                                in_window = True

                        if not in_window:
                            continue

                        pts = self._extract_points_from_record(record)
                        total_granted += pts

            except Exception as e:
                logger.error(
                    "Erro ao verificar teto orçamentário em %s: %s", self.decisions_path, e
                )
                # FAIL-CLOSED [CON-01]
                return (
                    False,
                    "Erro de I/O ao verificar teto orçamentário mensal: bloqueio preventivo ativado.",
                )

        if total_granted + new_points > cap:
            return (
                False,
                f"Teto cumulativo de 30 dias excedido para o cliente {customer_id}: "
                f"já concedidos {total_granted} pts nos últimos 30 dias com status elegível; "
                f"solicitados {new_points} pts (acumulado resultaria em {total_granted + new_points} pts > limite de {cap} pts).",
            )

        return True, f"Teto mensal respeitado: {total_granted} pts concedidos nos últimos 30 dias."

    def validate_miles_grant(
        self,
        customer_id: str,
        quantidade_pontos: int,
        motivo: str,
        flight_id: str | None = None,
    ) -> SafetyCheckResult:
        """Avalia concessão de milhas quanto a limites L1/L2, teto, limite sem voo, teto mensal e antifraude."""
        if quantidade_pontos <= 0:
            return SafetyCheckResult(
                approved=False,
                level="BLOCKED",
                status="rejected",
                human_review=False,
                reason="Quantidade de pontos deve ser estritamente positiva.",
                violations=["Pontos <= 0 inválidos."],
            )

        # 1. Concessão sem flight_id: limitar a no máximo 1.000 pontos [FIN-01]
        norm_flight = flight_id.strip() if flight_id and flight_id.strip() else None
        if not norm_flight and quantidade_pontos > MAX_POINTS_WITHOUT_FLIGHT:
            return SafetyCheckResult(
                approved=False,
                level="BLOCKED",
                status="rejected",
                human_review=False,
                reason=(
                    f"Concessão de milhas sem flight_id limitada ao teto de {MAX_POINTS_WITHOUT_FLIGHT} pontos "
                    f"(solicitado: {quantidade_pontos} pontos)."
                ),
                violations=["Concessão sem flight_id acima de 1.000 pontos."],
            )

        # 2. Idempotência por flight_id
        if norm_flight:
            ok, antifraud_msg = self.check_antifraud_flight_id(customer_id, norm_flight)
            if not ok:
                return SafetyCheckResult(
                    approved=False,
                    level="BLOCKED",
                    status="rejected",
                    human_review=False,
                    reason=antifraud_msg,
                    violations=["Tentativa de compensação duplicada para o mesmo voo."],
                )

        # 3. Teto orçamentário cumulativo dos últimos 30 dias (máximo 5.000 pontos) [FIN-01]
        cap_ok, cap_msg = self.check_monthly_budget_cap(
            customer_id=customer_id,
            new_points=quantidade_pontos,
            cap=MAX_POINTS_ABSOLUTE_CEILING,
        )
        if not cap_ok:
            return SafetyCheckResult(
                approved=False,
                level="BLOCKED",
                status="rejected",
                human_review=False,
                reason=cap_msg,
                violations=["Teto orçamentário mensal de 5.000 pontos excedido."],
            )

        # 4. Guardrails de texto no motivo [SEC-01: FAIL-CLOSED / BLOQUEIO EFETIVO]
        is_safe, text_violations = self.check_text_guardrails(motivo)
        if not is_safe:
            return SafetyCheckResult(
                approved=False,
                level="BLOCKED",
                status="rejected",
                human_review=False,
                reason=f"Bloqueado por violação de conformidade: {'; '.join(text_violations)}",
                violations=text_violations,
            )

        # 5. Avaliação de Teto Absoluto e Nível de Autonomia
        if quantidade_pontos > MAX_POINTS_ABSOLUTE_CEILING:
            return SafetyCheckResult(
                approved=False,
                level="BLOCKED",
                status="rejected",
                human_review=False,
                reason=(
                    f"Teto orçamentário estrito violado: {quantidade_pontos} pontos solicitados, "
                    f"acima do limite máximo absoluto de {MAX_POINTS_ABSOLUTE_CEILING} pontos."
                ),
                violations=["Excesso de teto orçamentário (> 5.000 pontos)."],
            )

        if quantidade_pontos <= MAX_POINTS_L1_AUTO_APPROVE:
            # Autonomia L1: Aprovação automática
            return SafetyCheckResult(
                approved=True,
                level="L1",
                status="approved",
                human_review=False,
                reason=f"Autonomia L1: {quantidade_pontos} pontos dentro do limite automático (<= 2.000). Aprovado.",
                violations=[],
            )
        else:
            # Autonomia L2: Exige revisão humana
            return SafetyCheckResult(
                approved=True,
                level="L2",
                status="in_review",
                human_review=True,
                reason=(
                    f"Autonomia L2: {quantidade_pontos} pontos supera a alçada L1 (2.000) e requer "
                    f"homologação de supervisor (status='in_review')."
                ),
                violations=[],
            )

    def validate_voucher_issue(
        self,
        customer_id: str,
        tipo_servico: str,
        motivo: str,
        flight_id: str | None = None,
    ) -> SafetyCheckResult:
        """Avalia emissão de vouchers de serviço (Autonomia L1 para conveniências)."""
        valid_services = {
            "lounge",
            "bagagem",
            "upgrade_cabine",
            "wi-fi",
            "wifi",
            "refeicao_aeroporto",
            "refeicao",
            "estacionamento",
        }

        norm_serv = tipo_servico.lower().strip()
        if not any(k in norm_serv for k in valid_services):
            return SafetyCheckResult(
                approved=False,
                level="BLOCKED",
                status="rejected",
                human_review=False,
                reason=f"Tipo de serviço de voucher inválido: {tipo_servico!r}.",
                violations=[f"Serviço não catalogado: {tipo_servico}"],
            )

        # Checagem antifraude por voo
        if flight_id and flight_id.strip():
            ok, antifraud_msg = self.check_antifraud_flight_id(customer_id, flight_id.strip())
            if not ok:
                return SafetyCheckResult(
                    approved=False,
                    level="BLOCKED",
                    status="rejected",
                    human_review=False,
                    reason=antifraud_msg,
                    violations=["Tentativa de voucher duplicado para o mesmo voo."],
                )

        # Guardrails de texto [SEC-01: FAIL-CLOSED / BLOQUEIO EFETIVO]
        is_safe, text_violations = self.check_text_guardrails(motivo)
        if not is_safe:
            return SafetyCheckResult(
                approved=False,
                level="BLOCKED",
                status="rejected",
                human_review=False,
                reason=f"Bloqueado por violação de conformidade: {'; '.join(text_violations)}",
                violations=text_violations,
            )

        # Vouchers de conveniência pertencem à alçada L1
        return SafetyCheckResult(
            approved=True,
            level="L1",
            status="approved",
            human_review=False,
            reason=f"Autonomia L1: Voucher de conveniência '{tipo_servico}' aprovado automaticamente.",
            violations=[],
        )

    def validate_vip_escalation(
        self,
        customer_id: str,
        gravidade: str,
        sumario_atrito: str,
    ) -> SafetyCheckResult:
        """Avalia escalonamento para mesa VIP (Autonomia L2 obrigatória: in_review)."""
        # Guardrails de texto [SEC-01: FAIL-CLOSED / BLOQUEIO EFETIVO]
        is_safe, text_violations = self.check_text_guardrails(sumario_atrito)
        if not is_safe:
            return SafetyCheckResult(
                approved=False,
                level="BLOCKED",
                status="rejected",
                human_review=False,
                reason=f"Bloqueado por violação de conformidade: {'; '.join(text_violations)}",
                violations=text_violations,
            )

        return SafetyCheckResult(
            approved=True,
            level="L2",
            status="in_review",
            human_review=True,
            reason=f"Autonomia L2: Escalonamento para mesa VIP com gravidade '{gravidade}' requer acompanhamento humano.",
            violations=[],
        )

    def validate_kanban_proposal(
        self,
        customer_id: str,
        action_id: str,
        action_name: str,
        mensagem: str,
        justificativa: str,
        status_proposto: str = "suggested",
    ) -> SafetyCheckResult:
        """Valida proposta de ação para o Kanban de decisões."""
        # Guardrails de texto [SEC-01: FAIL-CLOSED / BLOQUEIO EFETIVO]
        is_safe_msg, msg_violations = self.check_text_guardrails(mensagem)
        is_safe_just, just_violations = self.check_text_guardrails(justificativa)
        all_violations = msg_violations + just_violations
        if not is_safe_msg or not is_safe_just:
            return SafetyCheckResult(
                approved=False,
                level="BLOCKED",
                status="rejected",
                human_review=False,
                reason=f"Bloqueado por violação de conformidade: {'; '.join(all_violations)}",
                violations=all_violations,
            )

        status_final: DecisionStatus = (
            status_proposto
            if status_proposto in ["suggested", "in_review", "approved"]
            else "suggested"
        )
        needs_human = status_final in ["suggested", "in_review"]
        level: Any = "L2" if needs_human else "L1"

        return SafetyCheckResult(
            approved=True,
            level=level,
            status=status_final,
            human_review=needs_human,
            reason=f"Ação proposta registrada para fluxo Kanban com status '{status_final}'.",
            violations=[],
        )

    def persist_decision(self, record: DecisionRecord) -> DecisionRecord:
        """Registra a decisão em decisions.jsonl com assinatura SHA-256 e thread-safety."""
        # Garante hash preenchido
        if not record.hash_signature:
            record.hash_signature = record.compute_hash()

        # Garante diretório pai
        self.decisions_path.parent.mkdir(parents=True, exist_ok=True)

        with self._file_lock:
            payload_line = json.dumps(record.to_jsonl_dict(), ensure_ascii=False)
            with open(self.decisions_path, "a", encoding="utf-8") as f:
                f.write(payload_line + "\n")

        logger.info(
            "Decisão gravada em decisions.jsonl: cliente=%s acao=%s status=%s hash=%s...",
            record.customer_id,
            record.action_id,
            record.status,
            record.hash_signature[:12] if record.hash_signature else "none",
        )
        return record


_DEFAULT_SAFETY_ENGINE: SafetyEngine | None = None


def get_safety_engine() -> SafetyEngine:
    """Retorna instância singleton do SafetyEngine."""
    global _DEFAULT_SAFETY_ENGINE
    if _DEFAULT_SAFETY_ENGINE is None:
        _DEFAULT_SAFETY_ENGINE = SafetyEngine()
    return _DEFAULT_SAFETY_ENGINE
