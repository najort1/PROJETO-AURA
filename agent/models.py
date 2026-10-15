"""Modelos Pydantic para o Agente Autônomo de CRM de Alto Valor (Aura Concierge).

Define schemas rigorosos para:
- Requisições e respostas de tools corporativas.
- Registro de decisão (DecisionRecord) compatível com Next.js e Streamlit.
- Turnos de execução do agente ReAct (AgentTurnResult, ToolCallRequest, SafetyCheckResult).
"""

from __future__ import annotations

import datetime as dt
import hashlib
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


# Status permitidos de decisão (estritamente alinhados a dashboard/src/types/actions.ts e app/loader.py)
DecisionStatus = Literal[
    "suggested",
    "in_review",
    "approved",
    "edited",
    "dispatched",
    "completed",
    "rejected",
]

AutonomyLevel = Literal["L1", "L2", "BLOCKED"]


def generate_iso_timestamp() -> str:
    """Gera timestamp UTC no formato ISO estritamente compatível com Next.js (terminação Z sem +00:00)."""
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


class DecisionRecord(BaseModel):
    """Registro de decisão auditável, idêntico aos contratos de Next.js e Streamlit.

    Armazenado em `data/analytics/decisions.jsonl`.
    """

    timestamp: str = Field(
        default_factory=generate_iso_timestamp,
        description="Timestamp ISO-8601 UTC do momento da decisão.",
    )

    @field_validator("timestamp", mode="before")
    @classmethod
    def normalize_timestamp_iso(cls, v: Any) -> str:
        """Normaliza timestamp ISO para terminação 'Z' sem '+00:00', compatível com Next.js."""
        if isinstance(v, dt.datetime):
            if v.tzinfo is None:
                v = v.replace(tzinfo=dt.timezone.utc)
            return v.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        if isinstance(v, str):
            clean = v.strip()
            if clean.endswith("+00:00"):
                return clean[:-6] + "Z"
            if clean.endswith("Z"):
                return clean
            try:
                parsed = dt.datetime.fromisoformat(clean)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=dt.timezone.utc)
                return parsed.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            except Exception:
                return clean
        return generate_iso_timestamp()
    customer_id: str = Field(min_length=3, description="Identificador único do cliente (ex: C038454).")
    action_id: str = Field(min_length=3, description="Identificador da ação ou compensação (ex: ACT-MILHAS-L1).")
    action_name: str = Field(min_length=2, description="Nome legível da ação executada.")
    status: DecisionStatus = Field(
        default="suggested",
        description="Status no fluxo Kanban: 'approved' (L1), 'in_review' (L2), 'suggested', etc.",
    )
    operator: str = Field(
        default="aura_concierge_agent",
        description="Operador que tomou ou propôs a ação (ex: 'aura_concierge_agent', 'operador_humano').",
    )
    original_message: str = Field(default="", description="Mensagem original proposta pelo agente.")
    final_message: str = Field(default="", description="Mensagem final aprovada ou enviada ao cliente.")
    edited: bool = Field(default=False, description="Indica se houve intervenção/edição humana na mensagem.")
    notes: Optional[str] = Field(default=None, description="Notas de auditoria, justificativas ou logs técnicos.")
    hash_signature: Optional[str] = Field(
        default=None,
        description="Assinatura criptográfica SHA-256 calculada sobre os campos imutáveis.",
    )

    @model_validator(mode="after")
    def populate_hash_and_defaults(self) -> "DecisionRecord":
        """Garante que edited e hash_signature estejam preenchidos de forma consistente."""
        if not self.final_message and self.original_message:
            self.final_message = self.original_message
        if not self.original_message and self.final_message:
            self.original_message = self.final_message

        # Atualiza flag de edição caso mensagens difiram
        if self.original_message.strip() != self.final_message.strip():
            self.edited = True

        # Gera assinatura SHA-256 se ausente
        if not self.hash_signature:
            self.hash_signature = self.compute_hash()

        return self

    def compute_hash(self) -> str:
        """Calcula hash SHA-256 idêntico à implementação do Next.js (dashboard/src/lib/data/decisions.ts)."""
        payload = (
            f"{self.timestamp}|{self.customer_id}|{self.action_id}|"
            f"{self.status}|{self.operator}|{self.final_message.strip()}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_jsonl_dict(self) -> dict[str, Any]:
        """Converte para dicionário serializável em JSON Lines."""
        return {
            "timestamp": self.timestamp,
            "customer_id": self.customer_id,
            "action_id": self.action_id,
            "action_name": self.action_name,
            "status": self.status,
            "operator": self.operator,
            "original_message": self.original_message,
            "final_message": self.final_message,
            "edited": self.edited,
            "notes": self.notes,
            "hash_signature": self.hash_signature or self.compute_hash(),
        }


class SafetyCheckResult(BaseModel):
    """Resultado da checagem de segurança e governança de autonomia."""

    approved: bool = Field(description="Indica se a operação pode ser executada ou persistida.")
    level: AutonomyLevel = Field(description="Nível de autonomia avaliado: L1, L2 ou BLOCKED.")
    status: DecisionStatus = Field(description="Status resultante para a ação ('approved', 'in_review', 'rejected').")
    human_review: bool = Field(description="Indica se requer aprovação/revisão humana obrigatória.")
    reason: str = Field(description="Motivo explicativo da decisão de governança.")
    sanitized_message: Optional[str] = Field(default=None, description="Mensagem sanitizada de guardrails se aplicável.")
    violations: list[str] = Field(default_factory=list, description="Lista de violações detectadas (LGPD, limites, etc).")


class ToolCallRequest(BaseModel):
    """Representação estruturada de uma chamada de ferramenta emitida pelo LLM."""

    call_id: str = Field(description="ID gerado pelo gateway LLM (ex: call-xxxx).")
    name: str = Field(description="Nome da ferramenta invocada.")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Argumentos decodificados da chamada.")


class AgentTurnResult(BaseModel):
    """Resultado consolidado do ciclo ReAct do Aura Concierge."""

    customer_id: Optional[str] = Field(default=None, description="ID do cliente trabalhado neste ciclo.")
    turns: int = Field(default=0, description="Quantidade de turnos ReAct iterados.")
    thought_process: list[str] = Field(default_factory=list, description="Raciocínios e ponderações do agente.")
    tool_calls_executed: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Histórico de chamadas de ferramentas e seus retornos.",
    )

    @property
    def turns_executed(self) -> int:
        return self.turns

    @property
    def tools_executed(self) -> list[dict[str, Any]]:
        return self.tool_calls_executed
    decisions_taken: list[DecisionRecord] = Field(
        default_factory=list,
        description="Decisões registradas (milhas, vouchers, kanban, escalonamento).",
    )
    final_message: str = Field(default="", description="Mensagem final produzida para o operador ou cliente.")
    finish_reason: str = Field(default="stop", description="Motivo do término ('stop', 'max_turns', 'error').")
    human_review_required: bool = Field(default=False, description="Sinaliza se qualquer ação tomada requer aprovação L2.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadados adicionais de telemetria e execução.")


