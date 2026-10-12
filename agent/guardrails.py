"""Guardrails do Projeto Aura 2.0.

Implementa verificações inegociáveis de segurança e conformidade:
(a) toda citação regulatória EXISTE na base de conhecimento com status aceitável;
(b) zero promessa fora do inventário de ações elegíveis;
(c) zero dado sensível na mensagem (LGPD: faixa etária, gênero, região);
(d) tom respeitoso (sem urgência manipulativa / escassez artificial);
(e) saída estritamente validada por Pydantic;
(f) sanitização robusta contra prompt-injection.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field, field_validator

from agent.rag.retriever import get_retriever
from aura_core.config import load_yaml
from aura_core.log import get_logger

logger = get_logger("agent.guardrails")

NO_ACTION_NAME = "nenhuma_acao_elegivel"
NO_ACTION_ID = "ACT-NO-ACTION"


class GuardrailViolationError(ValueError):
    """Exceção levantada quando uma ou mais regras de guardrail são violadas."""

    def __init__(self, violations: list[str]) -> None:
        self.violations = violations
        super().__init__(
            "Violações de Guardrail detectadas:\n" + "\n".join(f"  - {v}" for v in violations)
        )


class JustificationPayload(BaseModel):
    shap_top3: list[str] = Field(default_factory=list)
    atritos: list[str] = Field(default_factory=list)
    regras_acionadas: list[str] = Field(default_factory=list)
    motivo_resumo: str = Field(min_length=1)


class CitationPayload(BaseModel):
    fact_id: str
    text: str
    verification_status: str
    valid_from: str
    snapshot_version: str
    source_label: str
    score: float = Field(default=1.0, ge=0.0, le=1.0)

    @field_validator("fact_id", "verification_status", "snapshot_version")
    @classmethod
    def check_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Campo obrigatório de citação não pode ser vazio")
        return v.strip()


class RecommendationPayload(BaseModel):
    customer_id: str
    action_id: str
    action_name: str
    channel: str
    message: str
    justification: JustificationPayload
    citations: list[CitationPayload] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    human_review: bool
    mode: str = "offline"
    snapshot_version: str

    @field_validator("mode")
    @classmethod
    def check_mode(cls, v: str) -> str:
        if v not in {"offline", "llm"}:
            raise ValueError(f"Modo inválido: {v}. Esperado 'offline' ou 'llm'.")
        return v


# -----------------------------------------------------------------------------
# Expressões Regulares de Detecção de Violações
# -----------------------------------------------------------------------------

# (c) LGPD: Atributos sensíveis na mensagem (ACH-09 + NEW-06/07/08/09)
SENSITIVE_PATTERNS = [
    # Idade / faixas etárias numéricas e textuais
    r"\b(faixa\s+et[áa]ria|idade\s+avan[çc]ada|idos[oa]s?|jovens?|menor\s+de\s+idade|terceira\s+idade)\b",
    r"\b\d{1,2}\s+anos(\s+de\s+idade)?\b",
    r"\b(data\s+de\s+nascimento|nascid[oa]s?\s+em\s+['´\"“]?\d{2,4}|nasceu\s+(em|no\s+ano)\s+['´\"“]?\d{2,4}|ano\s+de\s+nascimento\s+['´\"“]?\d{2,4})\b",
    # Gênero / sexo direto e indireto (inclui "maior de idade")
    r"\b(g[êe]nero|sexo\s+(masculino|feminino|bio|m|f)|homem|homens|mulher|mulheres|menino|menina|do\s+sexo|maior\s+de\s+idade)\b",
    # Regiões geográficas com e sem a palavra 'região' + "natural de"
    r"\b(regi[ãa]o\s+)?(norte|nordeste|sul|sudeste|centro-oeste)\b",
    r"\b(reside(?:nte)?|morador[a]?|natural\s+de)\s+(d[oe]s?|no|na|em)\s+[a-záàâãéêíóôõúç\s]+\b",
    # Estados brasileiros com e sem prefixo (Pará exige acento ou prefixo para evitar conflito com a preposição 'para')
    r"\b(estado\s+d[eo]\s+)?(acre|alagoas|amap[áa]|amazonas|bahia|cear[áa]|distrito\s+federal|esp[íi]rito\s+santo|goi[áa]s|maranh[ãa]o|mato\s+grosso(\s+do\s+sul)?|minas\s+gerais|para[íi]ba|paran[áa]|pernambuco|piau[íi]|rio\s+de\s+janeiro|rio\s+grande\s+do\s+(norte|sul)|rond[ôo]nia|roraima|santa\s+catarina|s[ãa]o\s+paulo|sergipe|tocantins)\b|\b(estado\s+do\s+par[áa]|pará)\b",
    # Documentos pessoais (inclui CPF/CNPJ numérico sem label)
    r"\b(cpf[:\s]+[0-9.-]+|rg[:\s]+[0-9.-]+)\b",
    r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b",  # CPF: 123.456.789-00
    r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b",  # CNPJ: 12.345.678/0001-00
]

# (d) Tom: Urgência manipulativa / escassez artificial (ACH-02 + NEW-04)
URGENCY_PATTERNS = [
    r"\b([úu]ltima\s+chance|corra\s+j[áa]|antes\s+que\s+acabe)\b",
    # R3 (revisita 2, B2): pretérito/subjuntivo + "última hora" + "apenas hoje" + "expira agora"
    r"\b(o\s+)?tempo\s+(acabou|esgotou|terminou)\b",
    r"\bacabou\s+o\s+tempo\b",
    r"\b[úu]ltima?s?\s+horas?\b",
    r"\bapenas\s+(hoje|hoje\s+mesmo)\b",
    r"\b(se\s+)?acabe\s+(hoje|agora|j[áa])\b",
    r"\b(expira|termina|acaba)\s+(agora|hoje)\b",
    r"\b(s[óo]\s+hoje|restam\s+apenas|n[ãa]o\s+perca(\s+por\s+nada|\s+essa\s+oportunidade|\s+tempo)?)\b",
    r"\b(urgente!?|imperd[íi]vel(\s+s[óo]\s+agora)?|compre\s+imediatamente)\b",
    r"\b(vagas\s+limitadas|apenas\s+\d+\s+horas?|v[áa]lid[ao]\s+apenas\s+por(\s+\d+)?\s+horas?|24\s+horas)\b",
    # Novos vetores de escassez/tempo (NEW-04) - bidirecional para cobrir ambas ordens
    r"\b(expira|termina|acaba)\s+em\s+(\d+\s+)?(minutos?|horas?|hoje|j[áa])\b",
    r"\b(pouqu[íi]ssim[ae]s?|limitad[íi]ssim[ae]s?)[\s,;.]+(vagas?|unidades?|chances?|oportunidades?)\b",
    r"\b(vagas?|unidades?|chances?|oportunidades?)[\s,;.]+(pouqu[íi]ssim[ae]s?|limitad[íi]ssim[ae]s?)\b",
    r"\b(oportunidade\s+[úu]nica)\b",
    r"\b(tempo\s+(?:esta\s+|est[aá]\s+)?(acabando|esgotando|correndo))\b",
    r"\b([úu]ltim[ae]s?)\s+(unidades?|vagas?|chances?)\b",
    r"\b(v[áa]lid[ao]\s+s[óo]\s+at[ée]\s+amanh[ãa])\b",
    r"\b(contagem\s+regressiva)\b",
    r"\b(\d+\s+minutos?\s+restantes?)\b",
    # R4 (revisita 3, V4-04): "acaba imediatamente"
    r"\b(expira|termina|acaba)\s+imediatamente\b",
]

# Promessas abusivas ou benefícios inexistentes generalizados (ACH-02 + NEW-03 + R3)
# Semântica R3 (revisita 2): separa dois vocabulários.
#   - GRATUIDADE_FREE ("grátis", "sem custo", "cortesia"): legítima para benefícios REAIS
#     (bagagens gratuitas, antecipação gratuita, marcação gratuita) — só é fabricação
#     quando pareada com benefícios NUNCA gratuitos (upgrade, status, lounge, milhas...).
#     Isso elimina falsos positivos como "Sua categoria Safira garante duas bagagens
#     gratuitas em rotas elegíveis" (benefício real do regulamento).
#   - DURABILIDADE_STRONG (vitalício, ilimitado, infinito, eterno, nunca expiram,
#     para sempre, máxima, todas as filas, por vida): NUNCA é legítimo em mensagem
#     de retenção — pareia com TODOS os benefícios.
_GRATUIDADE_FREE = r"gratu[íi]t[oa]s?|gr[áa]tis|de\s+gra[çc]a|de\s+cortesia|sem\s+custo"
_DURABILIDADE_STRONG = (
    r"vital[íi]ci[oa]s?|perp[ée]tu[oa]s?|perpetu[oa]s?|ilimitad[oa]s?|sem\s+limite|infinit[oa]s?|inesgot[áa]veis?|"
    r"etern[oa]s?|nunca\s+expira|expira[m]?\s+nunca|para\s+sempre|m[áa]xima|todas?\s+filas?|por\s+vida"
)
# Benefícios JAMAIS gratuitos: gratuidade próxima (free OU strong) = fabricação.
_NUNCA_FREE = (
    r"upgrade|status|milhas?|miles?|lounge|prioridade|preferenc(ia|ial)|cashback|dobro|duplo|validez|validade"
)
# Todos os benefícios: só disparam com vocabulário de durabilidade (strong).
_TODO_BENEFICIO = (
    r"upgrade|passagens?|voos?|lounge|status|milhas?|miles?|pontos?|categoria|bagagens?|bagagem|malas?|"
    r"n[íi]vel|isen[çc][ãa]o|isencao|taxas?|tarifas?|acompanhantes?|prioridade|cashback|dobro|duplo|"
    r"validez|validade|antecipacao"
)
FABRICATED_BENEFIT_PATTERNS = [
    # A) Nunca-gratuitos × (gratuidade OU durabilidade), bidirecional
    rf"\b({_NUNCA_FREE})\b.{{0,50}}\b({_GRATUIDADE_FREE}|{_DURABILIDADE_STRONG})\b",
    rf"\b({_GRATUIDADE_FREE}|{_DURABILIDADE_STRONG})\b.{{0,50}}\b({_NUNCA_FREE})\b",
    # B) Todos os benefícios × durabilidade-only, bidirecional
    rf"\b({_TODO_BENEFICIO})\b.{{0,50}}\b({_DURABILIDADE_STRONG})\b",
    rf"\b({_DURABILIDADE_STRONG})\b.{{0,50}}\b({_TODO_BENEFICIO})\b",
    # Padrões específicos de paráfrases comuns
    r"\b(passagens?\s+de\s+gra[çc]a\s+para\s+(toda\s+a\s+fam[íi]lia|sempre))\b",
    r"\b(passagens?\s+gr[áa]tis|voos?\s+gr[áa]tis)\b",
    r"\b(pontos\s+infinitos|milhas?\s+infinitas?|isen[çc][ãa]o\s+vital[íi]cia|status\s+vital[íi]cio|cashback\s+em\s+dobro)\b",
    r"\b(acesso\s+vital[íi]cio\s+ao\s+lounge)\b",
    r"\b(bagagem\s+sem\s+limite|bagagem\s+ilimitada|malas?\s+sem\s+limite|malas?\s+ilimitadas?)\b",
    r"\b(prioridade\s+m[áa]xima|prioridade\s+em\s+todas?\s+filas?)\b",
    r"\b(pontos?\s+nunca\s+expiram|validez\s+eterna|expira(c[aã]o|ção)\s+nunca)\b",
    r"\b(status\s+para\s+sempre|categoria\s+para\s+sempre|n[íi]vel\s+garantido\s+para\s+sempre)\b",
    r"\b(isen[çc][ãa]o\s+de\s+(todas?\s+)?taxas?\s+para\s+sempre|isencao\s+de\s+(todas?\s+)?taxas?\s+sempre|isent[oa]\s+(taxas?|tarifas?)\s+(para\s+sempre|sempre|vital[íi]cia))\b",
    # R3 (revisita 2, B2): "isento de tarifas por vida" + "pontos que não expiram nunca"
    r"\b(isent[oa]s?|isentos?)\s+(de\s+)?(todas?\s+)?(taxas?|tarifas?)\s+(por\s+vida|para\s+sempre|sempre|vital[íi]ci[oa]s?)\b",
    r"\b(pontos?|milhas?|miles?)\s+.{0,20}expira[m]?\s+nunca\b",
]

# (f) Prompt Injection Sanitization e Variantes PT+EN (ACH-02 + NEW-01/02/05)
PROMPT_INJECTION_VARIANTS = [
    # PT: ignore/ignorar/desconsidere/esqueca + regras/instruções/diretrizes/etc.
    r"\b(ignore|ignorar|desconsidere|desconsiderar|esqueca|esquecer)\s+(todas?\s+as?\s+|os?\s+|as?\s+)?(regras?|instrucoes|diretrizes|politicas?|prompts?|mensagens?)\s*(anteriores|acima|precedentes|do\s+sistema)?\b",
    r"\b(ignore|ignorar|desconsidere|desconsiderar)\s+(o\s+)?prompt(\s+acima|\s+anterior)?\b",
    r"\b(nao\s+siga|nao\s+considere|deixe\s+de\s+seguir)\s+(as?\s+)?(regras?|instrucoes|diretrizes)\b",
    # PT: "esqueça tudo antes/acima" variants (NEW-01)
    r"\b(esqueca|efqueca)\s+tudo\s+(antes|acima)\b",
    # PT: "não siga as diretrizes" / "desconsidere as diretrizes" variants (NEW-01)
    r"\b(nao\s+siga|desconsidere)\s+as\s+diretrizes\b",
    # PT: "não siga as diretrizes anteriores" / "desconsidere as diretrizes anteriores" (NEW-01)
    r"\b(nao\s+siga|desconsidere)\s+as\s+diretrizes\s+(anteriores|acima)\b",
    # PT: "a partir de agora você é outro" / "você é outro assistente" (NEW-01)
    r"\b(a\s+partir\s+de\s+agora|voce\s+e\s+outro)\b",
    # R3 (revisita 2, B2): desobediência / desrespeito a regras / troca de persona
    r"\b(nao\s+)?obedec[ae]s?\s+(a|as|aos?)\s+(regras?|diretrizes|instrucoes|politicas?)\b",
    r"\bdesrespeit[ae]s?\s+(as?\s+)?(regras?|diretrizes|instrucoes|politicas?)\b",
    r"\b(atue|aja|comporte-?se)\s+como\s+(um[oa]?\s+)?(outro|diferente)\s+(assistente|agente|modelo|sistema)\b",
    # R4 (revisita 3, V4-01/02): locuções perifrásticas de desobediência e troca de persona
    r"\b(deixe|deixar)\s+de\s+seguir\s+(as?\s+)?(regras?|diretrizes|instrucoes)\b",
    r"\b(seja|torn[e]-se)\s+(um[oa]?\s+)?(assistente|agente|modelo|sistema)\s+sem\s+(filtros?|limites?|restricoes)\b",
    # EN: ignore / disregard / forget / override
    r"\b(ignore|disregard|forget|override)\s+(all\s+)?(previous|prior|system|above)?\s*(instructions|rules|guidelines|policies|prompts?)\b",
    # Role prefixes: system:/assistant:/human:/user: (NEW-02) - sem \b final para permitir :
    r"(system\s*:|assistant\s*:|human\s*:|user\s*:|usu[aá]rio\s*:)",
    r"<script.*?>.*?</script>",
    r"\b(jailbreak|dan\s+mode|override\s+policy)\b",
    r"\b(drop\s+table|select\s+\*\s+from|delete\s+from|insert\s+into)\b",
]

SUSPICIOUS_RESIDUAL_PATTERNS = [
    r"<script",
    r"javascript:",
    r"\b(jailbreak|override\s+policy|drop\s+table|select\s+\*)\b",
    r"\b(system\s*:|assistant\s*:)\b",
]


def _strip_accents_lower(s: str) -> str:
    """Normaliza para minúsculas sem acentos."""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def sanitize_input_text(text: str | None) -> str:
    """Sanitiza campos de entrada de texto contra tentativas de prompt injection (ACH-02).

    A normalização NFKD é aplicada ANTES da detecção E da remoção para garantir
    que variantes unicode/acentos não burlam os padrões (NEW-16/NEW-17).
    O texto retornado é a versão normalizada (sem acentos), pois a segurança
    prevalece sobre a preservação de diacríticos em campos de entrada livre.
    """
    if not text:
        return ""
    raw = str(text).strip()

    # 1. Normalização semântica (minúsculas sem acentos) para detecção E remoção
    norm = _strip_accents_lower(raw)

    # 2. Identifica se há padrões maliciosos na versão normalizada
    has_injection = False
    for pat in PROMPT_INJECTION_VARIANTS:
        if re.search(pat, norm, flags=re.IGNORECASE):
            has_injection = True
            logger.warning("Tentativa de prompt injection detectada via padrão: %s", pat)
            break

    # 3. Remoção cirúrgica de padrões de injeção no texto NORMALIZADO
    clean = norm
    if has_injection:
        for pat in PROMPT_INJECTION_VARIANTS:
            clean = re.sub(pat, "[CONTEÚDO REMOVIDO]", clean, flags=re.IGNORECASE)

    # 4. Remove caracteres de controle estranhos exceto quebras de linha padrão
    clean = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", clean).strip()

    # 5. Fail-loud: se após a sanitização ainda restar conteúdo suspeito remanescente
    for sus_pat in SUSPICIOUS_RESIDUAL_PATTERNS:
        if re.search(sus_pat, clean, flags=re.IGNORECASE):
            logger.error("Conteúdo malicioso persistente após sanitização: %s", clean)
            raise ValueError(f"Entrada contém payload malicioso rejeitado: {clean!r}")

    return clean


@dataclass
class GuardrailCheckResult:
    passed: bool
    violations: list[str]
    sanitized_output: RecommendationPayload | None = None


def check_guardrails(
    payload_dict: dict[str, Any],
    eligible_action_names: list[str] | set[str] | None = None,
) -> GuardrailCheckResult:
    """Aplica todas as regras de guardrail sobre o dicionário de recomendação."""
    violations: list[str] = []

    # 1. Validação de Schema Pydantic
    try:
        rec = RecommendationPayload(**payload_dict)
    except Exception as exc:
        violations.append(f"Validação de schema falhou: {exc}")
        return GuardrailCheckResult(passed=False, violations=violations)

    actions_cfg = load_yaml("config/actions.yaml")
    actions_map = actions_cfg.get("actions", {})

    # 2 e 3. Verificação de Ação no Inventário e Elegibilidade (ACH-01)
    eligible_set = set(eligible_action_names) if eligible_action_names is not None else None

    if rec.action_name == NO_ACTION_NAME:
        if rec.action_id != NO_ACTION_ID:
            violations.append(
                f"Ação {NO_ACTION_NAME!r} requer action_id={NO_ACTION_ID!r}, recebido {rec.action_id!r}"
            )
        # Se o cliente tinha ações elegíveis, NÃO deveria ter recebido NO_ACTION
        if eligible_set is not None and len(eligible_set) > 0:
            violations.append(
                f"Resultado {NO_ACTION_NAME!r} emitido indevidamente: cliente possui ações elegíveis: {sorted(eligible_set)}"
            )
    else:
        # Ação padrão do playbook
        if rec.action_name not in actions_map:
            violations.append(
                f"Ação {rec.action_name!r} não existe no inventário oficial de actions.yaml"
            )

        if eligible_set is not None:
            if len(eligible_set) == 0:
                violations.append(
                    f"Ação {rec.action_name!r} recomendada para cliente sem nenhuma ação elegível (esperado {NO_ACTION_NAME!r})"
                )
            elif rec.action_name not in eligible_set:
                violations.append(
                    f"Ação {rec.action_name!r} não consta no conjunto de ações elegíveis para este cliente ({sorted(eligible_set)})"
                )

    # 4. Checagem de Promessas de Benefícios Fabricados / Inexistentes (ACH-02 + NEW-03)
    msg_lower = rec.message.lower()
    for pat in FABRICATED_BENEFIT_PATTERNS:
        if re.search(pat, msg_lower):
            violations.append(
                f"Mensagem promete benefício inexistente/não regulamentado: padrão {pat!r}"
            )

    # 5. LGPD: Ausência estrita de dados sensíveis na mensagem (ACH-09 + NEW-06/07/08/09)
    # Aplicar normalização NFKD antes do match para pegar variantes unicode (NEW-16)
    msg_norm = _strip_accents_lower(rec.message)
    for pat in SENSITIVE_PATTERNS:
        if re.search(pat, msg_norm):
            violations.append(
                f"Violação de LGPD: mensagem contém dado sensível ou demográfico (padrão {pat!r})"
            )

    # 6. Tom: Ausência de urgência manipulativa / pressão indevida (ACH-02 + NEW-04)
    # Aplicar normalização NFKD antes do match para pegar variantes unicode (NEW-16)
    for pat in URGENCY_PATTERNS:
        if re.search(pat, msg_norm):
            violations.append(
                f"Violação de tom: mensagem utiliza urgência manipulativa (padrão {pat!r})"
            )

    # 7. Groundedness RAG: Toda citação existe no KB com status aceitável E confere com o KB (ACH-08 + NEW-18)
    retriever = get_retriever()
    acceptable_statuses = {
        "official_historical",
        "official_current",
        "official_current_partial",
        "operational_playbook",
    }
    # Source labels canônicos do KB (para validação NEW-18)
    canonical_source_labels = set(retriever.get_canonical_source_labels())

    for cit in rec.citations:
        try:
            kb_cit = retriever.get_citation_for_fact(cit.fact_id)
            if kb_cit.verification_status not in acceptable_statuses:
                violations.append(
                    f"Citação {cit.fact_id} possui status não aceitável no KB: {kb_cit.verification_status}"
                )
            # Verificação contra atributos do payload (ACH-08)
            if cit.verification_status != kb_cit.verification_status:
                violations.append(
                    f"Divergência de citação {cit.fact_id}: verification_status no payload ({cit.verification_status!r}) "
                    f"diverge do KB canônico ({kb_cit.verification_status!r})"
                )
            if cit.valid_from != kb_cit.valid_from:
                violations.append(
                    f"Divergência de citação {cit.fact_id}: valid_from no payload ({cit.valid_from!r}) "
                    f"diverge do KB canônico ({kb_cit.valid_from!r})"
                )
            if cit.snapshot_version != kb_cit.snapshot_version:
                violations.append(
                    f"Divergência de citação {cit.fact_id}: snapshot_version no payload ({cit.snapshot_version!r}) "
                    f"diverge do KB canônico ({kb_cit.snapshot_version!r})"
                )
            # NEW-18: Valida source_label contra KB canônico
            if cit.source_label not in canonical_source_labels:
                violations.append(
                    f"Citação {cit.fact_id}: source_label não canônico no KB ({cit.source_label!r}). "
                    f"Valores permitidos: {sorted(canonical_source_labels)}"
                )
        except Exception as exc:
            violations.append(
                f"Citação regulatória inválida ou inexistente no KB: {cit.fact_id} ({exc})"
            )

    passed = len(violations) == 0
    return GuardrailCheckResult(
        passed=passed,
        violations=violations,
        sanitized_output=rec if passed else None,
    )


def validate_or_raise_guardrails(
    payload_dict: dict[str, Any],
    eligible_action_names: list[str] | set[str] | None = None,
) -> RecommendationPayload:
    """Valida e lança GuardrailViolationError se qualquer regra for descumprida."""
    res = check_guardrails(payload_dict, eligible_action_names)
    if not res.passed:
        raise GuardrailViolationError(res.violations)
    assert res.sanitized_output is not None
    return res.sanitized_output
