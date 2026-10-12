"""Testes exaustivos do motor determinístico de elegibilidade (agent/eligibility.py).

Cobre:
- Todas as 10 ações do catálogo actions.yaml
- Fail-safe de semântica de valores nulos (null_semantics) para Diamante Unique
- Casos de borda:
    * Saldo exatamente no valor mínimo (70.000 Safira, 50.000 Diamante) e 1 ponto abaixo
    * Meta de qualificação exatamente em 80% (0.80) e abaixo (0.799)
    * Cliente Diamante Unique solicitando Resgate Especial (inelegível + revisão humana)
"""

import pytest

from agent.eligibility import ClientState, EligibilityEngine


@pytest.fixture
def engine() -> EligibilityEngine:
    return EligibilityEngine()


# =============================================================================
# 1. Testes de Casos de Borda Específicos
# =============================================================================


def test_regressao_atrito_resgate_milhas_taxonomia_real(engine: EligibilityEngine):
    """Bugfix WS7b (achado #4): a taxonomia de aspectos da WS6 rotula o atrito de
    resgate como 'resgate_milhas'. O teste de membership exato em 'resgate' nunca
    disparava na base real — a semântica correta é substring. Guards contra
    regressão usando o valor REAL produzido pelo pipeline."""
    client = ClientState(
        tier="safira",
        persona="maximizador_milhas",
        risk_state="risco_alto_valor_alto",
        saldo_pontos=70000,
        atritos_dominantes="resgate_milhas",  # valor real da taxonomia
    )
    res = engine.evaluate_action("oferta_resgate_especial", client)
    assert res.is_eligible is True
    assert "atrito_resgate_observado" in res.rules_triggered

    # Atrito sem relação a resgate não pode acionar a regra
    client_outro = ClientState(
        tier="safira",
        persona="maximizador_milhas",
        risk_state="risco_alto_valor_alto",
        saldo_pontos=70000,
        atritos_dominantes="preco",
    )
    res_outro = engine.evaluate_action("oferta_resgate_especial", client_outro)
    assert res_outro.is_eligible is False
    assert "atrito_resgate_observado" not in res_outro.rules_triggered


def test_borda_saldo_exatamente_no_minimo_safira(engine: EligibilityEngine):
    """Safira exige 70.000 pontos para cota de Resgate Especial."""
    # Exatamente no mínimo: elegível
    client_exact = ClientState(
        tier="safira",
        persona="maximizador_milhas",
        risk_state="risco_alto_valor_alto",
        saldo_pontos=70000,
        atritos_dominantes="resgate",
    )
    res_exact = engine.evaluate_action("oferta_resgate_especial", client_exact)
    assert res_exact.is_eligible is True
    assert any("saldo_suficiente_para_cota" in r for r in res_exact.rules_triggered)

    # 1 ponto abaixo: estritamente inelegível
    client_below = ClientState(
        tier="safira",
        persona="maximizador_milhas",
        risk_state="risco_alto_valor_alto",
        saldo_pontos=69999,
        atritos_dominantes="resgate",
    )
    res_below = engine.evaluate_action("oferta_resgate_especial", client_below)
    assert res_below.is_eligible is False
    assert any("Saldo insuficiente" in r for r in res_below.reasons)


def test_borda_saldo_exatamente_no_minimo_diamante(engine: EligibilityEngine):
    """Diamante exige 50.000 pontos para cota de Resgate Especial."""
    # Exatamente no mínimo: elegível
    client_exact = ClientState(
        tier="diamante",
        persona="maximizador_milhas",
        risk_state="risco_alto_valor_alto",
        saldo_pontos=50000,
        atritos_dominantes="resgate",
    )
    res_exact = engine.evaluate_action("oferta_resgate_especial", client_exact)
    assert res_exact.is_eligible is True

    # 1 ponto abaixo: inelegível
    client_below = ClientState(
        tier="diamante",
        persona="maximizador_milhas",
        risk_state="risco_alto_valor_alto",
        saldo_pontos=49999,
        atritos_dominantes="resgate",
    )
    res_below = engine.evaluate_action("oferta_resgate_especial", client_below)
    assert res_below.is_eligible is False
    assert any("Saldo insuficiente" in r for r in res_below.reasons)


