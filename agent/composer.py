"""Compositor determinístico offline de recomendações e redação do Projeto Aura 2.0.

Gera mensagens personalizadas em PT-BR para cada ação x persona x estado de risco,
com tom respeitoso, sem urgência manipulativa e sem dados sensíveis.
Cita o regulamento sempre que regulation_support != null.
Constrói justificativa explicável estruturada com SHAP top-3 e atritos dominantes.
"""

from __future__ import annotations

import re
from typing import Any

from agent.eligibility import ClientState, EligibilityResult
from agent.rag.retriever import Citation, get_retriever
from aura_core.config import program_rules
from aura_core.log import get_logger

logger = get_logger("agent.composer")

TIER_NAMES = {
    "azul": "Azul Fidelidade",
    "topazio": "Topázio",
    "safira": "Safira",
    "diamante": "Diamante",
    "diamante_unique": "Diamante Unique",
}

TIER_NEXT = {
    "azul": ("topazio", "AF-TIER-TOPAZIO"),
    "topazio": ("safira", "AF-TIER-SAFIRA"),
    "safira": ("diamante", "AF-TIER-DIAMANTE"),
    "diamante": ("diamante_unique", "AF-TIER-DIAMANTE-UNIQUE"),
    "diamante_unique": (None, None),
}

TIER_FACT_MAP = {
    "azul": "AF-TIER-AZUL",
    "topazio": "AF-TIER-TOPAZIO",
    "safira": "AF-TIER-SAFIRA",
    "diamante": "AF-TIER-DIAMANTE",
    "diamante_unique": "AF-TIER-DIAMANTE-UNIQUE",
}

# (ACH-06) Dicionário de tradução de slug de benefícios para linguagem natural
BENEFIT_LABELS: dict[str, str] = {
    "espaco_azul": "cortesia no Espaço Azul",
    "espaco_azul_ilimitado": "Espaço Azul ilimitado",
    "bagagem_gratuita": "bagagem gratuita",
    "duas_bagagens_gratuitas": "duas bagagens gratuitas",
    "tres_bagagens_gratuitas": "três bagagens gratuitas",
    "marcacao_antecipada_assento": "marcação antecipada de assento",
    "antecipacao_gratuita": "antecipação gratuita de voo",
    "antecipacao_voo": "antecipação de voo",
    "desconto_antecipacao": "desconto na antecipação de voo",
    "resgate_especial": "cotas do Resgate Especial Azul",
    "cortesia_acompanhante": "passagem cortesia para acompanhante",
    "passagens_cortesia": "passagens cortesia para acompanhantes",
    "atendimento_whatsapp_24h": "atendimento exclusivo via WhatsApp 24 horas",
    "lounge_azul": "acesso ao Lounge Azul em Viracopos",
    "wifi_nacional": "Wi-Fi em voos nacionais",
    "economy_xtra": "assento Economy Xtra",
}

# (ACH-02) Conjunto de benefícios conhecidos por tier derivado de program_rules.yaml
TIER_BENEFITS_MAP: dict[str, set[str]] = {
    "azul": {
        "wifi_nacional",
        "desconto_antecipacao",
        "marcacao_antecipada_assento",
    },
    "topazio": {
        "espaco_azul",
        "bagagem_gratuita",
        "desconto_antecipacao",
        "wifi_nacional",
        "antecipacao_voo",
    },
    "safira": {
        # Nota (NEW-12, revisita WS7): lounge_azul e economy_xtra NÃO pertencem à
        # Safira — conforme o snapshot do regulamento (config/program_rules.yaml,
        # AF-TIER-SAFIRA), esses benefícios são EXCLUSIVOS do Diamante Unique
        # (AF-TIER-DIAMANTE-UNIQUE). A ausência aqui é intencional: se um slug
        # fora do tier chegar (ex.: beneficio_nao_utilizado vindo de dados),
        # validate_known_benefit descarta e o template usa o fallback genérico
        # honesto ("benefícios garantidos da sua categoria") — nunca promete
        # benefício não regulamentado para o nível.
        "bagagem_gratuita",
        "duas_bagagens_gratuitas",
        "marcacao_antecipada_assento",
        "antecipacao_gratuita",
        "antecipacao_voo",
        "resgate_especial",
        "espaco_azul",
        "wifi_nacional",
    },
    "diamante": {
        "bagagem_gratuita",
        "tres_bagagens_gratuitas",
        "espaco_azul",
        "espaco_azul_ilimitado",
        "cortesia_acompanhante",
        "passagens_cortesia",
        "resgate_especial",
        "marcacao_antecipada_assento",
        "antecipacao_gratuita",
        "wifi_nacional",
    },
    "diamante_unique": {
        "passagens_cortesia",
        "cortesia_acompanhante",
        "atendimento_whatsapp_24h",
        "bagagem_gratuita",
        "tres_bagagens_gratuitas",
        "espaco_azul",
        "economy_xtra",
        "lounge_azul",
        "wifi_nacional",
    },
}