# =============================================================================
# Schemas das 8 Ferramentas Corporativas
# =============================================================================

# 1. consultar_cliente_360
class ConsultarCliente360Args(BaseModel):
    customer_id: str = Field(description="Identificador único do cliente, ex: 'C038454'.")


class Cliente360Result(BaseModel):
    found: bool
    customer_id: str
    tier: Optional[str] = None
    persona: Optional[str] = None
    risk_state: Optional[str] = None
    churn_prob: Optional[float] = None
    clv_12m_previsto: Optional[float] = None
    valor_em_risco: Optional[float] = None
    alto_valor: Optional[bool] = None
    score_av: Optional[float] = None
    saldo_pontos: Optional[int] = None
    pontos_expirando_30d: Optional[int] = None
    pontos_qualificaveis_12m: Optional[int] = None
    meta_proximo_nivel_pct: Optional[float] = None
    trechos_12m: Optional[int] = None
    gastos_12m_brl: Optional[float] = None
    rota_favorita: Optional[str] = None
    beneficio_nao_utilizado: Optional[str] = None
    atritos_dominantes: Optional[str] = None
    shap_top3: list[dict[str, Any]] = Field(default_factory=list)
    raw_data: dict[str, Any] = Field(default_factory=dict)


# 2. consultar_historico_atritos_voos
class ConsultarHistoricoAtritosArgs(BaseModel):
    customer_id: str = Field(description="Identificador do cliente.")
    limite_eventos: int = Field(default=10, description="Número máximo de eventos a retornar.")
    apenas_com_atrito: bool = Field(default=False, description="Se True, filtra apenas atritos e voos com impacto negativo.")


class EventoHistorico(BaseModel):
    data: str
    tipo: str
    titulo: str
    detalhe: str
    impacto: str
    flight_id: Optional[str] = None
    flight_number: Optional[str] = None


class HistoricoAtritosResult(BaseModel):
    customer_id: str
    total_eventos_encontrados: int
    eventos: list[EventoHistorico] = Field(default_factory=list)


# 3. consultar_regras_regulamento
class ConsultarRegulamentoArgs(BaseModel):
    termo_ou_pergunta: str = Field(description="Termo, dúvida ou tópico regulatório para consulta.")
    top_k: int = Field(default=3, description="Quantidade de trechos normativos a recuperar.")
    fact_id: Optional[str] = Field(default=None, description="Consulta exata pelo identificador do fato (se conhecido).")


