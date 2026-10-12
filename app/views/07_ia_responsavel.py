"""Tela 07 — IA Responsável, Auditoria de Viés e Governança LGPD.

Conteúdo:
- Auditoria de viés (fairness) por atributos sensíveis (faixa etária, gênero, região)
- Métricas: taxas de seleção de alto valor, risco previsto médio, razão vs limiar 0,8 (Four-Fifths Rule)
- Gráficos comparativos de disparidade
- Declaração formal de integridade metodológica e dados 100% sintéticos
- Transparência de citações e rastreabilidade do regulamento versionado
- Seção de conformidade com a LGPD e mecanismo Humano no Circuito (Art. 20)
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from app.components import (
    citation_block,
    metric_row,
    render_fixture_banner,
    render_synthetic_banner,
    section_title,
)
from app.loader import load_fairness_data
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
    format_percent,
)


def render() -> None:
    render_synthetic_banner()

    df_fairness, is_fixture = load_fairness_data()
    render_fixture_banner(is_fixture)

    section_title(
        "IA Responsável: Auditoria de Equidade, Rastreabilidade e LGPD",
        "Monitoramento de impacto desproporcional (fairness), mitigação de viés algorítmico e salvaguardas humanas.",
    )

    # 1. DECLARAÇÃO FORMAL DE DADOS SINTÉTICOS E LGPD
    st.markdown(
        f"""
        <div style="background: {SURFACE}; border: 1px solid {BORDER_SUBTLE}; border-left: 5px solid {AZUL_ACTION}; border-radius: {RADIUS_MD}; padding: 16px 20px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(3,55,116,0.04);">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                <span style="font-size: 16px;">🛡️</span>
                <strong style="color: {AZUL_NAVY}; font-size: 14px;">DECLARAÇÃO DE PRIVACIDADE E DADOS SINTÉTICOS (LGPD)</strong>
            </div>
            <p style="margin: 0; font-size: 12.5px; color: {TEXT_PRIMARY}; line-height: 1.5;">
                O Projeto Aura 2.0 opera exclusivamente sobre uma <strong>base de dados sintética</strong> calibrada a partir de agregados públicos da ANAC e premissas de domínio da aviação civil.
                Nenhum dado pessoal identificável de clientes da Azul (como CPF, nome civil, telefone real ou dados financeiros) foi utilizado ou ingerido.
                Os atributos sensíveis (gênero, faixa etária e região) existem exclusivamente para <strong>auditoria de conformidade</strong> e são categoricamente <strong>excluídos das features de treinamento dos modelos</strong> preditivos.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df_fairness.empty:
        st.warning("Métricas de fairness indisponíveis na base.")
        return

    # Cálculos resumidos
    total_grupos = len(df_fairness)
    grupos_conformes = int(df_fairness["four_fifths_compliant"].sum())
    taxa_conformidade = grupos_conformes / max(1, total_grupos)

    metric_row([
        {
            "title": "Conformidade Four-Fifths (4/5)",
            "value": f"{grupos_conformes} / {total_grupos} grupos",
            "subtitle": "Razão de seleção >= 0,80 vs grupo base",
            "border_color": AZUL_ACTION,
            "delta": f"{taxa_conformidade*100:.1f}% em conformidade",
            "delta_positive": taxa_conformidade >= 0.8,
        },
        {
            "title": "Limiar Regulatório de Disparidade",
            "value": "0,80 (80%)",
            "subtitle": "Diretriz Four-Fifths Rule / EEOC",
            "border_color": AZUL_DEEP,
        },
        {
            "title": "Atributos Sensíveis Auditados",
            "value": "3 dimensões",
            "subtitle": "Faixa Etária, Gênero e Região Geográfica",
            "border_color": AZUL_PRIMARY,
        },
        {
            "title": "Humano no Circuito (HITL)",
            "value": "Artigo 20 LGPD",
            "subtitle": "Revisão e edição de recomendações ativa",
            "border_color": MAGENTA_CTA,
        },
    ])

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

    # 2. AUDITORIA DE VIÉS POR ATRIBUTO SENSÍVEL
    section_title("Métricas de Disparidade por Grupo Protegido", "Auditoria de taxa de seleção de Alto Valor e risco de churn predito")

    col_filter_dim, _ = st.columns([1.5, 2.5])
    with col_filter_dim:
        selected_dim = st.selectbox(
            "Selecionar dimensão demográfica para inspeção:",
            options=["faixa_etaria", "genero", "regiao"],
            format_func=lambda d: {"faixa_etaria": "Faixa Etária", "genero": "Gênero", "regiao": "Região Geográfica"}.get(d, d),
        )

    sub_dim = df_fairness[df_fairness["sensitive_attribute"] == selected_dim].copy()

    col_chart_fair, col_table_fair = st.columns([1.1, 0.9])

    with col_chart_fair:
        fig, ax = plt.subplots(figsize=(6, 3.4), facecolor=CANVAS)
        ax.set_facecolor("#FFFFFF")

        groups = sub_dim["group_value"].values
        ratios = sub_dim["selection_ratio_vs_max"].values
        x_pos = np.arange(len(groups))

        bar_colors = [AZUL_ACTION if r >= 0.80 else MAGENTA_CTA for r in ratios]
        bars = ax.bar(x_pos, ratios, color=bar_colors, width=0.45, edgecolor=BORDER_SUBTLE)

        # Linha de corte 0.80
        ax.axhline(0.80, color=WARNING, linestyle="--", linewidth=1.5, label="Limiar Four-Fifths (0,80)")

        for bar, r in zip(bars, ratios, strict=False):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                r + 0.02,
                f"{r:.2f}",
                ha="center",
                va="bottom",
                fontsize=8.5,
                fontweight="bold",
                color=AZUL_NAVY,
            )

        ax.set_xticks(x_pos)
        ax.set_xticklabels(groups, fontsize=8.5, fontweight="bold", color=TEXT_PRIMARY)
        ax.set_ylabel("Razão de Seleção vs Grupo Máximo", fontsize=8.5, color=TEXT_PRIMARY)
        ax.set_ylim(0, 1.25)
        ax.tick_params(colors=TEXT_SECONDARY, labelsize=8)
        ax.legend(loc="upper right", frameon=True, facecolor="#FFFFFF", edgecolor=BORDER_SUBTLE, fontsize=8)
        for spine in ax.spines.values():
            spine.set_color(BORDER_SUBTLE)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    with col_table_fair:
        display_sub = sub_dim[[
            "group_value", "group_size", "selection_rate", "avg_predicted_churn", "selection_ratio_vs_max", "four_fifths_compliant"
        ]].copy()
        display_sub.columns = ["Grupo", "Amostra", "Taxa Alto Valor", "Churn Médio", "Razão vs Max", "Conforme?"]
        display_sub["Taxa Alto Valor"] = display_sub["Taxa Alto Valor"].apply(lambda v: format_percent(v))
        display_sub["Churn Médio"] = display_sub["Churn Médio"].apply(lambda v: format_percent(v))
        display_sub["Razão vs Max"] = display_sub["Razão vs Max"].apply(lambda v: f"{v:.2f}")
        display_sub["Conforme?"] = display_sub["Conforme?"].apply(lambda v: "✅ Sim" if v else "⚠️ Atenção")
        st.dataframe(display_sub, width="stretch", hide_index=True)

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

    # 3. TRANSPARÊNCIA DE CITAÇÕES E RAG VERSIONADO
    section_title("Transparência Regulatória e RAG Versionado", "Base de conhecimento oficial e verificabilidade de cada promessa do agente")

    st.markdown(
        f"""
        <p style="font-size: 12px; color: {TEXT_SECONDARY}; margin-bottom: 12px;">
            Para prevenir alucinações e ofertas inválidas, o agente de retenção consome exclusivamente um snapshot congelado das regras do Azul Fidelidade.
            Cada benefício ofertado requer um <code>fact_id</code> verificado que acompanha a mensagem final.
        </p>
        """,
        unsafe_allow_html=True,
    )

    col_rag1, col_rag2 = st.columns(2)
    with col_rag1:
        citation_block(
            fact_id="AF-TIER-SAFIRA",
            verification_status="official_current_verified",
            valid_from="2024-04-01",
            source="Regulamento Azul Fidelidade Cláusula 4.3",
            quote="Clientes Safira possuem franquia de 1 bagagem despachada gratuita em voos domésticos e 2 acessos ao Lounge Azul.",
        )
    with col_rag2:
        citation_block(
            fact_id="AF-RESGATE-ESPECIAL-2025",
            verification_status="official_current_partial",
            valid_from="2025-01-01",
            source="Resgate Especial Azul — Tabela Fixa de Pontos",
            quote="Passagens emitidas sob tabela de resgate especial possuem pontuação fixa por trecho para clientes Diamante e Safira elegíveis.",
        )

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

    # 4. SALVAGUARDAS LGPD E HUMANO NO CIRCUITO (ARTIGO 20)
    section_title("Mecanismo Humano no Circuito (Art. 20 LGPD)", "Salvaguarda contra decisões e comunicações automatizadas sem intervenção humana")

    st.markdown(
        f"""
        <div style="background: #F8FAFC; border: 1px solid {BORDER_SUBTLE}; border-radius: {RADIUS_MD}; padding: 16px 20px; font-size: 12px; color: {TEXT_PRIMARY};">
            <h4 style="margin: 0 0 8px 0; color: {AZUL_NAVY}; font-size: 13.5px;">Garantias da Arquitetura Aura 2.0:</h4>
            <ul style="margin: 0; padding-left: 18px; line-height: 1.6;">
                <li><strong>Revisão Humana Ativa:</strong> Casos de risco crítico ou com elevado valor em risco recebem automaticamente a flag <code>human_review = True</code>, impedindo disparos automáticos sem consentimento prévio.</li>
                <li><strong>Trilhas de Auditoria Imutáveis:</strong> Todas as aprovações, edições e rejeições de mensagens são registradas em formato estruturado (<code>decisions.jsonl</code>) com carimbo de data/hora ISO-8601 e identificador do operador.</li>
                <li><strong>Direito à Explicação:</strong> A decomposição SHAP fornece aos operadores e clientes a justificativa clara e em linguagem natural sobre quais fatores operacionais fundamentaram a abordagem.</li>
                <li><strong>Minimização e Finalidade:</strong> O modelo processa exclusivamente métricas operacionais agregadas (voos, pontuação e atritos), sem ingerir dados comportamentais invasivos de redes sociais ou históricos externos.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


render()
