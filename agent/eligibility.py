"""Motor determinístico puro de elegibilidade do Projeto Aura 2.0.

Avalia o estado do cliente (tier, saldo, métricas de qualificação, atritos, persona,
risco e valor) contra o playbook de ações (config/actions.yaml) e as regras versionadas
do programa (config/program_rules.yaml).

REGRAS INEGOCIÁVEIS:
- Determinismo total; zero aleatoriedade.
- Sem inventar benefícios fora de actions.yaml.
- Regras com valor null em program_rules.yaml (ex.: Diamante Unique earn/validity/ceiling/beneficiaries)
  são estritamente tratadas como INELEGÍVEL (fail-safe) e sinalizadas com human_review=True.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from pydantic import BaseModel

from aura_core.config import load_yaml, program_rules, settings
from aura_core.log import get_logger

logger = get_logger("agent.eligibility")


class ClientState(BaseModel):
    """Estado do cliente consumido pelo motor de elegibilidade."""

    customer_id: str = "C000000"
    tier: str = "azul"  # azul, topazio, safira, diamante, diamante_unique
    persona: str = "executivo_recorrente"
    risk_state: str = "risco_alto_valor_alto"
    pontos_qualificaveis_12m: int = 0
    trechos_12m: int = 0
    gastos_12m_brl: float = 0.0
    saldo_pontos: int = 0
    pontos_expirando_30d: int = 0
    meta_proximo_nivel_pct: float = 0.0
    churn_prob: float = 0.5
    clv_12m_previsto: float = 1000.0
    alto_valor: bool = True
    atritos_dominantes: str | list[str] | dict[str, float] | None = None
    rota_favorita: str | None = None
    beneficio_nao_utilizado: str | None = None
    shap_top3: list[str] | str | None = None

    def get_atritos_set(self) -> set[str]:
        """Normaliza atritos para um conjunto de strings em minúsculas."""
        if not self.atritos_dominantes:
            return set()
        if isinstance(self.atritos_dominantes, str):
            parts = [
                p.strip().lower() for p in self.atritos_dominantes.replace(";", ",").split(",")
            ]
            return {p for p in parts if p}
        if isinstance(self.atritos_dominantes, list):
            return {str(x).strip().lower() for x in self.atritos_dominantes if str(x).strip()}
        if isinstance(self.atritos_dominantes, dict):
            return {str(k).strip().lower() for k, v in self.atritos_dominantes.items() if v}
        return set()


@dataclass(frozen=True)
class EligibilityResult:
    """Resultado da avaliação de elegibilidade para uma ação específica."""

    action_id: str
    action_name: str
    is_eligible: bool
    reasons: list[str]
    rules_triggered: list[str]
    requires_human_review: bool
    cost_brl: float
    channels: list[str]
    regulation_support: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Cotas e valores fixos de Resgate Especial do regulamento (AF-RESGATE-ESPECIAL-2025)
RESGATE_ESPECIAL_PONTOS = {
    "safira": 70000,
    "diamante": 50000,
}

# Metas de qualificação para cálculo de progresso
TIER_QUALIFICATION_TARGETS = {
    "azul": {"points": 0, "segments": 0, "next": "topazio"},
    "topazio": {"points": 6000, "segments": 6, "next": "safira"},
    "safira": {"points": 10000, "segments": 10, "next": "diamante"},
    "diamante": {"points": 12000, "segments": 12, "next": "diamante_unique"},
    "diamante_unique": {"points": 26000, "segments": 26, "next": None},
}


def _check_null_semantics_tier(tier_key: str, rules_doc: dict[str, Any]) -> dict[str, Any]:
    """Retorna os campos nulos do tier configurado no regulamento."""
    for t in rules_doc.get("tiers", []):
        if t.get("key") == tier_key:
            earn = t.get("earn", {})
            redemption = t.get("redemption", {})
            null_fields = []
            if earn.get("points_per_brl_flight") is None:
                null_fields.append("earn.points_per_brl_flight")
            if earn.get("points_validity_years") is None:
                null_fields.append("earn.points_validity_years")
            if redemption.get("national_ceiling_points") is None:
                null_fields.append("redemption.national_ceiling_points")
            if t.get("beneficiaries") is None:
                null_fields.append("beneficiaries")
            return {
                "has_nulls": len(null_fields) > 0,
                "null_fields": null_fields,
            }
    return {"has_nulls": False, "null_fields": []}


class EligibilityEngine:
    """Motor determinístico de elegibilidade de ações de retenção."""

    def __init__(
        self,
        actions_config: dict[str, Any] | None = None,
        rules_config: dict[str, Any] | None = None,
    ) -> None:
        self.actions_doc = actions_config or load_yaml("config/actions.yaml")
        self.rules_doc = rules_config or program_rules()

        st = settings()
        settings_budget = st.get("agent", {}).get("budget", {}).get("max_cost_brl_per_client")
        actions_budget = (
            self.actions_doc.get("meta", {}).get("budget", {}).get("max_cost_brl_per_client")
        )
        if settings_budget is not None:
            self.max_cost = float(settings_budget)
            if actions_budget is not None and float(actions_budget) != float(settings_budget):
                logger.warning(
                    "Divergência de orçamento: actions.yaml define R$ %.2f, mas settings.yaml define R$ %.2f. "
                    "Prevalecendo settings.yaml como fonte canônica.",
                    float(actions_budget),
                    float(settings_budget),
                )
        elif actions_budget is not None:
            self.max_cost = float(actions_budget)
        else:
            self.max_cost = 400.0

        self.max_cost_brl = self.max_cost

    def evaluate_action(
        self,
        action_name: str,
        client: ClientState,
    ) -> EligibilityResult:
        """Avalia determinísticamente se o cliente é elegível a uma ação específica."""
        actions_map = self.actions_doc.get("actions", {})
        if action_name not in actions_map:
            raise KeyError(f"Ação desconhecida no inventário: {action_name!r}")

        act = actions_map[action_name]
        action_id = str(act.get("id"))
        cost = float(act.get("cost_brl", 0.0))
        channels = list(act.get("channels", []))
        reg_supp = act.get("regulation_support")
        elig = act.get("eligibility", {})

        reasons: list[str] = []
        rules_triggered: list[str] = []
        is_eligible = True
        requires_human_review = False

        # ---------------------------------------------------------------------
        # 1. Checagem de Orçamento
        # ---------------------------------------------------------------------
        if cost > self.max_cost:
            is_eligible = False
            reasons.append(
                f"Custo da ação (R$ {cost:.2f}) excede teto por cliente (R$ {self.max_cost:.2f})"
            )
        else:
            rules_triggered.append(f"budget_check_ok (R$ {cost:.2f} <= R$ {self.max_cost:.2f})")

        # ---------------------------------------------------------------------
        # 2. Checagem de Persona
        # ---------------------------------------------------------------------
        allowed_personas = elig.get("personas_any")
        if allowed_personas:
            if client.persona in allowed_personas:
                rules_triggered.append(f"persona_match ({client.persona})")
            else:
                is_eligible = False
                reasons.append(f"Persona {client.persona!r} não autorizada para esta ação")

        # ---------------------------------------------------------------------
        # 3. Checagem de Estado de Risco
        # ---------------------------------------------------------------------
        allowed_risks = elig.get("risk_states_any")
        if allowed_risks:
            if client.risk_state in allowed_risks:
                rules_triggered.append(f"risk_state_match ({client.risk_state})")
            else:
                is_eligible = False
                reasons.append(f"Estado de risco {client.risk_state!r} não elegível")

        # ---------------------------------------------------------------------
        # 4. Checagem de Nível / Tier
        # ---------------------------------------------------------------------
        allowed_tiers = elig.get("tiers_any")
        if allowed_tiers:
            if client.tier in allowed_tiers:
                rules_triggered.append(f"tier_match ({client.tier})")
            else:
                is_eligible = False
                reasons.append(f"Tier {client.tier!r} não elegível (requer {allowed_tiers})")

        # ---------------------------------------------------------------------
        # 5. Fail-Safe do Regulamento: Semântica de Valores Nulos (null_semantics)
        # ---------------------------------------------------------------------
        tier_null_info = _check_null_semantics_tier(client.tier, self.rules_doc)
        if tier_null_info["has_nulls"] and action_name == "oferta_resgate_especial":
            # Diamante Unique não possui Resgate Especial definido no snapshot
            is_eligible = False
            requires_human_review = True
            reasons.append(
                "Resgate Especial não confirmado para Diamante Unique no snapshot vigente "
                "(fail-safe: regra null = INELEGÍVEL; requer revisão humana)"
            )
            rules_triggered.append("null_semantics_failsafe_triggered")

        # ---------------------------------------------------------------------
        # 6. Requisitos Específicos por Ação
        # ---------------------------------------------------------------------
        requires = elig.get("requires", [])
        atritos = client.get_atritos_set()

        # Requisito: proximo_do_proximo_nivel (>= 80% da meta)
        if "proximo_do_proximo_nivel" in requires or action_name == "antecipacao_de_nivel":
            if client.tier == "diamante_unique":
                is_eligible = False
                reasons.append(
                    "Cliente já no nível máximo (Diamante Unique); sem próximo nível para antecipação"
                )
            else:
                target_info = TIER_QUALIFICATION_TARGETS.get(client.tier, {})
                next_tier = target_info.get("next")
                pct = client.meta_proximo_nivel_pct

                # Se meta_proximo_nivel_pct não foi pré-calculada, verifica com base nos pontos/trechos
                if pct <= 0 and next_tier:
                    next_reqs = TIER_QUALIFICATION_TARGETS.get(next_tier, {})
                    target_pts = next_reqs.get("points", 0)
                    target_segs = next_reqs.get("segments", 0)
                    pct_pts = (
                        (client.pontos_qualificaveis_12m / target_pts) if target_pts > 0 else 0.0
                    )
                    pct_segs = (client.trechos_12m / target_segs) if target_segs > 0 else 0.0
                    pct = max(pct_pts, pct_segs)

                if pct >= 0.80:
                    rules_triggered.append(f"proximo_do_proximo_nivel_ok ({pct:.1%} >= 80%)")
                else:
                    is_eligible = False
                    reasons.append(
                        f"Progresso para o próximo nível insuficiente: {pct:.1%} (exige >= 80%)"
                    )

        # Requisito: saldo_suficiente_para_cota (Resgate Especial)
        if (
            "saldo_suficiente_para_cota" in requires or action_name == "oferta_resgate_especial"
        ) and client.tier in RESGATE_ESPECIAL_PONTOS:
            min_pts = RESGATE_ESPECIAL_PONTOS[client.tier]
            if client.saldo_pontos >= min_pts:
                rules_triggered.append(
                    f"saldo_suficiente_para_cota ({client.saldo_pontos} >= {min_pts})"
                )
            else:
                is_eligible = False
                reasons.append(
                    f"Saldo insuficiente para cota de resgate do nível {client.tier} "
                    f"(possui {client.saldo_pontos}, requer {min_pts})"
                )

        # Requisito: atrito_resgate_observado
        if "atrito_resgate_observado" in requires:
            if "resgate" in atritos:
                rules_triggered.append("atrito_resgate_observado")
            else:
                is_eligible = False
                reasons.append("Atrito com resgate de pontos não observado no histórico do cliente")

        # Requisito: rota_favorita_definida
        if "rota_favorita_definida" in requires:
            if client.rota_favorita and str(client.rota_favorita).strip():
                rules_triggered.append(f"rota_favorita_definida ({client.rota_favorita})")
            else:
                is_eligible = False
                reasons.append("Rota favorita não definida para personalização da oferta")

        # Requisito: atrito_atraso_observado
        if "atrito_atraso_observado" in requires:
            if "atraso" in atritos:
                rules_triggered.append("atrito_atraso_observado")
            else:
                is_eligible = False
                reasons.append("Atrito com atraso de voo não observado no histórico do cliente")

        # Requisito: beneficio_nivel_nao_utilizado
        if "beneficio_nivel_nao_utilizado" in requires:
            if client.beneficio_nao_utilizado and str(client.beneficio_nao_utilizado).strip():
                # Se for Diamante Unique e o benefício não utilizado envolver regra null
                if client.tier == "diamante_unique":
                    ben_str = str(client.beneficio_nao_utilizado).lower()
                    if any(
                        k in ben_str for k in ["multiplicador", "validade", "teto", "beneficiarios"]
                    ):
                        is_eligible = False
                        requires_human_review = True
                        reasons.append(
                            f"Benefício '{client.beneficio_nao_utilizado}' envolve regra null em Diamante Unique "
                            "(fail-safe: revisão humana necessária)"
                        )
                    else:
                        rules_triggered.append(
                            f"beneficio_nivel_nao_utilizado ({client.beneficio_nao_utilizado})"
                        )
                else:
                    rules_triggered.append(
                        f"beneficio_nivel_nao_utilizado ({client.beneficio_nao_utilizado})"
                    )
            else:
                is_eligible = False
                reasons.append("Nenhum benefício de nível não-utilizado identificado")

        return EligibilityResult(
            action_id=action_id,
            action_name=action_name,
            is_eligible=is_eligible,
            reasons=reasons,
            rules_triggered=rules_triggered,
            requires_human_review=requires_human_review,
            cost_brl=cost,
            channels=channels,
            regulation_support=reg_supp,
        )

    def evaluate_all(self, client: ClientState) -> list[EligibilityResult]:
        """Avalia todas as ações do inventário contra o estado do cliente."""
        results: list[EligibilityResult] = []
        for act_name in self.actions_doc.get("actions", {}):
            res = self.evaluate_action(act_name, client)
            results.append(res)
        return results

    def get_eligible_actions(self, client: ClientState) -> list[EligibilityResult]:
        """Filtra apenas as ações estritamente elegíveis."""
        return [res for res in self.evaluate_all(client) if res.is_eligible]