def test_borda_meta_exatamente_em_80_porcento(engine: EligibilityEngine):
    """Antecipação de nível exige >= 80% (0.80) da meta do próximo nível."""
    # Exatamente em 80% (0.80) -> elegível
    c_80 = ClientState(
        tier="topazio",
        persona="executivo_recorrente",
        risk_state="risco_alto_valor_alto",
        meta_proximo_nivel_pct=0.80,
    )
    res_80 = engine.evaluate_action("antecipacao_de_nivel", c_80)
    assert res_80.is_eligible is True
    assert any("proximo_do_proximo_nivel_ok" in r for r in res_80.rules_triggered)

    # Abaixo de 80% (ex: 0.799) -> inelegível
    c_799 = ClientState(
        tier="topazio",
        persona="executivo_recorrente",
        risk_state="risco_alto_valor_alto",
        meta_proximo_nivel_pct=0.799,
    )
    res_799 = engine.evaluate_action("antecipacao_de_nivel", c_799)
    assert res_799.is_eligible is False
    assert any("Progresso para o próximo nível insuficiente" in r for r in res_799.reasons)


def test_fail_safe_diamante_unique_resgate_especial(engine: EligibilityEngine):
    """Diamante Unique pedindo Resgate Especial aciona fail-safe de regra null e revisão humana."""
    client_du = ClientState(
        tier="diamante_unique",
        persona="maximizador_milhas",
        risk_state="risco_alto_valor_alto",
        saldo_pontos=150000,
        atritos_dominantes="resgate",
    )
    res = engine.evaluate_action("oferta_resgate_especial", client_du)
    # Deve ser inelegível E exigir revisão humana obrigatória
    assert res.is_eligible is False
    assert res.requires_human_review is True
    assert any("fail-safe" in r.lower() or "revisão humana" in r.lower() for r in res.reasons)


def test_fail_safe_diamante_unique_antecipacao_nivel(engine: EligibilityEngine):
    """Diamante Unique é o nível mais alto; antecipação não tem próximo nível."""
    client_du = ClientState(
        tier="diamante_unique",
        persona="executivo_recorrente",
        meta_proximo_nivel_pct=1.0,
    )
    res = engine.evaluate_action("antecipacao_de_nivel", client_du)
    assert res.is_eligible is False
    assert any("nível máximo" in r for r in res.reasons)


def test_fail_safe_diamante_unique_beneficio_nulo(engine: EligibilityEngine):
    """Se o benefício envolver regra null (ex.: multiplicadores/validade), aciona revisão humana."""
    client_du = ClientState(
        tier="diamante_unique",
        persona="executivo_recorrente",
        beneficio_nao_utilizado="multiplicador_pontos_acumulo",
    )
    res = engine.evaluate_action("educacao_beneficio_existente", client_du)
    assert res.is_eligible is False
    assert res.requires_human_review is True


# =============================================================================
# 2. Cobertura de Todas as 10 Ações de actions.yaml
# =============================================================================


def test_action_contato_proativo_relacionamento(engine: EligibilityEngine):
    c_ok = ClientState(persona="executivo_recorrente", risk_state="risco_alto_valor_alto")
    assert engine.evaluate_action("contato_proativo_relacionamento", c_ok).is_eligible is True

    c_bad_risk = ClientState(persona="executivo_recorrente", risk_state="risco_baixo_estavel")
    assert (
        engine.evaluate_action("contato_proativo_relacionamento", c_bad_risk).is_eligible is False
    )

    c_bad_persona = ClientState(persona="lazer_premium", risk_state="risco_alto_valor_alto")
    assert (
        engine.evaluate_action("contato_proativo_relacionamento", c_bad_persona).is_eligible
        is False
    )


def test_action_gesto_reconhecimento_bonus_pontos(engine: EligibilityEngine):
    c_ok = ClientState(tier="safira", risk_state="risco_alto_valor_alto")
    assert engine.evaluate_action("gesto_reconhecimento_bonus_pontos", c_ok).is_eligible is True

    c_du = ClientState(tier="diamante_unique", risk_state="risco_alto_valor_alto")
    assert engine.evaluate_action("gesto_reconhecimento_bonus_pontos", c_du).is_eligible is False

    c_low_risk = ClientState(tier="safira", risk_state="risco_baixo_estavel")
    assert (
        engine.evaluate_action("gesto_reconhecimento_bonus_pontos", c_low_risk).is_eligible is False
    )


def test_action_antecipacao_de_nivel(engine: EligibilityEngine):
    c_ok = ClientState(tier="safira", persona="maximizador_milhas", meta_proximo_nivel_pct=0.85)
    assert engine.evaluate_action("antecipacao_de_nivel", c_ok).is_eligible is True

    c_bad_persona = ClientState(tier="safira", persona="lazer_premium", meta_proximo_nivel_pct=0.85)
    assert engine.evaluate_action("antecipacao_de_nivel", c_bad_persona).is_eligible is False


def test_action_oferta_resgate_especial(engine: EligibilityEngine):
    # Safira com saldo e atrito
    c_ok = ClientState(
        tier="safira",
        persona="maximizador_milhas",
        saldo_pontos=80000,
        atritos_dominantes="resgate",
    )
    assert engine.evaluate_action("oferta_resgate_especial", c_ok).is_eligible is True

    # Sem atrito de resgate -> inelegível
    c_no_atrito = ClientState(
        tier="safira",
        persona="maximizador_milhas",
        saldo_pontos=80000,
        atritos_dominantes="bagagem",
    )
    assert engine.evaluate_action("oferta_resgate_especial", c_no_atrito).is_eligible is False


