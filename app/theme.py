"""Tokens visuais centralizados do ecossistema Azul e formatadores pt-BR.

Fonte da verdade visual:
- azul-design-patterns.md
- azul-design-reference.html
"""
from __future__ import annotations

import datetime as dt
from typing import Any

# =============================================================================
# CORES PRINCIPAIS (TOKENS EXATOS DO AZUL DESIGN REFERENCE)
# =============================================================================
AZUL_ACTION = "#0874B5"       # Botões de ação, links interativos
AZUL_PRIMARY = "#008BC4"      # Azul ciano de destaque
AZUL_SKY = "#2DA6D4"          # Azul céu iluminado
AZUL_DEEP = "#033774"         # Azul institucional escuro
AZUL_NAVY = "#0B3558"         # Navy profundo para cabeçalhos e títulos
MAGENTA_CTA = "#E832A5"       # Acento magenta/rosa (busca, preços, destaque)
LIME_CAMPAIGN = "#D8ED00"     # Amarelo-lima vivo (pontual, campanhas)
# SUPERFÍCIES E BORDAS
CANVAS = "#F8F9FA"            # Fundo geral cinza muito claro
SURFACE = "#FFFFFF"           # Fundo de cards e painéis
BORDER_SUBTLE = "#E2E6E9"     # Bordas suaves
BORDER_DARK = "#D7DEE2"       # Bordas de inputs e divisórias

# TIPOGRAFIA
TEXT_PRIMARY = "#1E2A30"      # Título e texto principal
TEXT_SECONDARY = "#5E6F7A"    # Metadados e textos de apoio (contraste >= 4.7:1 sobre branco — WCAG AA)
TEXT_MUTED = "#8A99A2"        # Rótulos discretos
TEXT_DISABLED = "#B5C0C6"     # Desabilitado
NAV_LINK_COLOR = "#4F626D"    # Links de navegação

# STATUS / FEEDBACK
SUCCESS = "#107C41"           # Verde institucional
WARNING = "#D83B01"           # Laranja alerta
INFO = "#0078D4"              # Azul informativo
NEUTRAL = "#605E5C"           # Cinza neutro

# =============================================================================
# TIERS AZUL FIDELIDADE (PROGRESSÃO CROMÁTICA OFICIAL DO REFERENCE)
# =============================================================================
TIER_TOKENS: dict[str, dict[str, str]] = {
    "azul": {
        "label": "Azul",
        "bg": "#9ae0e8",
        "text": "#0b4760",
        "badge_border": "#78d8f3",
        "level": "Base",
    },
    "topazio": {
        "label": "Topázio",
        "bg": "#39b4db",
        "text": "#073c62",
        "badge_border": "#2da6d4",
        "level": "Nível 2",
    },
    "safira": {
        "label": "Safira",
        "bg": "#147fb8",
        "text": "#FFFFFF",
        "badge_border": "#08648f",
        "level": "Nível 3",
    },
    "diamante": {
        "label": "Diamante",
        "bg": "#064c82",
        "text": "#FFFFFF",
        "badge_border": "#083e5b",
        "level": "Nível 4",
    },
    "diamante_unique": {
        "label": "Diamante Unique",
        "bg": "#062b52",
        "text": "#FFFFFF",
        "badge_border": "#032943",
        "level": "Nível 5",
        "tag": "Novo",
        "tag_bg": MAGENTA_CTA,
    },
}

# =============================================================================
# PERSONAS (CORES DE IDENTIDADE VISUAL)
# =============================================================================
PERSONA_TOKENS: dict[str, dict[str, str]] = {
    "executivo_recorrente": {
        "label": "Executivo Recorrente",
        "color": "#033774",  # Azul deep
        "bg_soft": "#EFF6FF",
        "icon": "💼",
    },
    "lazer_premium": {
        "label": "Lazer Premium",
        "color": "#E832A5",  # Magenta
        "bg_soft": "#FDF2F8",
        "icon": "🏖️",
    },
    "maximizador_milhas": {
        "label": "Maximizador de Milhas",
        "color": "#0874B5",  # Azul action
        "bg_soft": "#F0F9FF",
        "icon": "💳",
    },
    "regional_dependente": {
        "label": "Regional Dependente",
        "color": "#0B3558",  # Navy
        "bg_soft": "#F1F5F9",
        "icon": "✈️",
    },
    "eventual_ascendente": {
        "label": "Eventual Ascendente",
        "color": "#008BC4",  # Azul ciano
        "bg_soft": "#E0F2FE",
        "icon": "📈",
    },
    "eventual_promocional": {
        "label": "Eventual Promocional",
        "color": "#657681",  # Neutro
        "bg_soft": "#F8FAFC",
        "icon": "🏷️",
    },
}

# =============================================================================
# FORMA E ESPAÇAMENTO
# =============================================================================
RADIUS_SM = "4px"
RADIUS_MD = "7px"
RADIUS_PILL = "999px"

