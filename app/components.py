"""Componentes reutilizáveis de interface no padrão visual do Azul Design System.

Tokens e regras:
- Traço magenta de 34x3px (.section-mark) em títulos de seção
- Badges de tier com progressão cromática oficial (#9ae0e8 -> #062b52)
- KPI cards com tipografia e contraste adequados
- Blocos de citação de regulamento com fact_id, verificação, vigência e fonte
- Banners de integridade e honestidade visual (Sintético e Fixtures)
"""
from __future__ import annotations

import html
from typing import Any

import pandas as pd
import streamlit as st

from app.theme import (
    AZUL_ACTION,
    AZUL_NAVY,
    AZUL_PRIMARY,
    BORDER_SUBTLE,
    MAGENTA_CTA,
    RADIUS_MD,
    RADIUS_PILL,
    RADIUS_SM,
    SURFACE,
    TEXT_SECONDARY,
    TIER_TOKENS,
)


def render_synthetic_banner() -> None:
    """Banner obrigatório e permanente em todas as telas informando dados sintéticos."""
    html_code = """
    <div class="aura-synthetic-banner" role="alert" aria-label="Aviso de base sintética">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 14px;">⚠️</span>
            <span><strong>DADOS SINTÉTICOS — DEMONSTRAÇÃO</strong> · Pipeline reproduzível Aura 2.0 (Azul Fidelidade)</span>
        </div>
        <span class="tag-pill">Ambiente Seguro / LGPD</span>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)


def render_fixture_banner(is_fixture: bool = True) -> None:
    """Aviso explícito e honesto quando a visualização consome dados de fixture."""
    if not is_fixture:
        return
    html_code = """
    <div class="aura-fixture-warning" role="status">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 14px;">📦</span>
            <span><strong>FIXTURE ATIVA:</strong> Visualizando dados pré-computados de demonstração. Para gerar com a base analítica completa, execute <code>python tasks.py all</code>.</span>
        </div>
        <span style="font-size: 10px; font-weight: 800; background: #FDE68A; padding: 2px 6px; border-radius: 4px;">DEMO OFFLINE</span>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)


def render_header(current_screen_name: str | None = None) -> None:
    """Cabeçalho visual do produto com identidade Azul."""
    screen_label = f" · <em>{html.escape(current_screen_name)}</em>" if current_screen_name else ""
    html_code = f"""
    <header class="aura-header" role="banner">
        <div>
            <div class="aura-logo-title">
                Azul <span>Aura 2.0</span>
            </div>
            <div class="aura-subtitle">
                Inteligência de Retenção e Cuidado · Azul Fidelidade{screen_label}
            </div>
        </div>
        <div style="text-align: right; font-size: 11px; color: {TEXT_SECONDARY};">
            <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #107C41; margin-right: 4px;"></span>
            <strong>Status do Pipeline:</strong> Operacional
        </div>
    </header>
    """
    st.markdown(html_code, unsafe_allow_html=True)


def section_title(title: str, subtitle: str | None = None) -> None:
    """Título de seção com a assinatura visual do Azul Design System: traço magenta 34x3px."""
    sub_html = f'<p style="margin: 4px 0 0 0; font-size: 12px; color: {TEXT_SECONDARY};">{html.escape(subtitle)}</p>' if subtitle else ""
    html_code = f"""
    <div class="aura-section-title">
        <h2 style="color: {AZUL_NAVY}; font-size: 18px; font-weight: 700; margin: 0;">{html.escape(title)}</h2>
        <div class="aura-section-mark"></div>
        {sub_html}
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)


def kpi_card(
    title: str,
    value: str,
    subtitle: str | None = None,
    delta: str | None = None,
    delta_positive: bool = True,
    border_color: str | None = None,
) -> None:
    """Card de métrica individual com padrão visual institucional."""
    border_style = f"border-top: 3px solid {border_color};" if border_color else f"border-top: 3px solid {AZUL_PRIMARY};"
    sub_html = f'<div class="aura-kpi-sub">{html.escape(subtitle)}</div>' if subtitle else ""

    delta_html = ""
    if delta:
        delta_class = "aura-kpi-delta-up" if delta_positive else "aura-kpi-delta-down"
        arrow = "↑" if delta_positive else "↓"
        delta_html = f'<div class="aura-kpi-delta {delta_class}">{arrow} {html.escape(delta)}</div>'

    html_code = f"""
    <div class="aura-kpi-card" style="{border_style}">
        <div>
            <div class="aura-kpi-label">{html.escape(title)}</div>
            <div class="aura-kpi-value">{html.escape(value)}</div>
        </div>
        <div>
            {delta_html}
            {sub_html}
        </div>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)