# (ACH-03) Lista de promessas substantivas proibidas nos templates
FORBIDDEN_PROMISES: list[str] = [
    "acompanhamento dedicado",
    "acompanhamentos dedicados",
    "atendimento prioritário",
    "atendimentos prioritários",
    "alternativas ágeis",
    "alternativa ágil",
    "time de relacionamento exclusivo",
    "times de relacionamento exclusivo",
    "benefícios exclusivos",
    "benefício exclusivo",
    "beneficios exclusivos",
    "beneficio exclusivo",
]


def validate_route_format(route: str | None) -> str | None:
    """Valida formato estrito de rota IATA ^[A-Z]{3}-[A-Z]{3}$ (ACH-02)."""
    if not route:
        return None
    val = str(route).strip().upper()
    if re.match(r"^[A-Z]{3}-[A-Z]{3}$", val):
        return val
    logger.warning("Formato de rota inválido descartado: %r", route)
    return None


def validate_known_benefit(benefit_str: str | None, tier: str | None = None) -> str | None:
    """Valida se o benefício é conhecido para o programa ou nível (ACH-02)."""
    if not benefit_str:
        return None
    slug = str(benefit_str).strip().lower().replace("-", "_").replace(" ", "_")
    if tier and tier in TIER_BENEFITS_MAP:
        allowed = TIER_BENEFITS_MAP[tier]
        if slug in allowed:
            return slug
    elif slug in BENEFIT_LABELS:
        return slug
    logger.warning("Benefício não reconhecido descartado para tier=%s: %r", tier, benefit_str)
    return None


def format_benefit_natural(slug: str) -> str:
    """Traduz slug para linguagem natural em PT-BR (ACH-06)."""
    return BENEFIT_LABELS.get(slug, slug.replace("_", " "))


def _resolve_target_fact_id(
    action_name: str, reg_support: str | None, client: ClientState
) -> str | None:
    """Determina o fact_id formal correto para citação a partir do contexto."""
    if not reg_support:
        return None

    if action_name == "antecipacao_de_nivel":
        _, next_fact_id = TIER_NEXT.get(client.tier, (None, None))
        return next_fact_id

    if action_name == "educacao_beneficio_existente":
        return TIER_FACT_MAP.get(client.tier)

    # Suporte explícito (ex.: AF-QUALIFYING-POINTS, AF-RESGATE-ESPECIAL-2025)
    return reg_support


