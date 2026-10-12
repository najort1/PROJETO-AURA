"""Tela 05 — Mapa de Atritos e Sentimento por Aspecto.

Conteúdo:
- Mapa de sentimento: aspectos × intensidade (barras) × tendência temporal (linhas por semestre)
- Identificação dos pontos de fricção dominantes no programa de fidelidade
- Exemplos de comentários do corpus
- NOTA OBRIGATÓRIA de que o corpus é 100% sintético para respeito a termos de uso
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from app.components import (
    metric_row,
    render_fixture_banner,
    render_synthetic_banner,
    section_title,
)
from app.loader import load_friction_data
from app.theme import (
    AZUL_ACTION,
    AZUL_DEEP,
    AZUL_NAVY,
    AZUL_PRIMARY,
    BORDER_SUBTLE,
    CANVAS,
    MAGENTA_CTA,
    RADIUS_MD,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    format_int_br,
    format_percent,
)


def render() -> None:
    render_synthetic_banner()

    df_friction, is_fixture = load_friction_data()
    render_fixture_banner(is_fixture)

    section_title(
        "Mapa de Atritos e Inteligência de Sentimento por Aspecto",
        "Detecção de fricções nas experiências do cliente (voos, resgates, canais) que alimentam o motor de retenção.",
    )

    # Nota explícita e obrigatória sobre corpus sintético
    st.markdown(
        f"""
        <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-left: 4px solid {AZUL_PRIMARY}; border-radius: {RADIUS_MD}; padding: 12px 16px; margin-bottom: 20px; font-size: 12px; color: {AZUL_NAVY};">
            <strong>ℹ️ DECLARAÇÃO METODOLÓGICA — CORPUS SINTÉTICO (LGPD / TERMOS DE USO):</strong><br>
            As avaliações e menções analisadas foram geradas sinteticamente com calibração semântica e rotulagem por aspecto em PT-BR.
            Nenhum dado pessoal, perfil ou avaliação extraída sem autorização de plataformas terceiras é armazenado neste repositório.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df_friction.empty:
        st.warning("Dados do mapa de atritos indisponíveis.")
        return

    # Cálculos agregados
    total_mencoes = int(df_friction["mention_count"].sum())
    total_negativas = int(df_friction["negative_count"].sum())
    taxa_negativa_global = float(total_negativas / max(1, total_mencoes))

    # Identifica aspecto mais crítico no semestre mais recente
    recent_sem = df_friction["semester"].max()
    sub_recent = df_friction[df_friction["semester"] == recent_sem]
    pior_aspecto_row = sub_recent.sort_values("negative_rate", ascending=False).iloc[0]
    pior_aspecto_nome = pior_aspecto_row["aspect"].replace("_", " ").title()

    metric_row([
        {
            "title": "Total de Menções Analisadas",
            "value": format_int_br(total_mencoes),
            "subtitle": f"Janela temporal de {df_friction['semester'].nunique()} semestres",
            "border_color": AZUL_ACTION,
        },
        {
            "title": "Taxa Global de Negatividade",
            "value": format_percent(taxa_negativa_global),
            "subtitle": f"{format_int_br(total_negativas)} menções negativas",
            "border_color": MAGENTA_CTA,
            "delta": "Indicador de Atrito",
            "delta_positive": False,
        },
        {
            "title": "Atrito Mais Crítico Recente",
            "value": pior_aspecto_nome,
            "subtitle": f"{format_percent(pior_aspecto_row['negative_rate'])} taxa negativa ({recent_sem})",
            "border_color": MAGENTA_CTA,
        },
        {
            "title": "Aspectos Monitorados",
            "value": str(df_friction["aspect"].nunique()),
            "subtitle": "Atraso, bagagem, resgate, app, preço...",
            "border_color": AZUL_DEEP,
        },
    ])

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

    # Gráficos em duas colunas: Intensidade vs Tendência Temporal
    col_bar, col_trend = st.columns([1.0, 1.0])

    aspect_label_map = {
        "atraso": "Atraso de Voo",
        "bagagem": "Bagagem / Extravio",
        "atendimento": "Atendimento",
        "app_checkin": "App & Check-in",
        "resgate_milhas": "Resgate de Milhas",
        "preco": "Preço & Tarifas",
        "conforto": "Conforto a Bordo",
    }

    with col_bar:
        section_title("Intensidade por Aspecto (Semestre Recente)", f"Volume de menções e proporção de insatisfação ({recent_sem})")

        sub_recent_sorted = sub_recent.sort_values("negative_rate", ascending=True)
        aspect_labels = [aspect_label_map.get(a, a) for a in sub_recent_sorted["aspect"]]
        neg_rates = sub_recent_sorted["negative_rate"].values

        fig, ax = plt.subplots(figsize=(6, 3.8), facecolor=CANVAS)
        ax.set_facecolor("#FFFFFF")

        y_pos = np.arange(len(aspect_labels))
        bars = ax.barh(y_pos, neg_rates, color=AZUL_ACTION, height=0.55, edgecolor=BORDER_SUBTLE)

        # Destaca o pior em magenta
        bars[-1].set_facecolor(MAGENTA_CTA)

        for bar, val, cnt in zip(bars, neg_rates, sub_recent_sorted["mention_count"], strict=False):
            ax.text(
                val + 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"{val*100:.1f}% ({cnt} menções)",
                va="center",
                ha="left",
                fontsize=8,
                fontweight="bold",
                color=AZUL_NAVY,
            )

        ax.set_yticks(y_pos)
        ax.set_yticklabels(aspect_labels, fontsize=8.5, fontweight="bold", color=TEXT_PRIMARY)
        ax.set_xlabel("Taxa de Menções Negativas", fontsize=8.5, color=TEXT_PRIMARY, fontweight="bold")
        ax.set_xlim(0, 1.15)
        ax.tick_params(colors=TEXT_SECONDARY, labelsize=8)
        for spine in ax.spines.values():
            spine.set_color(BORDER_SUBTLE)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    with col_trend:
        section_title("Tendência Temporal por Semestre", "Evolução da taxa de insatisfação por aspecto ao longo do tempo")

        fig, ax = plt.subplots(figsize=(6, 3.8), facecolor=CANVAS)
        ax.set_facecolor("#FFFFFF")

        colors_palette = [AZUL_DEEP, MAGENTA_CTA, AZUL_ACTION, "#D97706", "#2563EB", "#059669", "#7C3AED"]

        for i, asp in enumerate(df_friction["aspect"].unique()):
            sub_asp = df_friction[df_friction["aspect"] == asp].sort_values("semester")
            asp_name = aspect_label_map.get(asp, asp)
            color = colors_palette[i % len(colors_palette)]
            linewidth = 2.4 if asp in ["resgate_milhas", "atraso"] else 1.3
            linestyle = "-" if asp in ["resgate_milhas", "atraso"] else "--"

            ax.plot(
                sub_asp["semester"],
                sub_asp["negative_rate"],
                marker="o",
                markersize=4,
                linewidth=linewidth,
                linestyle=linestyle,
                label=asp_name,
                color=color,
            )

        ax.set_xlabel("Semestre", fontsize=8.5, color=TEXT_PRIMARY, fontweight="bold")
        ax.set_ylabel("Taxa Negativa", fontsize=8.5, color=TEXT_PRIMARY)
        ax.set_ylim(0.2, 1.0)
        ax.tick_params(colors=TEXT_SECONDARY, labelsize=8)
        ax.legend(loc="upper right", frameon=True, facecolor="#FFFFFF", edgecolor=BORDER_SUBTLE, fontsize=7.5, ncol=2)
        for spine in ax.spines.values():
            spine.set_color(BORDER_SUBTLE)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

    # Tabela de Pesos dos Aspectos (friction_map.parquet - 49 linhas: 7 aspectos x 7 semestres)
    section_title("Pesos dos Aspectos no Modelo de Atrito", "Importância calibrada de cada aspecto no índice de insatisfação do cliente")

    df_weights = (
        df_friction.groupby("aspect")
        .agg(
            aspect_weight=("aspect_weight", "first"),
            total_mencoes=("mention_count", "sum"),
            taxa_neg_media=("negative_rate", "mean"),
        )
        .reset_index()
        .sort_values("aspect_weight", ascending=False)
    )

    df_weights["aspect_label"] = df_weights["aspect"].map(aspect_label_map).fillna(df_weights["aspect"])
    display_weights = df_weights[["aspect_label", "aspect_weight", "total_mencoes", "taxa_neg_media"]].copy()
    display_weights.columns = ["Aspecto de Experiência", "Peso no Modelo", "Menções Acumuladas", "Taxa Negativa Média"]
    display_weights["Peso no Modelo"] = display_weights["Peso no Modelo"].apply(lambda v: f"{v:.4f} ({v*100:.2f}%)")
    display_weights["Menções Acumuladas"] = display_weights["Menções Acumuladas"].apply(format_int_br)
    display_weights["Taxa Negativa Média"] = display_weights["Taxa Negativa Média"].apply(format_percent)

    st.dataframe(display_weights, width="stretch", hide_index=True)

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

    # Exemplos Sintéticos do Corpus
    section_title("Exemplos do Corpus Sintético Rotulado", "Amostra qualitativa dos atritos identificados e classificados por aspecto")

    sample_reviews = [
        {
            "Aspecto": "Resgate de Milhas",
            "Polaridade": "Negativa",
            "Comentário Sintético": "Tentei emitir uma passagem usando meus pontos para o feriado e os valores em pontos estavam absurdos, mais que o dobro do ano passado.",
            "Impacto no Pipeline": "Aciona ação de Resgate Especial com cotas de tabela fixa.",
        },
        {
            "Aspecto": "Atraso de Voo",
            "Polaridade": "Negativa",
            "Comentário Sintético": "Voo de Campinas para Brasília atrasou 2 horas sem comunicação prévia no portão de embarque.",
            "Impacto no Pipeline": "Gera prioridade de contato proativo no canal executivo.",
        },
        {
            "Aspecto": "App & Check-in",
            "Polaridade": "Negativa",
            "Comentário Sintético": "O aplicativo deu erro na hora de selecionar os assentos da família e tive que resolver no balcão.",
            "Impacto no Pipeline": "Registra atrito digital para clientes de categoria inicial/intermediária.",
        },
        {
            "Aspecto": "Atendimento",
            "Polaridade": "Positiva",
            "Comentário Sintético": "A tripulação e o atendimento em terra foram excelentes, muito atenciosos com meu filho.",
            "Impacto no Pipeline": "Equilibra o score de satisfação para clientes fidelizados.",
        },
    ]

    st.dataframe(pd.DataFrame(sample_reviews), width="stretch", hide_index=True)


render()
