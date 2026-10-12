"""Ponto de entrada do aplicativo Streamlit — Aura 2.0 (Azul Fidelidade).

Design e Navegação:
- Tema visual oficial Azul (tokens: azul-action, navy, magenta, lime, canvas)
- Navegação fluida via st.navigation e st.Page (7 telas)
- Banner permanente "DADOS SINTÉTICOS — demonstração" em todas as telas
- Header institucional do produto
- Suporte a modo offline com fallback declarativo de fixtures
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.theme import (
    AZUL_ACTION,
    AZUL_NAVY,
    LIME_CAMPAIGN,
    TEXT_SECONDARY,
    get_global_css,
)

# Configuração da página precisa ser a primeira chamada Streamlit
st.set_page_config(
    page_title="Aura 2.0 — Azul Fidelidade",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Injeta tokens CSS globais
st.markdown(get_global_css(), unsafe_allow_html=True)

# Definição das 7 páginas via caminhos de arquivo (padrão nativo do st.Page).
# Nota de robustez: o st.Page do Streamlit (>=1.30) resolve caminhos relativos
# contra o DIRETÓRIO DO SCRIPT DE ENTRADA (main_script_parent), não contra o
# CWD — logo "app/views/..." dobraria para "app/app/views/..." e levantaria
# StreamlitPageNotFoundError. Caminhos absolutos são parte do contrato público
# do st.Page e funcionam de qualquer diretório de lançamento.
_VIEWS = Path(__file__).resolve().parent / "views"

pages = [
    st.Page(str(_VIEWS / "01_carteira.py"), title="01 · Visão da Carteira", icon="📊", url_path="carteira", default=True),
    st.Page(str(_VIEWS / "02_personas.py"), title="02 · Personas", icon="👥", url_path="personas"),
    st.Page(str(_VIEWS / "03_cliente_360.py"), title="03 · Cliente 360", icon="🔍", url_path="cliente-360"),
    st.Page(str(_VIEWS / "04_agente.py"), title="04 · Agente de Retenção", icon="🤖", url_path="agente"),
    st.Page(str(_VIEWS / "05_atritos.py"), title="05 · Mapa de Atritos", icon="⚠️", url_path="atritos"),
    st.Page(str(_VIEWS / "06_simulador.py"), title="06 · Simulador de Impacto", icon="📈", url_path="simulador"),
    st.Page(str(_VIEWS / "07_ia_responsavel.py"), title="07 · IA Responsável", icon="🛡️", url_path="ia-responsavel"),
]

# Sidebar Institucional
with st.sidebar:
    st.markdown(
        f"""
        <div style="padding: 10px 0 16px 0; border-bottom: 2px solid #E2E6E9; margin-bottom: 14px;">
            <div style="font-size: 24px; font-weight: 900; color: {AZUL_NAVY}; letter-spacing: -0.04em; line-height: 1;">
                Azul <span style="color: {AZUL_ACTION}; font-weight: 800;">Aura 2.0</span>
            </div>
            <div style="font-size: 11px; color: {TEXT_SECONDARY}; margin-top: 4px; font-weight: 600;">
                Retenção e Fidelidade · Da Milha ao Cuidado
            </div>
            <div style="margin-top: 8px;">
                <span style="background: {LIME_CAMPAIGN}; color: {AZUL_NAVY}; font-size: 9.5px; font-weight: 800; padding: 2px 6px; border-radius: 4px; text-transform: uppercase;">
                    Base 100% Sintética
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Inicializa navegação nativa do Streamlit
pg = st.navigation(pages)

# Rodapé da Sidebar
with st.sidebar:
    st.markdown(
        f"""
        <div style="margin-top: 30px; padding-top: 14px; border-top: 1px solid #E2E6E9; font-size: 10px; color: {TEXT_SECONDARY}; line-height: 1.5;">
            <p style="margin: 0 0 6px 0;"><strong>Aura 2.0 MVP</strong></p>
            <p style="margin: 0 0 6px 0;">Calibrado com microdados públicos ANAC e regras Azul Fidelidade.</p>
            <p style="margin: 0; color: {AZUL_ACTION}; font-weight: 700;"><code>python tasks.py all</code></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Executa página ativa
pg.run()