def _build_ptbr_message(
    action_name: str,
    client: ClientState,
    citation: Citation | None,
) -> str:
    """Compõe mensagem em português com tom acolhedor, transparente e sem promessas desamparadas."""
    tier_label = TIER_NAMES.get(client.tier, client.tier.capitalize())
    citation_tag = ""
    if citation:
        citation_tag = (
            f" [Regulamento: {citation.fact_id} | status: {citation.verification_status} | "
            f"vigência: {citation.valid_from} | ref: {citation.source_label}]"
        )

    msg = ""
    if action_name == "contato_proativo_relacionamento":
        # ACH-03: reformulado para contato de relacionamento sincero, sem 'time exclusivo'
        msg = (
            f"Olá! Valorizamos imensamente seu relacionamento com o Azul Fidelidade na categoria {tier_label}. "
            "Identificamos que suas experiências recentes merecem atenção do nosso time e gostaríamos de "
            "ouvir você diretamente. Um profissional de relacionamento entrará em contato para entender seus "
            "pontos de vista e buscar a melhor solução para suas próximas viagens."
        )

    elif action_name == "gesto_reconhecimento_bonus_pontos":
        msg = (
            f"Olá! Em reconhecimento ao seu relacionamento e fidelidade na categoria {tier_label}, "
            "disponibilizamos um crédito de 2.000 Pontos Azul para você planejar seus próximos momentos de viagem. "
            f"Aproveite para transformar sua dedicação em novas experiências.{citation_tag}"
        )

    elif action_name == "antecipacao_de_nivel":
        # ACH-03: removido 'acompanhamento dedicado'; afirma apenas progresso factual e meta
        next_key, _ = TIER_NEXT.get(client.tier, (None, None))
        next_label = TIER_NAMES.get(next_key, "próximo nível")
        pct_str = (
            f"{client.meta_proximo_nivel_pct:.0%}" if client.meta_proximo_nivel_pct > 0 else "80%+"
        )
        msg = (
            f"Parabéns pelo seu progresso! Você já conquistou {pct_str} da meta de qualificação necessária para "
            f"alcançar a categoria {next_label} no Azul Fidelidade. Continue voando e acumulando pontos para concluir "
            f"sua transição de nível.{citation_tag}"
        )

    elif action_name == "oferta_resgate_especial":
        cotas_info = "70.000 pontos/trecho" if client.tier == "safira" else "50.000 pontos/trecho"
        msg = (
            f"Como cliente {tier_label}, você tem à disposição as cotas do Resgate Especial Azul: "
            f"passagens nacionais com valor fixo ({cotas_info}), conforme os termos e condições do regulamento.{citation_tag}"
        )

    elif action_name == "oferta_rota_favorita":
        # ACH-02: valida formato da rota; descarta se inválida
        valid_rota = validate_route_format(client.rota_favorita)
        rota_str = f"({valid_rota})" if valid_rota else "em sua rota mais frequente"
        msg = (
            f"Preparamos uma oportunidade para seu trecho favorito {rota_str}: "
            "bônus de Pontos Azul na sua próxima reserva para valorizar cada momento voado conosco."
            f"{citation_tag}"
        )

    elif action_name == "pacote_experiencia_destino":
        # ACH-03: convite para conhecer pacotes Azul Viagens sem prometer 'benefícios exclusivos'
        msg = (
            f"Pensando no seu momento de lazer, a Azul Viagens preparou opções de pacotes e experiências para "
            f"clientes da categoria {tier_label}. Planeje seu descanso com a comodidade e o cuidado dos serviços Azul."
        )

    elif action_name == "missao_acumulo_parceiro":
        msg = (
            "Acelere seu saldo com as missões de parceiros e cartão Azul Itaú: "
            "cada ponto acumulado em compras do dia a dia aproxima você de novas viagens no programa."
            f"{citation_tag}"
        )

    elif action_name == "aviso_antecipado_prioridade":
        # ACH-07: corrigido 'sua conta conta com' para redação limpa
        msg = (
            "Para apoiar o planejamento dos seus deslocamentos, seu perfil conta com comunicações antecipadas "
            "sobre frequências de voos e novidades na sua rota de preferência."
        )

    elif action_name == "reencaminhamento_atraso":
        # ACH-03: reconhecimento do atrito + suporte pelos canais existentes sem prometer 'prioritário/ágeis'
        msg = (
            "Sabemos que pontualidade é essencial para você e lamentamos eventuais atritos com atrasos em sua "
            "programação recente. Convidamos você a contatar nossos canais de atendimento para suporte e "
            "verificação de alternativas de voo disponíveis para sua rota."
        )

    elif action_name == "educacao_beneficio_existente":
        # ACH-02 / ACH-03 / ACH-06: validação em enum, tradução de slug e citação do chunk de benefícios
        ben_slug = validate_known_benefit(client.beneficio_nao_utilizado, client.tier)
        ben_label = (
            format_benefit_natural(ben_slug)
            if ben_slug
            else "benefícios garantidos da sua categoria"
        )
        msg = (
            f"Lembramos que sua categoria {tier_label} no Azul Fidelidade já inclui benefícios garantidos pelo programa, "
            f"como {ben_label}. Aproveite para usufruir dessas vantagens já disponíveis para você."
            f"{citation_tag}"
        )

    else:
        # Fallback genérico transparente
        msg = (
            f"Agradecemos sua história na categoria {tier_label} do Azul Fidelidade. "
            f"Seguimos à disposição em nossos canais oficiais para tornar sua experiência cada vez melhor.{citation_tag}"
        )

    # Verificação de segurança: nenhuma promessa proibida pode constar na mensagem gerada (ACH-03)
    msg_lower = msg.lower()
    for forbidden in FORBIDDEN_PROMISES:
        if forbidden in msg_lower:
            raise ValueError(
                f"Mensagem gerada contém promessa proibida sem lastro fático: {forbidden!r}"
            )

    return msg