def metric_row(metrics: list[dict[str, Any]]) -> None:
    """Renderiza uma linha de 2 a 5 KPI cards lado a lado usando st.columns."""
    n = len(metrics)
    if n == 0:
        return
    cols = st.columns(n)
    for col, m in zip(cols, metrics, strict=False):
        with col:
            kpi_card(
                title=m.get("title", ""),
                value=m.get("value", ""),
                subtitle=m.get("subtitle"),
                delta=m.get("delta"),
                delta_positive=m.get("delta_positive", True),
                border_color=m.get("border_color"),
            )


def tier_badge(tier_key: str, show_level: bool = False) -> str:
    """Retorna o HTML do badge de tier com a cor exata correspondente."""
    tk = str(tier_key).strip().lower().replace(" ", "_")
    token = TIER_TOKENS.get(tk, TIER_TOKENS["azul"])

    bg = token["bg"]
    text = token["text"]
    label = token["label"]
    tag = token.get("tag")

    tag_html = ""
    if tag:
        tag_html = f'<span style="background: {MAGENTA_CTA}; color: #FFFFFF; font-size: 8px; font-weight: 800; padding: 1px 4px; border-radius: {RADIUS_PILL}; margin-left: 4px; text-transform: uppercase;">{html.escape(tag)}</span>'

    level_html = f' <span style="font-size: 9px; opacity: 0.85;">({html.escape(token["level"])})</span>' if show_level else ""

    return (
        f'<span style="background: {bg}; color: {text}; font-size: 11px; font-weight: 700; '
        f'padding: 3px 8px; border-radius: {RADIUS_SM}; display: inline-flex; align-items: center; gap: 2px; '
        f'border: 1px solid rgba(0,0,0,0.08); vertical-align: middle;">'
        f'✧ {html.escape(label)}{level_html}{tag_html}'
        f'</span>'
    )


def citation_block(
    fact_id: str,
    verification_status: str,
    valid_from: str | None = None,
    source: str | None = None,
    quote: str | None = None,
) -> None:
    """Exibe um bloco formal de citação do regulamento com metadados de auditoria."""
    status_label = {
        "official_current_verified": "Oficial Verificado",
        "official_current_partial": "Oficial Parcial",
        "verified": "Verificado",
        "premise": "Premissa Declarada",
    }.get(verification_status, verification_status)

    status_color = "#107C41" if "verif" in verification_status else "#B45309"

    quote_html = f'<div style="margin-top: 8px; font-style: italic; background: #FFFFFF; padding: 8px; border-radius: 4px; border: 1px solid {BORDER_SUBTLE};">"{html.escape(quote)}"</div>' if quote else ""
    source_html = f" · Fonte: <strong>{html.escape(source)}</strong>" if source else ""
    valid_html = f" · Vigência: <strong>{html.escape(str(valid_from))}</strong>" if valid_from else ""

    html_code = f"""
    <div class="aura-citation-card">
        <div class="aura-citation-header">
            <span>📋 Citação: <code>{html.escape(fact_id)}</code></span>
            <span style="color: {status_color}; font-size: 11px; font-weight: 700;">● {html.escape(status_label)}</span>
        </div>
        <div style="font-size: 11px; color: {TEXT_SECONDARY};">
            {valid_html}{source_html}
        </div>
        {quote_html}
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)


def empty_state_card(message: str, action_suggestion: str | None = None) -> None:
    """Card informativo quando um filtro ou tabela não retorna registros."""
    sug_html = f'<p style="margin-top: 6px; font-size: 11px; color: {AZUL_ACTION}; font-weight: 600;">👉 {html.escape(action_suggestion)}</p>' if action_suggestion else ""
    html_code = f"""
    <div style="background: {SURFACE}; border: 1px dashed {BORDER_SUBTLE}; border-radius: {RADIUS_MD}; padding: 24px; text-align: center; margin: 16px 0;">
        <span style="font-size: 28px; display: block; margin-bottom: 8px;">🔍</span>
        <h4 style="margin: 0; color: {AZUL_NAVY}; font-size: 14px; font-weight: 700;">Nenhum dado encontrado</h4>
        <p style="margin: 4px 0 0 0; font-size: 12px; color: {TEXT_SECONDARY};">{html.escape(message)}</p>
        {sug_html}
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)


def styled_dataframe(df: pd.DataFrame, height: int | None = None) -> None:
    """Exibe um DataFrame do pandas com formatação e apresentação limpa."""
    if df.empty:
        empty_state_card("Tabela vazia sem registros a exibir.")
        return
    st.dataframe(df, width="stretch", height=height)