class RegraRegulamentoResult(BaseModel):
    query: str
    total_encontrados: int
    citacoes: list[dict[str, Any]] = Field(default_factory=list)


# 4. conceder_milhas_cortesia
class ConcederMilhasArgs(BaseModel):
    customer_id: str = Field(description="Identificador do cliente beneficiário.")
    quantidade_pontos: int = Field(description="Quantidade de milhas/pontos a conceder (teto máximo absoluto: 5000).")
    motivo: str = Field(description="Justificativa corporativa para a concessão.")
    flight_id: Optional[str] = Field(default=None, description="ID do voo associado ao atrito (para idempotência antifraude).")


class ConcessaoMilhasResult(BaseModel):
    success: bool
    customer_id: str
    pontos_concedidos: int
    autonomy_level: AutonomyLevel
    status: DecisionStatus
    human_review: bool
    motivo: str
    flight_id: Optional[str] = None
    decision: Optional[DecisionRecord] = None
    message: str


# 5. emitir_voucher_servico
class EmitirVoucherArgs(BaseModel):
    customer_id: str = Field(description="Identificador do cliente.")
    tipo_servico: str = Field(description="Tipo de conveniência/serviço: 'lounge', 'bagagem', 'upgrade_cabine', 'wi-fi', 'refeicao_aeroporto'.")
    motivo: str = Field(description="Motivo e contexto da emissão.")
    flight_id: Optional[str] = Field(default=None, description="ID do voo impactado se aplicável.")


class EmissaoVoucherResult(BaseModel):
    success: bool
    customer_id: str
    codigo_voucher: str
    tipo_servico: str
    validade_dias: int = 90
    data_expiracao: str
    status: DecisionStatus
    human_review: bool
    motivo: str
    flight_id: Optional[str] = None
    decision: Optional[DecisionRecord] = None
    message: str


# 6. propor_acao_retencao_kanban
class ProporAcaoKanbanArgs(BaseModel):
    customer_id: str = Field(description="Identificador do cliente.")
    action_id: str = Field(description="Identificador da ação proposta (ex: ACT-UPGRADE-SAFIRA).")
    action_name: str = Field(description="Nome resumido da ação.")
    mensagem_proposta: str = Field(description="Texto da mensagem de abordagem personalizada.")
    justificativa: str = Field(description="Justificativa orientada a risco, churn ou valor.")
    status: DecisionStatus = Field(default="suggested", description="Coluna inicial no Kanban ('suggested' ou 'in_review').")
    canal: str = Field(default="whatsapp", description="Canal de comunicação proposto ('whatsapp', 'email', 'app_push', 'telefone').")


class AcaoKanbanResult(BaseModel):
    success: bool
    card_id: str
    customer_id: str
    action_id: str
    action_name: str
    status: DecisionStatus
    decision: Optional[DecisionRecord] = None
    message: str


# 7. escalar_atendimento_vip
class EscalarAtendimentoVipArgs(BaseModel):
    customer_id: str = Field(description="Identificador do cliente VIP.")
    gravidade: Literal["media", "alta", "critica"] = Field(description="Severidade do atrito ou risco de perda.")
    sumario_atrito: str = Field(description="Síntese do problema e das tentativas anteriores.")
    canal_preferencial: str = Field(default="telefone", description="Canal preferencial de contato para a mesa VIP.")


class EscalacaoVipResult(BaseModel):
    success: bool
    protocolo: str
    customer_id: str
    gravidade: str
    status: DecisionStatus
    human_review: bool = True
    decision: Optional[DecisionRecord] = None
    message: str


# 8. listar_clientes_em_risco_ou_atrito
class ListarClientesRiscoArgs(BaseModel):
    top_n: int = Field(default=10, description="Quantidade máxima de clientes a retornar.")
    min_churn_prob: float = Field(default=0.50, description="Probabilidade mínima de churn estimada.")
    apenas_alto_valor: bool = Field(default=True, description="Se True, filtra apenas clientes categorizados como alto valor.")
    tipo_atrito: Optional[str] = Field(default=None, description="Filtrar por atrito dominante específico se desejado.")


class ClienteRiscoItem(BaseModel):
    customer_id: str
    tier: str
    persona: str
    churn_prob: float
    clv_12m_previsto: float
    valor_em_risco: float
    saldo_pontos: int
    risk_state: str
    atritos_dominantes: Optional[str] = None


class ListarClientesRiscoResult(BaseModel):
    total_encontrados: int
    clientes: list[ClienteRiscoItem] = Field(default_factory=list)


# Aliases canônicos de argumentos para despacho no ToolRegistry
ConsultarAtritosArgs = ConsultarHistoricoAtritosArgs
AcaoKanbanArgs = ProporAcaoKanbanArgs
EscalarVipArgs = EscalarAtendimentoVipArgs