def compose_recommendation(
    eligibility_result: EligibilityResult,
    client: ClientState,
) -> dict[str, Any]:
    """Compõe a recomendação determinística completa com justificativa explicável e citações."""
    retriever = get_retriever()
    action_name = eligibility_result.action_name
    action_id = eligibility_result.action_id

    # 1. Resolução e validação de citação regulatória
    target_fact_id = _resolve_target_fact_id(
        action_name, eligibility_result.regulation_support, client
    )
    citations: list[Citation] = []
    if target_fact_id:
        if action_name == "educacao_beneficio_existente":
            # ACH-03: cita explicitamente o chunk de benefícios do tier ({tier_id}:beneficios)
            preferred_chunk = f"{target_fact_id}:beneficios"
            citation = retriever.get_citation_for_fact(
                target_fact_id, preferred_chunk_id=preferred_chunk
            )
        else:
            citation = retriever.get_citation_for_fact(target_fact_id)
        citations.append(citation)
    else:
        citation = None

    # 2. Redação da mensagem
    message = _build_ptbr_message(action_name, client, citation)

    # 3. Justificativa estruturada ("por que este cliente / por que esta ação")
    shap_list: list[str] = []
    if client.shap_top3:
        if isinstance(client.shap_top3, list):
            shap_list = [str(x) for x in client.shap_top3]
        elif isinstance(client.shap_top3, str):
            import json

            try:
                parsed = json.loads(client.shap_top3)
                if isinstance(parsed, list):
                    shap_list = [str(x) for x in parsed]
                else:
                    shap_list = [client.shap_top3]
            except Exception:
                shap_list = [client.shap_top3]

    atritos_list = sorted(list(client.get_atritos_set()))

    rules_triggered = list(eligibility_result.rules_triggered)

    justification = {
        "shap_top3": shap_list,
        "atritos": atritos_list,
        "regras_acionadas": rules_triggered,
        "motivo_resumo": (
            f"Ação {action_name} selecionada para persona={client.persona}, risco={client.risk_state}, "
            f"tier={client.tier} (alto_valor={client.alto_valor})"
        ),
    }

    # 4. Canal preferencial
    channel = eligibility_result.channels[0] if eligibility_result.channels else "app"

    # 5. Confiança e human_review
    confidence = 0.95
    human_review = eligibility_result.requires_human_review

    snapshot_version = (
        program_rules().get("meta", {}).get("snapshot_version", "research-2026-10-12")
    )

    return {
        "customer_id": client.customer_id,
        "action_id": action_id,
        "action_name": action_name,
        "channel": channel,
        "message": message,
        "justification": justification,
        "citations": [c.to_dict() for c in citations],
        "confidence": confidence,
        "human_review": human_review,
        "mode": "offline",
        "snapshot_version": snapshot_version,
    }
