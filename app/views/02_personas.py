"""Tela 02 — Personas e Segmentação Comportamental.

Conteúdo:
- Cards das personas com cor de identidade visual
- Métricas: tamanho (nº clientes, share %), CLV médio, risco médio (P_churn)
- Atritos dominantes (alimentados da frente de sentimento)
- Ação recomendada do playbook de retenção
- Tabela comparativa detalhada dos arquétipos
"""

from __future__ import annotations

import streamlit as st

from app.components import (
    render_fixture_banner,
    render_synthetic_banner,
    section_title,
)
from app.loader import load_personas_data
from app.theme import (
    AZUL_ACTION,
    AZUL_NAVY,
    BORDER_SUBTLE,
    PERSONA_TOKENS,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    format_currency_brl,
    format_int_br,
    format_percent,
)


def render() -> None:
    render_synthetic_banner()

    df_personas, is_fixture = load_personas_data()
    render_fixture_banner(is_fixture)

    section_title(
        "Personas do Azul Fidelidade e Playbook de Retenção",
        "Segmentação comportamental orientada a valor: perfil quantitativo, atritos preponderantes e ações de retenção.",
    )

    if df_personas.empty:
        st.warning("Nenhuma persona encontrada.")
        return

    # Renderiza grid de cards das personas (2 colunas)
    cols = st.columns(2)

    for idx, (_, row) in enumerate(df_personas.iterrows()):
        col = cols[idx % 2]
        p_key = row["persona"]
        token = PERSONA_TOKENS.get(
            p_key, {"color": AZUL_ACTION, "icon": "👤", "bg_soft": "#F8FAFC"}
        )

        border_color = token["color"]
        icon = token.get("icon", "👤")

        with col:
            html_card = f"""
            <div class="aura-persona-card" style="border-top: 4px solid {border_color};">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                    <div>
                        <div style="font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; color: {border_color};">
                            {icon} Arquétipo Analítico
                        </div>
                        <h3 style="margin: 2px 0 0 0; font-size: 17px; font-weight: 800; color: {AZUL_NAVY};">
                            {row["nome_display"]}
                        </h3>
                    </div>
                    <span style="background: {token.get("bg_soft", "#F1F5F9")}; color: {border_color}; font-size: 11px; font-weight: 800; padding: 4px 8px; border-radius: 4px; border: 1px solid {border_color}33;">
                        {format_percent(row["share_pct"])} da base
                    </span>
                </div>

                <p style="font-size: 12px; color: {TEXT_SECONDARY}; line-height: 1.4; margin-bottom: 14px;">
                    {row["descricao"]}
                </p>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; background: #F8F9FA; padding: 10px; border-radius: 6px; border: 1px solid {BORDER_SUBTLE}; margin-bottom: 14px;">
                    <div>
                        <span style="font-size: 10px; text-transform: uppercase; color: {TEXT_SECONDARY}; font-weight: 700; display: block;">CLV 12M Médio</span>
                        <strong style="font-size: 15px; color: {AZUL_NAVY};">{format_currency_brl(row["clv_medio"])}</strong>
                    </div>
                    <div>
                        <span style="font-size: 10px; text-transform: uppercase; color: {TEXT_SECONDARY}; font-weight: 700; display: block;">Risco Médio (Churn)</span>
                        <strong style="font-size: 15px; color: {"#E832A5" if row["churn_medio"] > 0.35 else AZUL_ACTION};">{format_percent(row["churn_medio"])}</strong>
                    </div>
                    <div>
                        <span style="font-size: 10px; text-transform: uppercase; color: {TEXT_SECONDARY}; font-weight: 700; display: block;">Tamanho do Grupo</span>
                        <strong style="font-size: 13px; color: {TEXT_PRIMARY};">{format_int_br(row["clientes_count"])} membros</strong>
                    </div>
                    <div>
                        <span style="font-size: 10px; text-transform: uppercase; color: {TEXT_SECONDARY}; font-weight: 700; display: block;">Ticket Médio Est.</span>
                        <strong style="font-size: 13px; color: {TEXT_PRIMARY};">{format_currency_brl(row.get("ticket_medio", 0))}</strong>
                    </div>
                </div>

                <div style="font-size: 11px; margin-bottom: 6px;">
                    <span style="font-weight: 700; color: {AZUL_NAVY};">⚠️ Atritos Dominantes:</span>
                    <span style="color: {TEXT_PRIMARY}; background: #FFF1F2; padding: 2px 6px; border-radius: 4px; font-weight: 600; margin-left: 4px;">{row["atritos_dominantes"]}</span>
                </div>

                <div style="font-size: 11px;">
                    <span style="font-weight: 700; color: {AZUL_NAVY};">🎯 Ação Recomendada:</span>
                    <span style="color: {AZUL_ACTION}; font-weight: 700; margin-left: 4px;">{row["acao_recomendada"]}</span>
                </div>
            </div>
            """
            st.markdown(html_card, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

    # Tabela comparativa e playbook
    section_title(
        "Comparativo Analítico das Personas",
        "Visão tabular das premissas comportamentais e impacto na carteira",
    )

    display_df = df_personas[
        [
            "nome_display",
            "clientes_count",
            "share_pct",
            "clv_medio",
            "churn_medio",
            "valor_em_risco_total",
            "atritos_dominantes",
            "acao_recomendada",
        ]
    ].copy()

    display_df.columns = [
        "Persona",
        "Membros",
        "Share (%)",
        "CLV Médio (R$)",
        "Risco Churn",
        "Valor em Risco Total (R$)",
        "Atritos Principais",
        "Ação do Playbook",
    ]

    display_df["Share (%)"] = display_df["Share (%)"].apply(lambda v: format_percent(v))
    display_df["CLV Médio (R$)"] = display_df["CLV Médio (R$)"].apply(
        lambda v: format_currency_brl(v)
    )
    display_df["Risco Churn"] = display_df["Risco Churn"].apply(lambda v: format_percent(v))
    display_df["Valor em Risco Total (R$)"] = display_df["Valor em Risco Total (R$)"].apply(
        lambda v: format_currency_brl(v)
    )
    display_df["Membros"] = display_df["Membros"].apply(lambda v: format_int_br(v))

    st.dataframe(display_df, width="stretch", hide_index=True)


render()
