"""Tela 01 — Visão da Carteira (Portfolio Overview).

Conteúdo:
- KPIs centrais: Valor em Risco Total (Σ CLV × P_churn), CLV Total, Nº Clientes, % Alto Valor, Custo Médio Ação
- Histograma de distribuição de CLV
- Curva de Pareto / Lorenz da receita com coeficiente de Gini
- Valor em Risco por persona / segmento (gráfico de barras)
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
from app.loader import load_customers_data, load_personas_data
from app.theme import (
    AZUL_ACTION,
    AZUL_DEEP,
    AZUL_NAVY,
    AZUL_PRIMARY,
    BORDER_SUBTLE,
    CANVAS,
    MAGENTA_CTA,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    format_currency_brl,
    format_int_br,
    format_percent,
)


def render() -> None:
    render_synthetic_banner()

    df_customers, is_fixture = load_customers_data()
    df_personas, _ = load_personas_data()
    render_fixture_banner(is_fixture)

    section_title(
        "Visão Geral da Carteira e Valor em Risco",
        "Panorama agregado dos clientes sintéticos do Azul Fidelidade, concentração de receita e exposição à evasão.",
    )

    if df_customers.empty:
        st.warning("Nenhum cliente disponível na base.")
        return

    # Cálculos derivados dos dados carregados (nunca hardcode)
    n_clientes = len(df_customers)
    clv_total = float(df_customers["clv_12m_previsto"].sum())
    # Valor em Risco total = Σ(clv_12m_previsto × churn_prob) sobre a carteira real
    valor_em_risco_total = float(
        (df_customers["clv_12m_previsto"] * df_customers["churn_prob"]).sum()
    )
    pct_alto_valor = float(df_customers["alto_valor"].mean())
    custo_medio_acao = 45.0  # PREMISSA (não derivada dos dados): custo médio por ação de
    # retenção do playbook (média ponderada de gestos/contatos/ofertas). Premissa de negócio
    # documentada no relatório de limitações (docs/limitations.md); ajustar quando houver
    # custo real unitário por ação homologado. Nunca apresentar como valor observado.

    # Linha de KPIs
    metric_row(
        [
            {
                "title": "Valor em Risco Total",
                "value": format_currency_brl(valor_em_risco_total),
                "subtitle": "Σ (CLV × P_churn) em risco de perda",
                "border_color": MAGENTA_CTA,
                "delta": f"{format_percent(valor_em_risco_total / max(1.0, clv_total))} do CLV",
                "delta_positive": False,
            },
            {
                "title": "CLV 12M Total Previsto",
                "value": format_currency_brl(clv_total),
                "subtitle": f"Média: {format_currency_brl(clv_total / n_clientes)}/cliente",
                "border_color": AZUL_ACTION,
            },
            {
                "title": "Tamanho da Carteira",
                "value": format_int_br(n_clientes),
                "subtitle": "Clientes na coorte de análise",
                "border_color": AZUL_DEEP,
            },
            {
                "title": "Segmento Alto Valor",
                "value": format_percent(pct_alto_valor),
                "subtitle": f"{format_int_br(df_customers['alto_valor'].sum())} clientes prioritários",
                "border_color": AZUL_PRIMARY,
            },
            {
                "title": "Custo Médio da Ação",
                "value": format_currency_brl(custo_medio_acao),
                "subtitle": "Playbook de retenção ponderado",
                "border_color": AZUL_NAVY,
            },
        ]
    )

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

    # Gráficos em duas colunas
    col_left, col_right = st.columns(2)

    with col_left:
        section_title(
            "Distribuição do CLV 12M Previsto", "Densidade de valor futuro dos membros do programa"
        )
        fig, ax = plt.subplots(figsize=(6, 3.8), facecolor=CANVAS)
        ax.set_facecolor("#FFFFFF")
        clv_vals = df_customers["clv_12m_previsto"].values
        p95 = np.percentile(clv_vals, 95)

        n, bins, patches = ax.hist(
            clv_vals,
            bins=25,
            color=AZUL_PRIMARY,
            edgecolor=BORDER_SUBTLE,
            alpha=0.9,
        )
        # Destaca o percentil de alto valor em magenta
        for patch, b in zip(patches, bins, strict=False):
            if b >= p95:
                patch.set_facecolor(MAGENTA_CTA)

        ax.axvline(
            float(np.mean(clv_vals)),
            color=AZUL_DEEP,
            linestyle="--",
            linewidth=1.5,
            label=f"Média: {format_currency_brl(np.mean(clv_vals))}",
        )
        ax.axvline(
            float(np.median(clv_vals)),
            color=AZUL_ACTION,
            linestyle=":",
            linewidth=1.5,
            label=f"Mediana: {format_currency_brl(np.median(clv_vals))}",
        )

        ax.set_xlabel("CLV 12M Previsto (R$)", fontsize=9, color=TEXT_PRIMARY, fontweight="bold")
        ax.set_ylabel("Frequência de Clientes", fontsize=9, color=TEXT_PRIMARY)
        ax.tick_params(colors=TEXT_SECONDARY, labelsize=8)
        ax.legend(frameon=True, facecolor="#FFFFFF", edgecolor=BORDER_SUBTLE, fontsize=8)
        for spine in ax.spines.values():
            spine.set_color(BORDER_SUBTLE)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    with col_right:
        section_title(
            "Curva de Concentração (Lorenz / Pareto)",
            "Distribuição acumulada de receita vs clientes (Gini)",
        )
        # Curva de Lorenz
        sorted_clv = np.sort(clv_vals)
        cum_clv = np.cumsum(sorted_clv) / np.sum(sorted_clv)
        cum_pop = np.arange(1, len(sorted_clv) + 1) / len(sorted_clv)

        # Gini (compatível com NumPy 1.x e 2.x)
        trap_fn = getattr(np, "trapezoid", getattr(np, "trapz", None))
        gini = 1.0 - 2.0 * float(trap_fn(cum_clv, cum_pop))

        fig, ax = plt.subplots(figsize=(6, 3.8), facecolor=CANVAS)
        ax.set_facecolor("#FFFFFF")
        ax.plot(
            cum_pop,
            cum_clv,
            color=AZUL_ACTION,
            linewidth=2.5,
            label=f"Curva de Lorenz (Gini = {gini:.2f})",
        )
        ax.plot(
            [0, 1],
            [0, 1],
            color=TEXT_SECONDARY,
            linestyle="--",
            linewidth=1.2,
            label="Distribuição Igualitária",
        )

        # Ponto 80/20
        idx_80 = int(len(sorted_clv) * 0.8)
        top_20_share = 1.0 - cum_clv[idx_80]
        ax.scatter([0.8], [cum_clv[idx_80]], color=MAGENTA_CTA, s=60, zorder=5)
        ax.annotate(
            f"Top 20% detém {top_20_share * 100:.1f}% do CLV",
            xy=(0.8, cum_clv[idx_80]),
            xytext=(0.35, 0.55),
            arrowprops=dict(
                facecolor=MAGENTA_CTA, edgecolor=MAGENTA_CTA, shrink=0.08, width=1, headwidth=6
            ),
            fontsize=8,
            fontweight="bold",
            color=AZUL_NAVY,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFFFFF", edgecolor=BORDER_SUBTLE),
        )

        ax.set_xlabel(
            "Fração Acumulada da População", fontsize=9, color=TEXT_PRIMARY, fontweight="bold"
        )
        ax.set_ylabel("Fração Acumulada do CLV", fontsize=9, color=TEXT_PRIMARY)
        ax.tick_params(colors=TEXT_SECONDARY, labelsize=8)
        ax.legend(
            loc="upper left", frameon=True, facecolor="#FFFFFF", edgecolor=BORDER_SUBTLE, fontsize=8
        )
        for spine in ax.spines.values():
            spine.set_color(BORDER_SUBTLE)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)

    # Gráfico inferior: Valor em Risco por Persona / Segmento
    section_title(
        "Valor em Risco e CLV por Persona", "Exposição financeira agrupada por arquétipo de cliente"
    )

    var_by_persona = (
        df_customers.groupby("persona")
        .agg(
            valor_em_risco=("valor_em_risco", "sum"),
            clv_total=("clv_12m_previsto", "sum"),
            clientes=("customer_id", "count"),
            churn_medio=("churn_prob", "mean"),
        )
        .reset_index()
    )
    var_by_persona = var_by_persona.sort_values("valor_em_risco", ascending=True)

    # Mapeia nomes amigáveis
    persona_names_map = {
        "executivo_recorrente": "Executivo Recorrente",
        "lazer_premium": "Lazer Premium",
        "maximizador_milhas": "Maximizador de Milhas",
        "regional_dependente": "Regional Dependente",
        "eventual_ascendente": "Eventual Ascendente",
        "eventual_promocional": "Eventual Promocional",
    }
    var_by_persona["persona_label"] = (
        var_by_persona["persona"].map(persona_names_map).fillna(var_by_persona["persona"])
    )

    fig, ax = plt.subplots(figsize=(10, 3.8), facecolor=CANVAS)
    ax.set_facecolor("#FFFFFF")

    y_pos = np.arange(len(var_by_persona))
    bars = ax.barh(
        y_pos,
        var_by_persona["valor_em_risco"],
        color=AZUL_ACTION,
        height=0.6,
        edgecolor=BORDER_SUBTLE,
    )

    # Destaca maior risco em magenta
    max_idx = int(np.argmax(var_by_persona["valor_em_risco"].values))
    bars[max_idx].set_facecolor(MAGENTA_CTA)

    for i, bar in enumerate(bars):
        w = bar.get_width()
        cnt = var_by_persona["clientes"].iloc[i]
        ch = var_by_persona["churn_medio"].iloc[i]
        ax.text(
            w + (var_by_persona["valor_em_risco"].max() * 0.01),
            bar.get_y() + bar.get_height() / 2,
            f"{format_currency_brl(w)} ({cnt} clientes · P_churn {ch * 100:.1f}%)",
            va="center",
            ha="left",
            fontsize=8,
            fontweight="bold",
            color=AZUL_NAVY,
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(
        var_by_persona["persona_label"], fontsize=9, fontweight="bold", color=TEXT_PRIMARY
    )
    ax.set_xlabel("Valor em Risco Total (R$)", fontsize=9, color=TEXT_PRIMARY, fontweight="bold")
    ax.set_xlim(0, var_by_persona["valor_em_risco"].max() * 1.35)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(BORDER_SUBTLE)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


render()
