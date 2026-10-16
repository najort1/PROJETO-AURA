"""Tela 06 — Simulador de Impacto Financeiro e Retenção.

Conteúdo:
- Simulador interativo com sliders de parâmetros de campanha:
  * Orçamento total (R$)
  * Taxa de resposta (%)
  * Efeito da ação em P(evasão) (%)
  * Custo médio por ação (R$)
  * Margem de contribuição (%)
- Recálculo dinâmico baseado na fórmula canônica:
  ΔReceita = Σ_alvo [ P(evasão evitada | ação) × CLV_12m × margem ] − custos
- Cenários pré-definidos (chips/botões): Conservador, Base, Otimista
- Premissas explícitas na tela com nota permanente "estimativa, não resultado validado"
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from app.components import (
    metric_row,
    render_fixture_banner,
    render_synthetic_banner,
    section_title,
)
from app.loader import load_customers_data
from app.theme import (
    AZUL_ACTION,
    AZUL_DEEP,
    AZUL_NAVY,
    AZUL_PRIMARY,
    BORDER_SUBTLE,
    CANVAS,
    MAGENTA_CTA,
    RADIUS_MD,
    SURFACE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WARNING,
    format_currency_brl,
    format_int_br,
)


def render() -> None:
    render_synthetic_banner()

    df_customers, is_fixture = load_customers_data()
    render_fixture_banner(is_fixture)

    section_title(
        "Simulador de Impacto Financeiro da Retenção",
        "Projeção interativa de retorno financeiro (ΔReceita) sobre a carteira sob diferentes premissas de resposta e eficácia.",
    )

    # Nota explícita de estimativa metodológica
    st.markdown(
        f"""
        <div style="background: #FFFBEB; border: 1px solid #FDE68A; border-left: 4px solid #F59E0B; border-radius: {RADIUS_MD}; padding: 12px 16px; margin-bottom: 20px; font-size: 12px; color: #92400E;">
            <strong>⚠️ NOTA METODOLÓGICA (RIGOR ANALÍTICO):</strong>
            Os valores projetados representam uma <em>estimativa sob premissas declaradas</em>, não um resultado validado em produção.
            No mundo real, a eficácia de cada ação deve ser calibrada mediante testes A/B com grupo de controle antes de escala plena.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df_customers.empty:
        st.warning("Carteira indisponível para simulação.")
        return

    # Cenários Pré-definidos
    scenarios = {
        "Conservador": {
            "orcamento": 50000,
            "taxa_resposta": 0.08,
            "efeito_acao": 0.15,
            "custo_acao": 55.0,
            "margem": 0.18,
            "desc": "Baixa adesão e redução cautelosa de risco (cenário de estresse).",
        },
        "Base (Recomendado)": {
            "orcamento": 80000,
            "taxa_resposta": 0.18,
            "efeito_acao": 0.25,
            "custo_acao": 45.0,
            "margem": 0.22,
            "desc": "Parâmetros centrais calibrados com benchmarks de programas de fidelidade.",
        },
        "Otimista": {
            "orcamento": 120000,
            "taxa_resposta": 0.30,
            "efeito_acao": 0.38,
            "custo_acao": 38.0,
            "margem": 0.26,
            "desc": "Engajamento elevado impulsionado por canais proativos e ofertas personalizadas.",
        },
    }

    st.write("##### Cenários Rápidos Pré-configurados:")
    col_scen1, col_scen2, col_scen3 = st.columns(3)

    if "current_scenario" not in st.session_state:
        st.session_state["current_scenario"] = "Base (Recomendado)"

    with col_scen1:
        if st.button("🛡️ Conservador", width="stretch"):
            st.session_state["current_scenario"] = "Conservador"
            sc = scenarios["Conservador"]
            st.session_state["sim_orcamento"] = sc["orcamento"]
            st.session_state["sim_taxa_resp"] = int(sc["taxa_resposta"] * 100)
            st.session_state["sim_efeito"] = int(sc["efeito_acao"] * 100)
            st.session_state["sim_custo"] = float(sc["custo_acao"])
            st.session_state["sim_margem"] = int(sc["margem"] * 100)
            st.rerun()

    with col_scen2:
        if st.button(
            "⚖️ Base (Recomendado)",
            type="primary"
            if st.session_state["current_scenario"] == "Base (Recomendado)"
            else "secondary",
            width="stretch",
        ):
            st.session_state["current_scenario"] = "Base (Recomendado)"
            sc = scenarios["Base (Recomendado)"]
            st.session_state["sim_orcamento"] = sc["orcamento"]
            st.session_state["sim_taxa_resp"] = int(sc["taxa_resposta"] * 100)
            st.session_state["sim_efeito"] = int(sc["efeito_acao"] * 100)
            st.session_state["sim_custo"] = float(sc["custo_acao"])
            st.session_state["sim_margem"] = int(sc["margem"] * 100)
            st.rerun()

    with col_scen3:
        if st.button("🚀 Otimista", width="stretch"):
            st.session_state["current_scenario"] = "Otimista"
            sc = scenarios["Otimista"]
            st.session_state["sim_orcamento"] = sc["orcamento"]
            st.session_state["sim_taxa_resp"] = int(sc["taxa_resposta"] * 100)
            st.session_state["sim_efeito"] = int(sc["efeito_acao"] * 100)
            st.session_state["sim_custo"] = float(sc["custo_acao"])
            st.session_state["sim_margem"] = int(sc["margem"] * 100)
            st.rerun()

    cur_sc = scenarios.get(st.session_state["current_scenario"], scenarios["Base (Recomendado)"])
    st.caption(f"Cenário ativo: **{st.session_state['current_scenario']}** — {cur_sc['desc']}")

    st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)

    # Painel de Sliders
    st.write("##### Ajuste Fino dos Parâmetros da Campanha:")
    col_sl1, col_sl2 = st.columns(2)

    with col_sl1:
        orcamento = st.slider(
            "Orçamento Total Disponível (R$):",
            min_value=10000,
            max_value=300000,
            value=st.session_state.get("sim_orcamento", cur_sc["orcamento"]),
            step=5000,
            format="R$ %d",
            key="slider_orcamento",
        )
        taxa_resp_pct = st.slider(
            "Taxa de Resposta do Cliente (%):",
            min_value=3,
            max_value=50,
            value=st.session_state.get("sim_taxa_resp", int(cur_sc["taxa_resposta"] * 100)),
            step=1,
            format="%d%%",
            key="slider_taxa_resp",
        )
        custo_por_acao = st.slider(
            "Custo Médio por Ação (R$):",
            min_value=15.0,
            max_value=120.0,
            value=float(st.session_state.get("sim_custo", cur_sc["custo_acao"])),
            step=2.5,
            format="R$ %.2f",
            key="slider_custo",
        )

    with col_sl2:
        efeito_acao_pct = st.slider(
            "Efeito da Ação na Redução de Evasão (%):",
            min_value=5,
            max_value=60,
            value=st.session_state.get("sim_efeito", int(cur_sc["efeito_acao"] * 100)),
            step=1,
            format="%d%%",
            key="slider_efeito",
        )
        margem_pct = st.slider(
            "Margem de Contribuição Líquida (%):",
            min_value=10,
            max_value=40,
            value=st.session_state.get("sim_margem", int(cur_sc["margem"] * 100)),
            step=1,
            format="%d%%",
            key="slider_margem",
        )
        st.markdown(
            f"""
            <div style="background: {SURFACE}; border: 1px solid {BORDER_SUBTLE}; border-radius: {RADIUS_MD}; padding: 12px; font-size: 11px; color: {TEXT_SECONDARY}; margin-top: 10px;">
                <strong>Fórmula de Recálculo em Tempo Real:</strong><br>
                <code>ΔReceita = Σ_alvo [ (P_churn × Efeito × TaxaResp) × CLV_12M × Margem ] − CustoTotal</code>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # CÁLCULO DO IMPACTO SOBRE A BASE REAL CARREGADA
    taxa_resp = taxa_resp_pct / 100.0
    efeito_acao = efeito_acao_pct / 100.0
    margem = margem_pct / 100.0

    # Ordena carteira por Valor em Risco decrescente (prioridade analítica)
    df_prioritized = df_customers.sort_values("valor_em_risco", ascending=False).copy()

    # Quantidade de clientes que o orçamento comporta
    max_clientes_alcancaveis = int(orcamento // custo_por_acao)
    n_alvo = min(len(df_prioritized), max_clientes_alcancaveis)
    df_target = df_prioritized.iloc[:n_alvo].copy()

    # Cálculo por cliente:
    p_evitada = df_target["churn_prob"] * efeito_acao * taxa_resp
    receita_salva_bruta = (p_evitada * df_target["clv_12m_previsto"] * margem).sum()
    evasoes_evitadas_abs = p_evitada.sum()

    custo_total_campanha = n_alvo * custo_por_acao
    delta_receita_liquida = receita_salva_bruta - custo_total_campanha
    roi_liquido = (
        (delta_receita_liquida / custo_total_campanha) if custo_total_campanha > 0 else 0.0
    )

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

    # Resultados do Impacto Projetado
    section_title(
        "Resultados da Simulação na Carteira Carregada",
        "Retorno projetado sobre os clientes priorizados pelo algoritmo",
    )

    metric_row(
        [
            {
                "title": "ΔReceita Líquida Estimada",
                "value": format_currency_brl(delta_receita_liquida),
                "subtitle": "Receita salva ponderada menos custos",
                "border_color": MAGENTA_CTA if delta_receita_liquida > 0 else WARNING,
                "delta": f"ROI: {roi_liquido * 100:+.1f}%",
                "delta_positive": delta_receita_liquida > 0,
            },
            {
                "title": "Receita Bruta Preservada",
                "value": format_currency_brl(receita_salva_bruta),
                "subtitle": f"Margem de {margem_pct}% sobre CLV retido",
                "border_color": AZUL_ACTION,
            },
            {
                "title": "Investimento Total da Campanha",
                "value": format_currency_brl(custo_total_campanha),
                "subtitle": f"{format_currency_brl(custo_por_acao)} / cliente abordado",
                "border_color": AZUL_NAVY,
            },
            {
                "title": "Clientes Abordados",
                "value": f"{format_int_br(n_alvo)} ({n_alvo / len(df_customers) * 100:.1f}%)",
                "subtitle": "Top prioridade em Valor em Risco",
                "border_color": AZUL_PRIMARY,
            },
            {
                "title": "Evasões Evitadas (Absoluto)",
                "value": f"~{evasoes_evitadas_abs:.1f} clientes",
                "subtitle": f"Taxa média evitada: {evasoes_evitadas_abs / max(1, n_alvo) * 100:.2f}%",
                "border_color": AZUL_DEEP,
            },
        ]
    )

    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

    # Gráfico de Cascata Financeira (Waterfall Custo vs Receita vs Líquido)
    col_chart, col_breakdown = st.columns([1.1, 0.9])

    with col_chart:
        section_title(
            "Decomposição Financeira do Retorno",
            "Comparativo de investimento, receita preservada e lucro marginal",
        )
        fig, ax = plt.subplots(figsize=(6, 3.2), facecolor=CANVAS)
        ax.set_facecolor("#FFFFFF")

        bars_labels = ["Investimento (Custo)", "Receita Salva Bruta", "ΔReceita Líquida"]
        bars_values = [custo_total_campanha, receita_salva_bruta, delta_receita_liquida]
        bars_colors = [
            AZUL_NAVY,
            AZUL_ACTION,
            MAGENTA_CTA if delta_receita_liquida > 0 else WARNING,
        ]

        x_pos = np.arange(len(bars_labels))
        bars = ax.bar(x_pos, bars_values, color=bars_colors, width=0.45, edgecolor=BORDER_SUBTLE)

        for bar, val in zip(bars, bars_values, strict=False):
            h = bar.get_height()
            y_text = h + (max(bars_values) * 0.02) if h >= 0 else h - (abs(min(bars_values)) * 0.05)
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                y_text,
                format_currency_brl(val),
                ha="center",
                va="bottom" if h >= 0 else "top",
                fontsize=8.5,
                fontweight="bold",
                color=AZUL_NAVY,
            )

        ax.axhline(0, color=TEXT_SECONDARY, linewidth=0.8)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(bars_labels, fontsize=8.5, fontweight="bold", color=TEXT_PRIMARY)
        ax.set_ylabel("Valor em Reais (R$)", fontsize=8.5, color=TEXT_PRIMARY)
        ax.set_ylim(min(0, min(bars_values) * 1.2), max(bars_values) * 1.25)
        ax.tick_params(colors=TEXT_SECONDARY, labelsize=8)
        for spine in ax.spines.values():
            spine.set_color(BORDER_SUBTLE)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    with col_breakdown:
        section_title(
            "Distribuição do Alvo por Categoria",
            "Membros selecionados pelo critério de maior Valor em Risco",
        )
        tier_counts = df_target["tier"].value_counts().reset_index()
        tier_counts.columns = ["Categoria", "Clientes Alvo"]
        tier_counts["Share (%)"] = (tier_counts["Clientes Alvo"] / n_alvo * 100).apply(
            lambda v: f"{v:.1f}%"
        )
        st.dataframe(tier_counts, width="stretch", hide_index=True)


render()
