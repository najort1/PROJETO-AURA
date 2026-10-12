"""Tela 04 — Agente de Recomendação, Redação e Auditoria.

Conteúdo:
- Recomendação do agente para o cliente selecionado (ação, canal, confiança)
- Mensagem redigida em português brasileiro com suporte do regulamento
- Citações formais do regulamento (fact_id, status de verificação, vigência, fonte)
- Justificativa ponta a ponta (SHAP + atritos + regras de elegibilidade)
- Flag de revisão humana visível quando aplicável
- Botões FUNCIONAIS "Aprovar" e "Editar" com persistência em decisions.jsonl e session_state
- Histórico auditável de decisões tomadas nesta sessão
"""
from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from app.components import (
    citation_block,
    render_fixture_banner,
    render_synthetic_banner,
    section_title,
    tier_badge,
)
from app.loader import (
    get_recorded_decisions,
    load_customers_data,
    load_recommendations_data,
    record_decision,
)
from app.theme import (
    AZUL_ACTION,
    AZUL_NAVY,
    BORDER_SUBTLE,
    RADIUS_MD,
    SURFACE,
    TEXT_PRIMARY,
    WARNING,
    format_currency_brl,
    format_date_br,
    format_percent,
)


def render() -> None:
    render_synthetic_banner()

    df_customers, is_c_fixture = load_customers_data()
    df_recs, is_r_fixture = load_recommendations_data()
    render_fixture_banner(is_c_fixture or is_r_fixture)

    section_title(
        "Agente Especialista: Recomendação, Redação e Elegibilidade",
        "Próxima Melhor Ação (Next Best Action) ancorada no regulamento Azul Fidelidade com explicabilidade e humano no circuito.",
    )

    if df_recs.empty or df_customers.empty:
        st.warning("Recomendações indisponíveis na base.")
        return

    # Seletor do cliente
    cids_with_recs = sorted(df_recs["customer_id"].unique())

    # Verifica se há cliente já ativo no session_state
    current_cid = st.session_state.get("selected_customer_id", cids_with_recs[0])
    if current_cid not in cids_with_recs:
        current_cid = cids_with_recs[0]

    selected_cid = st.selectbox(
        "Selecione o Cliente para avaliar recomendação:",
        options=cids_with_recs,
        index=cids_with_recs.index(current_cid),
        help="Alterne entre clientes para verificar as diferentes ações e justificativas do agente.",
    )
    st.session_state["selected_customer_id"] = selected_cid

    # Dados do cliente e recomendação
    cust_row = df_customers[df_customers["customer_id"] == selected_cid].iloc[0]
    rec_row = df_recs[df_recs["customer_id"] == selected_cid].iloc[0]

    st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)

    # Flag de Revisão Humana
    needs_review = bool(rec_row.get("human_review", False))
    if needs_review:
        st.markdown(
            f"""
            <div style="background: #FEF3C7; border: 1px solid #F59E0B; border-left: 5px solid {WARNING}; border-radius: {RADIUS_MD}; padding: 12px 16px; margin-bottom: 16px; font-size: 12px;">
                <strong style="color: #92400E; font-size: 13px;">⚠️ FLAG DE REVISÃO HUMANA ATIVA (Human-in-the-Loop)</strong><br>
                <span style="color: #78350F;">
                    Este cliente possui valor elevado e risco crítico ou regras de borda. O envio automático foi bloqueado; a validação ou ajuste por um operador é mandatória antes do despacho.
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Informações da Ação em Cartão
    channel_icons = {"whatsapp": "📱 WhatsApp", "email": "📧 E-mail", "app": "🔔 Notificação App", "telefone": "📞 Telefone"}
    canal_fmt = channel_icons.get(rec_row["channel"], rec_row["channel"].capitalize())

    action_header_html = f"""
    <div style="background: {SURFACE}; border: 1px solid {BORDER_SUBTLE}; border-radius: {RADIUS_MD}; padding: 16px 20px; margin-bottom: 18px; box-shadow: 0 2px 8px rgba(3,55,116,0.04);">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px;">
            <div>
                <span style="font-size: 10px; font-weight: 800; text-transform: uppercase; color: {AZUL_ACTION}; letter-spacing: 0.05em;">
                    Ação Selecionada pelo Playbook
                </span>
                <h3 style="margin: 2px 0 0 0; font-size: 18px; font-weight: 800; color: {AZUL_NAVY};">
                    {rec_row['action_id']} · {rec_row['action_name'].replace('_', ' ').title()}
                </h3>
            </div>
            <div style="text-align: right;">
                <span style="background: #F0F9FF; color: {AZUL_ACTION}; border: 1px solid {AZUL_ACTION}44; font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 4px;">
                    Confiança do Agente: {format_percent(rec_row['confidence'])}
                </span>
            </div>
        </div>
        <div style="margin-top: 12px; display: flex; flex-wrap: wrap; gap: 14px; font-size: 12px; color: {TEXT_PRIMARY}; border-top: 1px solid {BORDER_SUBTLE}; padding-top: 8px;">
            <span>Canal Indicado: <strong>{canal_fmt}</strong></span>
            <span>Categoria: {tier_badge(cust_row['tier'])}</span>
            <span>Valor em Risco: <strong>{format_currency_brl(cust_row['valor_em_risco'])}</strong></span>
            <span>Modo do Agente: <code>{rec_row.get('mode', 'offline')}</code></span>
            <span>Snapshot de Regras: <code>{rec_row.get('snapshot_version', 'v1')}</code></span>
        </div>
    </div>
    """
    st.markdown(action_header_html, unsafe_allow_html=True)

    # Mensagem Redigida e Ações (Aprovar / Editar)
    section_title("Mensagem Redigida pelo Agente", "Comunicação personalizada pronta para envio ou edição supervisionada")

    edit_mode_key = f"edit_mode_{selected_cid}"
    if edit_mode_key not in st.session_state:
        st.session_state[edit_mode_key] = False

    msg_state_key = f"msg_content_{selected_cid}"
    if msg_state_key not in st.session_state:
        st.session_state[msg_state_key] = rec_row["message"]

    # Se estiver em modo de edição
    if st.session_state[edit_mode_key]:
        st.info("✏️ Modo de edição ativado. Ajuste o texto abaixo e clique em 'Salvar e Aprovar'.")
        edited_text = st.text_area(
            "Mensagem a ser enviada:",
            value=st.session_state[msg_state_key],
            height=130,
            key=f"text_area_{selected_cid}",
        )
        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            if st.button("💾 Salvar Alterações e Aprovar", type="primary", use_container_width=True):
                st.session_state[msg_state_key] = edited_text
                st.session_state[edit_mode_key] = False
                record_decision(
                    customer_id=selected_cid,
                    action_id=rec_row["action_id"],
                    action_name=rec_row["action_name"],
                    status="edited",
                    original_message=rec_row["message"],
                    final_message=edited_text,
                    notes="Mensagem ajustada manualmente pelo operador no painel.",
                )
                st.success("✅ Mensagem editada e aprovada com sucesso! Registro persistido em decisions.jsonl.")
                st.rerun()
        with col_btn2:
            if st.button("Cancelar Edição", use_container_width=True):
                st.session_state[edit_mode_key] = False
                st.rerun()
    else:
        # Exibe mensagem formatada em balão de visualização
        msg_display = st.session_state[msg_state_key]
        message_box_html = f"""
        <div style="background: #F8FAFC; border: 1px solid #CBD5E1; border-left: 4px solid {AZUL_ACTION}; border-radius: {RADIUS_MD}; padding: 18px 20px; font-size: 13.5px; line-height: 1.55; color: {TEXT_PRIMARY}; margin-bottom: 14px;">
            {msg_display}
        </div>
        """
        st.markdown(message_box_html, unsafe_allow_html=True)

        col_act1, col_act2, col_act3 = st.columns([1.2, 1.2, 2.0])
        with col_act1:
            if st.button("✅ Aprovar Envio", type="primary", use_container_width=True):
                record_decision(
                    customer_id=selected_cid,
                    action_id=rec_row["action_id"],
                    action_name=rec_row["action_name"],
                    status="approved",
                    original_message=rec_row["message"],
                    final_message=msg_display,
                    notes="Aprovação direta sem alterações no texto.",
                )
                st.success(f"✅ Recomendação para o cliente {selected_cid} aprovada com sucesso e gravada em data/analytics/decisions.jsonl!")
        with col_act2:
            if st.button("✏️ Editar Mensagem", use_container_width=True):
                st.session_state[edit_mode_key] = True
                st.rerun()

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

    # Justificativa e Citações em duas colunas
    col_just, col_cit = st.columns([1.1, 0.9])

    with col_just:
        section_title("Justificativa Ponta a Ponta", "Racional auditável: SHAP + atritos dominantes + regras determinísticas")

        just_raw = rec_row.get("justification_json", "{}")
        try:
            just_dict = json.loads(just_raw) if isinstance(just_raw, str) else just_raw
        except Exception:
            just_dict = {}

        atritos_list = just_dict.get("atritos_dominantes", [])
        regras_list = just_dict.get("regras", [])

        st.markdown(
            f"""
            <div style="background: {SURFACE}; border: 1px solid {BORDER_SUBTLE}; border-radius: {RADIUS_MD}; padding: 14px 18px; font-size: 12px; color: {TEXT_PRIMARY};">
                <p style="margin: 0 0 10px 0;"><strong>Por que este cliente foi selecionado?</strong><br>
                Apresenta Valor em Risco de <strong>{format_currency_brl(cust_row['valor_em_risco'])}</strong> (CLV de {format_currency_brl(cust_row['clv_12m_previsto'])} com probabilidade de churn de {format_percent(cust_row['churn_prob'])}).
                </p>
                <p style="margin: 0 0 10px 0;"><strong>Principais sinais de atrito e insatisfação:</strong><br>
                {", ".join(atritos_list) if atritos_list else "Sem atrito crítico catalogado"}
                </p>
                <p style="margin: 0;"><strong>Regras determinísticas de elegibilidade atendidas:</strong><br>
                {", ".join([f"<code>{r}</code>" for r in regras_list]) if regras_list else "Regras padrão de categoria"}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_cit:
        section_title("Citações Formais do Regulamento", "Base de conhecimento auditável que sustenta a oferta")

        cit_raw = rec_row.get("citations_json", "[]")
        try:
            citations_list = json.loads(cit_raw) if isinstance(cit_raw, str) else cit_raw
        except Exception as e:
            st.warning(f"Campo citations_json inválido para este cliente (não será exibida citação): {e}")
            citations_list = []

        if citations_list:
            for cit in citations_list:
                citation_block(
                    fact_id=cit.get("fact_id", "AF-REG-GENERIC"),
                    verification_status=cit.get("verification_status", "official_current_verified"),
                    valid_from=cit.get("valid_from", "2024-04-01"),
                    source=cit.get("source", "Regulamento Azul Fidelidade"),
                    quote=cit.get("quote"),
                )
        else:
            # Estado honesto: NUNCA inventar citação. Recomendações elegíveis sempre
            # carregam citações do pipeline; ausência aqui indica anomalia ou
            # ACT-NO-ACTION (sem oferta), e deve ser sinalizada ao operador.
            st.warning(
                "⚠️ Esta recomendação não possui citação formal do regulamento registrada "
                "no pipeline. Nenhuma citação será exibida (o sistema jamais fabrica lastro "
                "regulatório). Se a ação for elegível, investigue a execução de "
                "`python tasks.py agent-precompute` antes de despachar qualquer mensagem."
            )

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

    # Histórico de Decisões Registradas
    section_title("Histórico Auditável de Decisões", "Decisões do operador humano persistidas em decisions.jsonl")

    decisions = get_recorded_decisions()
    if decisions:
        dec_df = pd.DataFrame(decisions)
        display_dec = dec_df[["timestamp", "customer_id", "action_id", "status", "edited"]].copy()
        display_dec["timestamp"] = display_dec["timestamp"].apply(lambda v: format_date_br(v, include_time=True))
        display_dec.columns = ["Data / Hora", "Cliente", "Ação", "Status", "Houve Edição?"]
        st.dataframe(display_dec.tail(10), use_container_width=True, hide_index=True)
    else:
        st.caption("Nenhuma decisão registrada nesta sessão ainda. Utilize os botões acima para aprovar ou editar mensagens.")


render()