def test_action_oferta_rota_favorita(engine: EligibilityEngine):
    c_ok = ClientState(
        persona="lazer_premium",
        risk_state="risco_baixo_potencial_alto",
        rota_favorita="VCP-FOR",
    )
    assert engine.evaluate_action("oferta_rota_favorita", c_ok).is_eligible is True

    c_no_route = ClientState(
        persona="lazer_premium",
        risk_state="risco_baixo_potencial_alto",
        rota_favorita=None,
    )
    assert engine.evaluate_action("oferta_rota_favorita", c_no_route).is_eligible is False


def test_action_pacote_experiencia_destino(engine: EligibilityEngine):
    c_ok = ClientState(persona="lazer_premium", risk_state="risco_baixo_potencial_alto")
    assert engine.evaluate_action("pacote_experiencia_destino", c_ok).is_eligible is True

    c_bad = ClientState(persona="regional_dependente", risk_state="risco_baixo_potencial_alto")
    assert engine.evaluate_action("pacote_experiencia_destino", c_bad).is_eligible is False


def test_action_missao_acumulo_parceiro(engine: EligibilityEngine):
    c_ok = ClientState(persona="maximizador_milhas", risk_state="risco_medio_valor_alto")
    assert engine.evaluate_action("missao_acumulo_parceiro", c_ok).is_eligible is True

    c_bad = ClientState(persona="executivo_recorrente", risk_state="risco_medio_valor_alto")
    assert engine.evaluate_action("missao_acumulo_parceiro", c_bad).is_eligible is False


def test_action_aviso_antecipado_prioridade(engine: EligibilityEngine):
    c_ok = ClientState(persona="regional_dependente")
    assert engine.evaluate_action("aviso_antecipado_prioridade", c_ok).is_eligible is True

    c_bad = ClientState(persona="lazer_premium")
    assert engine.evaluate_action("aviso_antecipado_prioridade", c_bad).is_eligible is False


def test_action_reencaminhamento_atraso(engine: EligibilityEngine):
    c_ok = ClientState(risk_state="risco_alto_valor_alto", atritos_dominantes="atraso")
    assert engine.evaluate_action("reencaminhamento_atraso", c_ok).is_eligible is True

    c_no_atraso = ClientState(risk_state="risco_alto_valor_alto", atritos_dominantes="resgate")
    assert engine.evaluate_action("reencaminhamento_atraso", c_no_atraso).is_eligible is False


def test_action_educacao_beneficio_existente(engine: EligibilityEngine):
    c_ok = ClientState(tier="safira", beneficio_nao_utilizado="duas_bagagens_gratuitas")
    assert engine.evaluate_action("educacao_beneficio_existente", c_ok).is_eligible is True

    c_no_ben = ClientState(tier="safira", beneficio_nao_utilizado=None)
    assert engine.evaluate_action("educacao_beneficio_existente", c_no_ben).is_eligible is False


def test_budget_ceiling_leitura_canonica_settings(engine: EligibilityEngine):
    """Verifica que o motor lê o teto orçamentário de settings.yaml (ACH-11)."""
    from aura_core.config import settings

    expected_ceiling = float(
        settings().get("agent", {}).get("budget", {}).get("max_cost_brl_per_client", 100.0)
    )
    assert engine.max_cost_brl == expected_ceiling


def test_cliente_sem_acoes_elegiveis_retorna_lista_vazia_e_pipeline_no_action(
    engine: EligibilityEngine,
):
    """Cliente sem correspondência de persona/risco recebe lista vazia e ACT-NO-ACTION (ACH-01)."""
    from agent.pipeline import RetentionAgentPipeline

    # Cliente fora de qualquer perfil de elegibilidade
    c_ineligible = ClientState(
        customer_id="C_ZERO_ELIGIBLE",
        persona="turista_esporadico_desconhecido",
        risk_state="sem_risco_neutro",
        saldo_pontos=100,
        meta_proximo_nivel_pct=0.01,
    )
    eligible = engine.get_eligible_actions(c_ineligible)
    assert len(eligible) == 0, "Nenhuma ação deve ser elegível para este cliente"

    pipeline = RetentionAgentPipeline()
    rec = pipeline.run_for_client(c_ineligible)
    assert rec.action_id == "ACT-NO-ACTION"
    assert rec.action_name == "nenhuma_acao_elegivel"
    assert rec.channel == "nenhum"
    assert rec.human_review is True
    assert rec.action_name != "contato_proativo_relacionamento"
