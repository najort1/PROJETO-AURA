"""Tela 03 — Visão Cliente 360 e Explicabilidade SHAP.

Conteúdo:
- Seletor de cliente (busca por ID, ordenável por Valor em Risco, CLV ou Churn)
- Scores analíticos: CLV 12M, Probabilidade de Churn, Valor em Risco, ScoreAV
- Badge de categoria (tier) com cor oficial e progresso de qualificação
- Explicabilidade SHAP: principais fatores explicativos locais do modelo de risco
- Atritos recentes identificados
- Linha do tempo de eventos do cliente (voos, resgates, atritos, evolução de tier)
"""
from __future__ import annotations

import contextlib
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from app.components import (
    metric_row,
    render_fixture_banner,
    render_synthetic_banner,
    section_title,
    tier_badge,
)
from app.loader import load_customers_data, load_dataset, load_timeline_data
from app.theme import (
    AZUL_ACTION,
    AZUL_DEEP,
    AZUL_NAVY,
    AZUL_PRIMARY,
    BORDER_SUBTLE,
    CANVAS,
    MAGENTA_CTA,
    PERSONA_TOKENS,
    RADIUS_MD,
    SURFACE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    format_currency_brl,
    format_date_br,
    format_int_br,
    format_percent,
)


def render() -> None:
    render_synthetic_banner()

    df_customers, is_fixture = load_customers_data()
    render_fixture_banner(is_fixture)

    section_title(
        "Cliente 360: Scores Preditivos e Explicabilidade",
        "Inspeção individualizada de risco, valor de vida, fatores SHAP locais e histórico de relacionamento.",
    )

    if df_customers.empty:
        st.warning("Base de clientes indisponível.")
        return

    # Controles de Ordenação e Seleção de Cliente
    col_sort, col_filter, col_select = st.columns([1.2, 1.2, 2.0])

    with col_sort:
        sort_by = st.selectbox(
            "Ordenar clientes por:",
            options=["Maior Valor em Risco", "Maior CLV Previsto", "Maior Prob. Churn", "ID do Cliente"],
            index=0,
        )

    # Ordena o DataFrame
    if sort_by == "Maior Valor em Risco":
        df_sorted = df_customers.sort_values("valor_em_risco", ascending=False)
    elif sort_by == "Maior CLV Previsto":
        df_sorted = df_customers.sort_values("clv_12m_previsto", ascending=False)
    elif sort_by == "Maior Prob. Churn":
        df_sorted = df_customers.sort_values("churn_prob", ascending=False)
    else:
        df_sorted = df_customers.sort_values("customer_id", ascending=True)

    with col_filter:
        tier_filter = st.selectbox(
            "Filtrar por Categoria:",
            options=["Todas", "azul", "topazio", "safira", "diamante", "diamante_unique"],
            index=0,
        )
        if tier_filter != "Todas":
            df_sorted = df_sorted[df_sorted["tier"] == tier_filter]

    # Vetorização de alta performance para os 50k clientes reais (0.1s)
    f_var = df_sorted["valor_em_risco"].map(format_currency_brl)
    f_churn = df_sorted["churn_prob"].map(format_percent)
    cust_options = (
        df_sorted["customer_id"] + " · " + df_sorted["tier"].str.upper() + " · VaR " + f_var + " · Churn " + f_churn
    ).tolist()

    # Recupera cliente selecionado do session_state se existir
    default_idx = 0
    if "selected_customer_id" in st.session_state:
        saved_id = st.session_state["selected_customer_id"]
        for i, opt in enumerate(cust_options):
            if opt.startswith(saved_id):
                default_idx = i
                break

    with col_select:
        selected_option = st.selectbox(
            "Selecione o Cliente para detalhamento:",
            options=cust_options,
            index=default_idx if default_idx < len(cust_options) else 0,
        )

    # Identifica o cliente escolhido
    selected_cid = selected_option.split(" · ")[0]
    st.session_state["selected_customer_id"] = selected_cid
    customer = df_customers[df_customers["customer_id"] == selected_cid].iloc[0]

    st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)

    # Header de Perfil do Cliente Selecionado
    p_info = PERSONA_TOKENS.get(customer["persona"], {"label": customer["persona"], "color": AZUL_ACTION})
    alto_valor_badge = (
        f'<span style="background: {MAGENTA_CTA}; color: #FFFFFF; font-size: 10px; font-weight: 800; padding: 3px 8px; border-radius: 4px; margin-left: 6px;">★ ALTO VALOR</span>'
        if customer["alto_valor"]
        else ""
    )

    profile_card_html = f"""
    <div style="background: {SURFACE}; border: 1px solid {BORDER_SUBTLE}; border-left: 6px solid {p_info['color']}; border-radius: {RADIUS_MD}; padding: 18px 22px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(3,55,116,0.04);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
            <div>
                <div style="font-size: 11px; font-weight: 700; color: {TEXT_SECONDARY}; text-transform: uppercase;">
                    Perfil do Cliente · ID Sintético
                </div>
                <div style="font-size: 24px; font-weight: 800; color: {AZUL_NAVY}; display: flex; align-items: center; gap: 8px;">
                    {customer['customer_id']}
                    {tier_badge(customer['tier'], show_level=True)}
                    {alto_valor_badge}
                </div>
            </div>
            <div style="text-align: right;">
                <span style="font-size: 11px; color: {TEXT_SECONDARY}; display: block;">Persona Atribuída</span>
                <span style="font-size: 15px; font-weight: 800; color: {p_info['color']};">
                    {p_info['label']}
                </span>
            </div>
        </div>
        <div style="margin-top: 14px; display: flex; flex-wrap: wrap; gap: 16px; font-size: 12px; color: {TEXT_PRIMARY}; border-top: 1px solid {BORDER_SUBTLE}; pt: 10px; padding-top: 10px;">
            <span>📍 <strong>Rota Favorita:</strong> {customer.get('rota_favorita', 'N/D')}</span>
            <span>⏱️ <strong>Última Atividade:</strong> {customer.get('recencia_dias', 0)} dias atrás</span>
            <span>✈️ <strong>Trechos 12M:</strong> {customer.get('trechos_12m', 0)}</span>
            <span>🪙 <strong>Saldo de Pontos:</strong> {format_int_br(customer.get('saldo_pontos', 0))}</span>
            <span>⚠️ <strong>Atrito Recente:</strong> <span style="background: #FFF1F2; color: #BE123C; padding: 1px 6px; border-radius: 4px; font-weight: 600;">{customer.get('atritos_dominantes', 'nenhum')}</span></span>
        </div>
    </div>
    """
    st.markdown(profile_card_html, unsafe_allow_html=True)

    # Métricas do Cliente em Destaque
    metric_row([
        {
            "title": "Valor em Risco",
            "value": format_currency_brl(customer["valor_em_risco"]),
            "subtitle": "CLV × P_churn (perda potencial)",
            "border_color": MAGENTA_CTA,
            "delta": f"{customer['churn_prob']*100:.1f}% do valor total",
            "delta_positive": False,
        },
        {
            "title": "CLV 12M Previsto",
            "value": format_currency_brl(customer["clv_12m_previsto"]),
            "subtitle": f"Gastos últimos 12m: {format_currency_brl(customer['gastos_12m_brl'])}",
            "border_color": AZUL_ACTION,
        },
        {
            "title": "Probabilidade de Evasão (Churn)",
            "value": format_percent(customer["churn_prob"]),
            "subtitle": "Horizonte: 12 meses",
            "border_color": MAGENTA_CTA if customer["churn_prob"] > 0.40 else AZUL_PRIMARY,
            "delta": "Risco Alto" if customer["churn_prob"] >= 0.50 else "Risco Moderado",
            "delta_positive": customer["churn_prob"] < 0.50,
        },
        {
            "title": "Score de Alto Valor (ScoreAV)",
            "value": f"{customer['score_av']:.2f}",
            "subtitle": "0,6·CLV + 0,2·RFM + 0,2·Potencial",
            "border_color": AZUL_DEEP,
        },
        {
            "title": "Progresso Próximo Nível",
            "value": format_percent(customer["meta_proximo_nivel_pct"]),
            "subtitle": f"{format_int_br(customer['pontos_qualificaveis_12m'])} pts qualificáveis",
            "border_color": AZUL_PRIMARY,
        },
    ])

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

    # Duas colunas: Explicabilidade SHAP vs Linha do Tempo
    col_shap, col_timeline = st.columns([1.1, 0.9])

    with col_shap:
        section_title("Explicabilidade Local SHAP (CLV)", "Contribuição dos principais fatores para o valor de vida previsto")

        shap_raw = customer.get("shap_top3")
        shap_factors: list[dict] = []
        if isinstance(shap_raw, str):
            with contextlib.suppress(Exception):
                shap_factors = json.loads(shap_raw)
        elif isinstance(shap_raw, list):
            shap_factors = shap_raw

        # Fallback para clv_shap caso não esteja na linha do cliente
        if not shap_factors:
            with contextlib.suppress(Exception):
                df_c_shap, _ = load_dataset("clv_shap")
                c_rows = df_c_shap[df_c_shap["customer_id"] == selected_cid]
                if not c_rows.empty:
                    c_row = c_rows.iloc[0]
                    for k in [1, 2, 3]:
                        f_name = c_row.get(f"top{k}_feature")
                        f_val = c_row.get(f"top{k}_shap", 0.0)
                        if pd.notna(f_name) and f_name:
                            shap_factors.append({"factor": str(f_name), "shap_value": float(f_val)})

        if shap_factors:
            factors_names = []
            shap_vals = []
            # Labels amigáveis em português alinhados ao modelo de CLV e histórico
            label_map = {
                "tier_encoded": "Nível / Categoria (Tier)",
                "avg_advance_booking_days": "Antecedência de Compra (Dias)",
                "recency_days": "Recência (Dias sem Voo)",
                "monetary_12m": "Gasto Acumulado 12M",
                "ticket_medio_12m": "Ticket Médio por Voo",
                "frequency_trend": "Tendência de Frequência de Voos",
                "pontos_qualificaveis_12m": "Pontos Qualificáveis 12M",
                "share_rotas_troncais": "Proporção de Rotas Troncais",
                "frequency_3m": "Frequência de Voos (Últimos 3M)",
                "frequency_6m": "Frequência de Voos (Últimos 6M)",
                "frequency_12m": "Frequência de Voos (12M)",
                "pontos_expirando_30d": "Pontos a Expirar em 30d",
                "days_since_last_interaction": "Dias sem Interação",
                "total_atritos_12m": "Total de Atritos (12M)",
                "atritos_atraso_12m": "Atritos por Atraso (12M)",
                "share_resgate": "Proporção de Resgate",
                "meta_proximo_nivel_pct": "Progresso Meta Próximo Tier",
                "queda_frequencia_voos": "Queda na Frequência de Voos",
                "atrito_recente_resgate": "Atrito em Resgate de Milhas",
                "recencia_inatividade": "Inatividade Prolongada (Recência)",
                "competicao_preco_rota": "Pressão Competitiva de Tarifa",
                "expiracao_proxima_pontos": "Pontos Próximos da Expiração",
                "atraso_voos_ultimos_90d": "Histórico de Atrasos Recentes",
            }

            for item in shap_factors:
                fac = item.get("factor", "outro")
                val = float(item.get("shap_value", 0.0))
                factors_names.append(label_map.get(fac, fac.replace("_", " ").title()))
                shap_vals.append(val)

            # Plota barras horizontais de impacto SHAP (suporta valores positivos e negativos)
            fig, ax = plt.subplots(figsize=(6, 3.2), facecolor=CANVAS)
            ax.set_facecolor("#FFFFFF")
            y_pos = np.arange(len(factors_names))

            bar_colors = [AZUL_ACTION if v >= 0 else MAGENTA_CTA for v in shap_vals]
            bars = ax.barh(y_pos, shap_vals, color=bar_colors, height=0.5, edgecolor=BORDER_SUBTLE)
            for bar, val in zip(bars, shap_vals, strict=False):
                txt = f"+R$ {val:,.2f}" if val >= 0 else f"-R$ {abs(val):,.2f}"
                offset = (max(shap_vals) - min(shap_vals) + 1.0) * 0.03
                ax.text(
                    val + (offset if val >= 0 else -offset),
                    bar.get_y() + bar.get_height() / 2,
                    txt,
                    va="center",
                    ha="left" if val >= 0 else "right",
                    fontsize=8,
                    fontweight="bold",
                    color=AZUL_NAVY if val >= 0 else MAGENTA_CTA,
                )

            ax.set_yticks(y_pos)
            ax.set_yticklabels(factors_names, fontsize=8.5, fontweight="bold", color=TEXT_PRIMARY)
            ax.set_xlabel("Contribuição Marginal no CLV 12M Previsto (R$)", fontsize=8.5, color=TEXT_PRIMARY, fontweight="bold")
            max_abs = max([abs(v) for v in shap_vals] + [10.0])
            margin = max_abs * 0.45
            min_lim = min(min(shap_vals) - margin, -margin) if any(v < 0 for v in shap_vals) else 0.0
            max_lim = max(shap_vals) + margin
            ax.set_xlim(min_lim, max_lim)
            if min_lim < 0:
                ax.axvline(0, color=BORDER_SUBTLE, linestyle="--", linewidth=1.2)
            ax.tick_params(colors=TEXT_SECONDARY, labelsize=8)
            for spine in ax.spines.values():
                spine.set_color(BORDER_SUBTLE)
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

            st.caption("Explicabilidade SHAP do modelo de CLV: barras em azul elevam a projeção financeira; barras em magenta reduzem a estimativa.")
        else:
            st.info("Fatores SHAP indisponíveis para este registro.")

        # Atalho para acionar o agente
        st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
        if st.button("🤖 Ver Recomendação do Agente para este Cliente →", width="stretch"):
            st.session_state["nav_goto"] = "Agente"
            st.rerun()

    with col_timeline:
        section_title("Linha do Tempo de Relacionamento", "Histórico recente de eventos, voos e manifestações")

        df_time, _ = load_timeline_data(customer_id=selected_cid)
        if not df_time.empty:
            df_time_sorted = df_time.sort_values("data", ascending=False)
            icon_map = {
                "voo": "✈️",
                "atrito": "⚠️",
                "resgate": "🪙",
                "tier_change": "🎖️",
            }

            for _, event in df_time_sorted.iterrows():
                tipo = event.get("tipo", "voo")
                icon = icon_map.get(tipo, "📌")
                color_bg = "#FFF1F2" if tipo == "atrito" else "#F0F9FF"
                color_border = MAGENTA_CTA if tipo == "atrito" else AZUL_PRIMARY

                event_html = f"""
                <div style="background: {color_bg}; border-left: 3px solid {color_border}; padding: 8px 12px; border-radius: 4px; margin-bottom: 8px; font-size: 11px;">
                    <div style="display: flex; justify-content: space-between; font-weight: 700; color: {AZUL_NAVY};">
                        <span>{icon} {event['titulo']}</span>
                        <span style="color: {TEXT_SECONDARY}; font-weight: normal;">{format_date_br(event['data'])}</span>
                    </div>
                    <div style="color: {TEXT_PRIMARY}; margin-top: 3px;">
                        {event['detalhe']}
                    </div>
                </div>
                """
                st.markdown(event_html, unsafe_allow_html=True)
        else:
            st.info(f"Sem eventos recentes registrados para o cliente {selected_cid}.")


render()