SPACE_1 = "4px"
SPACE_2 = "8px"
SPACE_3 = "12px"
SPACE_4 = "16px"
SPACE_5 = "24px"
SPACE_6 = "32px"
SPACE_7 = "48px"
SPACE_8 = "64px"

FONT_FAMILY = "Arial, Helvetica, -apple-system, sans-serif"


# =============================================================================
# FORMATADORES PT-BR
# =============================================================================
def format_currency_brl(val: Any) -> str:
    """Formata valor numérico para BRL no padrão R$ 1.234,56."""
    if val is None:
        return "R$ 0,00"
    try:
        num = float(val)
        if str(num).lower() in {"nan", "inf", "-inf"}:
            return "R$ 0,00"
    except (ValueError, TypeError):
        return "R$ 0,00"

    sign = "-" if num < 0 else ""
    abs_num = abs(num)
    formatted = f"{abs_num:,.2f}"
    # Troca separadores no formato americano para brasileiro: 1,234.56 -> 1.234,56
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{sign}R$ {formatted}"


def format_percent(val: Any, decimals: int = 1) -> str:
    """Formata fração (0.123) ou percentual (12.3) com vírgula."""
    if val is None:
        return "0,0%"
    try:
        num = float(val)
        if str(num).lower() in {"nan", "inf", "-inf"}:
            return "0,0%"
    except (ValueError, TypeError):
        return "0,0%"

    # Se for menor que 1.5 e positivo (ou entre -1.5 e 0), supomos que é taxa unitária (ex.: 0.12 = 12%)
    if -1.5 <= num <= 1.5 and num != 0.0 and abs(num) < 1.0:
        num = num * 100.0

    fmt = f"{num:.{decimals}f}".replace(".", ",")
    return f"{fmt}%"


def format_int_br(val: Any) -> str:
    """Formata número inteiro com separador de milhar pt-BR (ex.: 12.345)."""
    if val is None:
        return "0"
    try:
        num = int(round(float(val)))
    except (ValueError, TypeError):
        return "0"

    formatted = f"{abs(num):,}".replace(",", ".")
    sign = "-" if num < 0 else ""
    return f"{sign}{formatted}"


def format_date_br(val: Any, include_time: bool = False) -> str:
    """Formata data ISO ou objeto datetime para padrão DD/MM/AAAA."""
    if val is None:
        return "-"
    if isinstance(val, (dt.date, dt.datetime)):
        if include_time and isinstance(val, dt.datetime):
            return val.strftime("%d/%m/%Y %H:%M")
        return val.strftime("%d/%m/%Y")

    s = str(val).strip()
    if not s or s.lower() in {"none", "nat", "nan"}:
        return "-"
    try:
        # Tenta formatos comuns
        if "T" in s:
            parsed = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
            return parsed.strftime("%d/%m/%Y %H:%M" if include_time else "%d/%m/%Y")
        if " " in s and len(s) >= 19:
            parsed = dt.datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")
            return parsed.strftime("%d/%m/%Y %H:%M" if include_time else "%d/%m/%Y")
        if len(s) >= 10:
            parsed = dt.datetime.strptime(s[:10], "%Y-%m-%d")
            return parsed.strftime("%d/%m/%Y")
    except Exception:
        pass
    return s


# =============================================================================
# CSS GLOBAL EMBEDDED PARA STREAMLIT
# =============================================================================
def get_global_css() -> str:
    """Gera bloco CSS alinhado ao azul-design-patterns.md e azul-design-reference.html."""
    return f"""
    <style>
        /* Importante: manter tipografia sans-serif Azul */
        html, body, [class*="css"] {{
            font-family: {FONT_FAMILY};
            color: {TEXT_PRIMARY};
        }}

        /* Banner permanente de dados sintéticos
           NOTA DE DESIGN: o lime é reservado a CTAs de campanha e, por exceção
           intencional documentada (WS8a), ao banner de disclosure de dados
           sintéticos — visibilidade máxima do aviso de honestidade é mais
           importante que a regra pontual de campanha. */
        .aura-synthetic-banner {{
            background: linear-gradient(90deg, {AZUL_NAVY} 0%, {AZUL_DEEP} 100%);
            color: #FFFFFF;
            padding: 8px 18px;
            border-radius: {RADIUS_SM};
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.05em;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
            border-left: 4px solid {LIME_CAMPAIGN};
            box-shadow: 0 2px 6px rgba(11, 53, 88, 0.12);
        }}
        .aura-synthetic-banner .tag-pill {{
            background: {LIME_CAMPAIGN};
            color: {AZUL_NAVY};
            padding: 2px 8px;
            border-radius: {RADIUS_PILL};
            font-size: 10px;
            font-weight: 800;
            text-transform: uppercase;
        }}

        /* Header do Produto */
        .aura-header {{
            background: {SURFACE};
            border-bottom: 2px solid {BORDER_SUBTLE};
            padding: 14px 20px;
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-radius: {RADIUS_SM};
        }}
        .aura-logo-title {{
            font-size: 26px;
            font-weight: 900;
            color: {AZUL_NAVY};
            letter-spacing: -0.04em;
            line-height: 1;
        }}
        .aura-logo-title span {{
            color: {AZUL_ACTION};
        }}
        .aura-subtitle {{
            font-size: 12px;
            color: {TEXT_SECONDARY};
            margin-top: 4px;
        }}

        /* Assinatura de Seção: Traço Magenta 34x3px (.section-mark) */
        .aura-section-title {{
            margin-top: 18px;
            margin-bottom: 14px;
        }}
        .aura-section-title h2, .aura-section-title h3 {{
            color: {AZUL_NAVY};
            font-weight: 700;
            font-size: 18px;
            margin: 0 0 6px 0;
            padding: 0;
        }}
        .aura-section-mark {{
            width: 34px;
            height: 3px;
            background: {MAGENTA_CTA};
            border-radius: 1px;
        }}

        /* KPI Card */
        .aura-kpi-card {{
            background: {SURFACE};
            border: 1px solid {BORDER_SUBTLE};
            border-radius: {RADIUS_MD};
            padding: 16px 18px;
            box-shadow: 0 2px 8px rgba(3, 55, 116, 0.04);
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }}
        .aura-kpi-card:hover {{
            box-shadow: 0 6px 16px rgba(3, 55, 116, 0.08);
            border-color: {AZUL_PRIMARY};
        }}
        .aura-kpi-label {{
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: {TEXT_SECONDARY};
            margin-bottom: 6px;
        }}
        .aura-kpi-value {{
            font-size: 24px;
            font-weight: 800;
            color: {AZUL_NAVY};
            line-height: 1.1;
        }}
        .aura-kpi-sub {{
            font-size: 11px;
            color: {TEXT_SECONDARY};
            margin-top: 6px;
        }}
        .aura-kpi-delta {{
            font-size: 11px;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
            gap: 2px;
            padding: 2px 6px;
            border-radius: {RADIUS_SM};
            margin-top: 6px;
        }}
        .aura-kpi-delta-up {{
            color: {SUCCESS};
            background: #E8F5E9;
        }}
        .aura-kpi-delta-down {{
            color: {MAGENTA_CTA};
            background: #FDF2F8;
        }}

        /* Bloco de Citação de Regulamento */
        .aura-citation-card {{
            background: #F0F8FF;
            border-left: 4px solid {AZUL_ACTION};
            border-radius: {RADIUS_SM};
            padding: 12px 16px;
            margin: 10px 0;
            font-size: 12px;
            color: {TEXT_PRIMARY};
        }}
        .aura-citation-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 6px;
            font-weight: 700;
            color: {AZUL_NAVY};
        }}
        .aura-citation-tag {{
            background: {AZUL_ACTION};
            color: #FFFFFF;
            padding: 2px 8px;
            border-radius: {RADIUS_PILL};
            font-size: 10px;
            font-weight: 700;
        }}

        /* Persona Card */
        .aura-persona-card {{
            background: {SURFACE};
            border: 1px solid {BORDER_SUBTLE};
            border-radius: {RADIUS_MD};
            padding: 18px;
            box-shadow: 0 4px 12px rgba(3, 55, 116, 0.05);
            margin-bottom: 14px;
            position: relative;
            overflow: hidden;
        }}
        .aura-persona-strip {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
        }}

        /* Banner de Aviso de Fixture */
        .aura-fixture-warning {{
            background: #FFFBEB;
            border: 1px solid #FDE68A;
            border-left: 4px solid #F59E0B;
            border-radius: {RADIUS_SM};
            padding: 10px 14px;
            margin-bottom: 16px;
            font-size: 12px;
            color: #92400E;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        /* Botões customizados */
        div.stButton > button {{
            border-radius: {RADIUS_SM};
            font-weight: 700;
            font-size: 13px;
            transition: all 0.15s ease;
        }}
        div.stButton > button:hover {{
            border-color: {AZUL_ACTION};
            box-shadow: 0 2px 6px rgba(8, 116, 181, 0.15);
        }}

        /* Navegação Lateral Consistente com Design Reference */
        [data-testid="stSidebarNav"] a, [data-testid="stSidebar"] a {{
            color: {NAV_LINK_COLOR} !important;
            text-decoration: none !important;
            font-weight: 600 !important;
            font-size: 13px !important;
            border-radius: {RADIUS_SM} !important;
            transition: all 0.18s ease !important;
        }}
        [data-testid="stSidebarNav"] a:hover, [data-testid="stSidebar"] a:hover {{
            color: {AZUL_ACTION} !important;
            background-color: #F0F9FF !important;
        }}
        [data-testid="stSidebarNav"] a[aria-current="page"], [data-testid="stSidebar"] a[aria-current="page"] {{
            color: {AZUL_ACTION} !important;
            font-weight: 700 !important;
            border-left: 3px solid {MAGENTA_CTA} !important;
            background-color: #F8F9FA !important;
        }}
    </style>
    """
