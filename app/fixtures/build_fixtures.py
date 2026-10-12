"""Gerador de fixtures sintéticas representativas e calibradas para o modo demonstração/offline do Aura 2.0.

Gera conjuntos Parquet em `app/fixtures/` com seed fixa (42):
- customers_scores.parquet
- personas_summary.parquet
- customer_timeline.parquet
- agent_recommendations.parquet
- friction_map.parquet
- fairness_metrics.parquet
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd

FIXTURES_DIR = Path(__file__).resolve().parent


def build_all_fixtures(target_dir: Path | None = None, seed: int = 42) -> dict[str, pd.DataFrame]:
    """Constrói todos os DataFrames de fixture e salva como Parquet."""
    out_dir = target_dir or FIXTURES_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    np.random.seed(seed)

    # 1. PERSONAS DEFINITIONS
    personas_def = [
        {
            "persona": "executivo_recorrente",
            "nome_display": "Executivo Recorrente",
            "cor": "#033774",
            "share_pct": 0.22,
            "clv_medio_base": 8500.0,
            "churn_base": 0.38,
            "atritos_dominantes": "atraso, atendimento",
            "acao_recomendada": "Contato Proativo de Relacionamento (ACT-CONTATO)",
            "descricao": "Alta frequência corporativa em rotas troncais (VCP, SDU, BSB, CGH). Valoriza pontualidade e flexibilidade.",
            "rotas": ["VCP-SDU", "VCP-BSB", "CGH-CNF", "VCP-POA", "CGH-CWB"],
        },
        {
            "persona": "lazer_premium",
            "nome_display": "Lazer Premium",
            "cor": "#E832A5",
            "share_pct": 0.18,
            "clv_medio_base": 9200.0,
            "churn_base": 0.29,
            "atritos_dominantes": "preco, bagagem",
            "acao_recomendada": "Oferta Rota Favorita com Bônus (ACT-OFERTA-ROTA)",
            "descricao": "Viagens de férias em família ou casais, alta antecedência, ticket médio alto em destinos turísticos e internacionais.",
            "rotas": ["VCP-REC", "VCP-MCO", "CNF-SSA", "VCP-NAT", "VCP-FOR"],
        },
        {
            "persona": "maximizador_milhas",
            "nome_display": "Maximizador de Milhas",
            "cor": "#0874B5",
            "share_pct": 0.25,
            "clv_medio_base": 6100.0,
            "churn_base": 0.45,
            "atritos_dominantes": "resgate_milhas, app_checkin",
            "acao_recomendada": "Oferta Resgate Especial Azul (ACT-RESGATE-ESPECIAL)",
            "descricao": "Acúmulo massivo via cartões co-branded e parceiros. Muito sensível a disponibilidade e precificação de resgate.",
            "rotas": ["VCP-SDU", "CGH-SDU", "CNF-VCP", "VCP-SSA", "VCP-REC"],
        },
        {
            "persona": "regional_dependente",
            "nome_display": "Regional Dependente",
            "cor": "#0B3558",
            "share_pct": 0.15,
            "clv_medio_base": 5800.0,
            "churn_base": 0.22,
            "atritos_dominantes": "conforto, cancelamento",
            "acao_recomendada": "Garantia de Conectividade e Prioridade (ACT-CONTATO)",
            "descricao": "Voa rotas conectando cidades do interior sem concorrentes diretos (ATR e E-Jets). Valoriza regularidade da malha.",
            "rotas": ["VCP-MGF", "CNF-IPN", "VCP-RAO", "CWB-CAC", "POA-PET"],
        },
        {
            "persona": "eventual_ascendente",
            "nome_display": "Eventual Ascendente",
            "cor": "#008BC4",
            "share_pct": 0.12,
            "clv_medio_base": 3900.0,
            "churn_base": 0.35,
            "atritos_dominantes": "app_checkin, preco",
            "acao_recomendada": "Antecipação de Nível Assistida (ACT-ANTECIPACAO-NIVEL)",
            "descricao": "Clientes em rápida progressão de voos e pontos, próximos de saltar para Safira ou Diamante.",
            "rotas": ["VCP-BSB", "CNF-CGH", "VCP-CWB", "SDU-CNF", "VCP-FLN"],
        },
        {
            "persona": "eventual_promocional",
            "nome_display": "Eventual Promocional",
            "cor": "#657681",
            "share_pct": 0.08,
            "clv_medio_base": 1800.0,
            "churn_base": 0.58,
            "atritos_dominantes": "preco",
            "acao_recomendada": "Campanha Promocional Tarifa / Pontos (ACT-BONUS-PONTOS)",
            "descricao": "Sensíveis exclusivamente a preço em campanhas sazonais; baixa frequência e engajamento esporádico.",
            "rotas": ["VCP-SSA", "CGH-FLN", "CNF-VIX", "VCP-AJU", "VCP-MCZ"],
        },
    ]

    # 2. GENERATE CUSTOMERS
    n_customers = 600
    customer_ids = [f"C{i:06d}" for i in range(1, n_customers + 1)]

    tiers_pool = ["azul", "topazio", "safira", "diamante", "diamante_unique"]

    personas_keys = [p["persona"] for p in personas_def]
    personas_weights = [p["share_pct"] for p in personas_def]

    faixas_etarias = ["18-29", "30-49", "50-64", "65+"]
    faixas_probs = [0.18, 0.52, 0.22, 0.08]
    generos = ["Feminino", "Masculino"]
    generos_probs = [0.46, 0.54]
    regioes = ["Sudeste", "Sul", "Nordeste", "Centro-Oeste", "Norte"]
    regioes_probs = [0.55, 0.18, 0.15, 0.08, 0.04]

    p_map = {p["persona"]: p for p in personas_def}

    rows = []
    for cid in customer_ids:
        persona_key = np.random.choice(personas_keys, p=personas_weights)
        p_info = p_map[persona_key]

        # Tier proporcional à persona
        if persona_key == "executivo_recorrente":
            tier_weights = [0.05, 0.15, 0.40, 0.32, 0.08]
        elif persona_key == "lazer_premium":
            tier_weights = [0.10, 0.25, 0.35, 0.25, 0.05]
        elif persona_key == "maximizador_milhas":
            tier_weights = [0.15, 0.30, 0.35, 0.18, 0.02]
        elif persona_key == "eventual_ascendente":
            tier_weights = [0.10, 0.60, 0.25, 0.05, 0.00]
        else:
            tier_weights = [0.60, 0.30, 0.08, 0.02, 0.00]

        tier = np.random.choice(tiers_pool, p=tier_weights)

        # CLV 12m
        clv_base = p_info["clv_medio_base"] * np.random.lognormal(0.0, 0.35)
        # Bônus por tier
        tier_mult = {"azul": 0.6, "topazio": 0.9, "safira": 1.3, "diamante": 1.9, "diamante_unique": 2.8}
        clv_12m = round(float(clv_base * tier_mult[tier]), 2)

        # Churn Prob (0.05 a 0.95)
        churn_base = p_info["churn_base"] + np.random.normal(0.0, 0.12)
        churn_prob = float(np.clip(churn_base, 0.04, 0.92))

        # Valor em Risco = CLV * Churn
        valor_em_risco = round(clv_12m * churn_prob, 2)

        # Recência e frequência
        recencia_dias = int(np.random.exponential(35) + 5)
        trechos_12m = max(1, int(np.random.poisson(14 if persona_key == "executivo_recorrente" else 6)))
        frequencia_voos = trechos_12m

        # Gastos 12m
        gastos_12m = round(clv_12m * float(np.random.uniform(0.7, 1.1)), 2)

        # Saldo de pontos
        saldo_base = {"azul": 5000, "topazio": 18000, "safira": 45000, "diamante": 110000, "diamante_unique": 260000}[tier]
        saldo_pontos = int(saldo_base * np.random.uniform(0.5, 2.2))
        pontos_expirando_30d = int(saldo_pontos * np.random.choice([0.0, 0.05, 0.15, 0.25], p=[0.5, 0.3, 0.15, 0.05]))
        pontos_qualificaveis = int(gastos_12m * 1.5 + np.random.randint(500, 3000))
        meta_proximo_pct = float(np.clip(np.random.beta(3, 2), 0.15, 1.25))

        # ScoreAV: 0.6*pct(CLV) + 0.2*pct(RFM) + 0.2*pct(Potencial) - calculado preliminarmente
        score_av = float(np.clip(clv_12m / 18000.0 * 0.7 + (1.0 - recencia_dias / 180.0) * 0.3, 0.05, 0.99))
        alto_valor = bool(score_av >= 0.70 or clv_12m >= 8000.0)

        # Risk state
        if churn_prob >= 0.50 and alto_valor:
            risk_state = "risco_alto_valor_alto"
        elif churn_prob >= 0.40 and alto_valor:
            risk_state = "risco_medio_valor_alto"
        elif churn_prob < 0.40 and alto_valor:
            risk_state = "risco_baixo_potencial_alto"
        else:
            risk_state = "risco_baixo_estavel"

        # Demografia e contexto
        faixa_etaria = np.random.choice(faixas_etarias, p=faixas_probs)
        genero = np.random.choice(generos, p=generos_probs)
        regiao = np.random.choice(regioes, p=regioes_probs)
        rota_favorita = np.random.choice(p_info["rotas"])
        atritos = p_info["atritos_dominantes"].split(", ")[0]

        # SHAP top 3 fatores de risco
        shap_factors_pool = [
            ("queda_frequencia_voos", round(float(np.random.uniform(0.12, 0.32)), 3)),
            ("atrito_recente_resgate", round(float(np.random.uniform(0.08, 0.22)), 3)),
            ("recencia_inatividade", round(float(np.random.uniform(0.06, 0.18)), 3)),
            ("competicao_preco_rota", round(float(np.random.uniform(0.04, 0.15)), 3)),
            ("expiracao_proxima_pontos", round(float(np.random.uniform(0.03, 0.12)), 3)),
            ("atraso_voos_ultimos_90d", round(float(np.random.uniform(0.05, 0.20)), 3)),
        ]
        np.random.shuffle(shap_factors_pool)
        shap_top3 = json.dumps([{"factor": f[0], "shap_value": f[1]} for f in shap_factors_pool[:3]])

        beneficio_nao_utilizado = np.random.choice(
            ["espaco_azul", "bagagem_adicional", "embarque_prioritario", "sala_vip", "upgrade_voo", None],
            p=[0.25, 0.25, 0.20, 0.15, 0.10, 0.05],
        )

        rows.append(
            {
                "customer_id": cid,
                "tier": tier,
                "persona": persona_key,
                "clv_12m_previsto": clv_12m,
                "churn_prob": churn_prob,
                "valor_em_risco": valor_em_risco,
                "score_av": score_av,
                "alto_valor": alto_valor,
                "risk_state": risk_state,
                "gastos_12m_brl": gastos_12m,
                "recencia_dias": recencia_dias,
                "frequencia_voos": frequencia_voos,
                "trechos_12m": trechos_12m,
                "saldo_pontos": saldo_pontos,
                "pontos_expirando_30d": pontos_expirando_30d,
                "pontos_qualificaveis_12m": pontos_qualificaveis,
                "meta_proximo_nivel_pct": meta_proximo_pct,
                "faixa_etaria": faixa_etaria,
                "genero": genero,
                "regiao": regiao,
                "rota_favorita": rota_favorita,
                "atritos_dominantes": atritos,
                "beneficio_nao_utilizado": beneficio_nao_utilizado,
                "shap_top3": shap_top3,
            }
        )

    df_customers = pd.DataFrame(rows)
    # Recalcula ScoreAV real percentilar:
    pct_clv = df_customers["clv_12m_previsto"].rank(pct=True)
    pct_rfm = (df_customers["frequencia_voos"].rank(pct=True) + (1.0 - df_customers["recencia_dias"].rank(pct=True))) / 2.0
    pct_pot = df_customers["meta_proximo_nivel_pct"].rank(pct=True)
    df_customers["score_av"] = (0.60 * pct_clv + 0.20 * pct_rfm + 0.20 * pct_pot).round(4)
    df_customers["alto_valor"] = df_customers["score_av"] >= df_customers["score_av"].quantile(0.85)

    df_customers.to_parquet(out_dir / "customers_scores.parquet", index=False)

    # 2. PERSONAS SUMMARY
    personas_summary_rows = []
    for p in personas_def:
        sub = df_customers[df_customers["persona"] == p["persona"]]
        cnt = len(sub)
        personas_summary_rows.append(
            {
                "persona": p["persona"],
                "nome_display": p["nome_display"],
                "cor": p["cor"],
                "clientes_count": cnt,
                "share_pct": round(cnt / n_customers, 3),
                "clv_medio": round(float(sub["clv_12m_previsto"].mean()), 2) if cnt > 0 else p["clv_medio_base"],
                "churn_medio": round(float(sub["churn_prob"].mean()), 3) if cnt > 0 else p["churn_base"],
                "valor_em_risco_total": round(float(sub["valor_em_risco"].sum()), 2),
                "atritos_dominantes": p["atritos_dominantes"],
                "acao_recomendada": p["acao_recomendada"],
                "descricao": p["descricao"],
                "ticket_medio": round(float(sub["gastos_12m_brl"].mean() / np.maximum(1, sub["frequencia_voos"].mean())), 2) if cnt > 0 else 650.0,
            }
        )
    df_personas_summary = pd.DataFrame(personas_summary_rows)
    df_personas_summary.to_parquet(out_dir / "personas_summary.parquet", index=False)

    # 3. TIMELINE EVENTS FOR CUSTOMERS
    timeline_rows = []
    base_date = dt.date(2026, 8, 31)

    for cid in customer_ids[:100]:  # Timeline rica para clientes analisados
        sub_c = df_customers[df_customers["customer_id"] == cid].iloc[0]
        # Evento 1: Voo recente
        d1 = base_date - dt.timedelta(days=int(sub_c["recencia_dias"]))
        timeline_rows.append(
            {
                "customer_id": cid,
                "data": d1.isoformat(),
                "tipo": "voo",
                "titulo": f"Voo {sub_c['rota_favorita']}",
                "detalhe": f"Trecho operado pontualmente em classe { 'Executiva' if sub_c['tier'] in ['diamante', 'diamante_unique'] else 'Econômica' }",
                "impacto": "positivo",
            }
        )
        # Evento 2: Atrito ou contato
        d2 = d1 - dt.timedelta(days=int(np.random.randint(15, 60)))
        atrito_tipo = sub_c["atritos_dominantes"]
        timeline_rows.append(
            {
                "customer_id": cid,
                "data": d2.isoformat(),
                "tipo": "atrito",
                "titulo": f"Atrito registrado: {atrito_tipo.capitalize()}",
                "detalhe": f"Manifestação do cliente via canal digital relacionada a {atrito_tipo}.",
                "impacto": "negativo",
            }
        )
        # Evento 3: Resgate ou pontos
        d3 = d2 - dt.timedelta(days=int(np.random.randint(20, 80)))
        timeline_rows.append(
            {
                "customer_id": cid,
                "data": d3.isoformat(),
                "tipo": "resgate",
                "titulo": "Resgate de Pontos Azul",
                "detalhe": "Emissão de bilhete prêmio para parceiro / rota doméstica.",
                "impacto": "neutro",
            }
        )
        # Evento 4: Atualização de tier
        d4 = d3 - dt.timedelta(days=int(np.random.randint(40, 150)))
        timeline_rows.append(
            {
                "customer_id": cid,
                "data": d4.isoformat(),
                "tipo": "tier_change",
                "titulo": f"Qualificação Categoria {sub_c['tier'].replace('_', ' ').title()}",
                "detalhe": f"Atingimento de meta anual em pontos qualificáveis ({sub_c['pontos_qualificaveis_12m']} pts).",
                "impacto": "positivo",
            }
        )

    df_timeline = pd.DataFrame(timeline_rows)
    df_timeline.to_parquet(out_dir / "customer_timeline.parquet", index=False)

    # 4. AGENT RECOMMENDATIONS (conforming to schemas/recommendations.yaml)
    recs_rows = []
    actions_map = {
        "executivo_recorrente": {
            "id": "ACT-CONTATO",
            "name": "contato_proativo_relacionamento",
            "channel": "whatsapp",
            "msg_template": "Olá! Notamos que seus últimos voos na rota {rota} apresentaram atrasos pontuais. Como cliente {tier_fmt}, valorizamos profundamente sua pontualidade e queremos oferecer suporte exclusivo da nossa equipe executiva.",
            "fact_id": "AF-ATENDIMENTO-PRIORITARIO",
            "fact_verif": "official_current_verified",
            "valid_from": "2024-04-01",
            "source": "Regulamento Azul Fidelidade Cláusula 9.1",
        },
        "lazer_premium": {
            "id": "ACT-OFERTA-ROTA",
            "name": "oferta_rota_favorita",
            "channel": "email",
            "msg_template": "Prezado(a) cliente {tier_fmt}! Planeje sua próxima viagem de lazer para {rota} com 20% de bônus em pontos qualificáveis e franquia adicional de bagagem garantida.",
            "fact_id": "AF-QUALIFYING-POINTS",
            "fact_verif": "official_current_verified",
            "valid_from": "2024-04-01",
            "source": "Regulamento Azul Fidelidade Anexo III",
        },
        "maximizador_milhas": {
            "id": "ACT-RESGATE-ESPECIAL",
            "name": "oferta_resgate_especial",
            "channel": "app",
            "msg_template": "Olá! Você tem {saldo} Pontos Azul disponíveis. Aproveite condições especiais de emissão de passagens nacionais com tabela de pontos congelada exclusiva da sua categoria {tier_fmt}.",
            "fact_id": "AF-RESGATE-ESPECIAL-2025",
            "fact_verif": "official_current_partial",
            "valid_from": "2025-01-01",
            "source": "Resgate Especial Azul — Tabela Fixa 2025",
        },
        "regional_dependente": {
            "id": "ACT-CONTATO",
            "name": "contato_proativo_relacionamento",
            "channel": "telefone",
            "msg_template": "Olá! Agradecemos sua fidelidade conectando sua região pela rota {rota}. Para assegurar sua tranquilidade, disponibilizamos atendimento prioritário dedicado.",
            "fact_id": "AF-ATENDIMENTO-PRIORITARIO",
            "fact_verif": "official_current_verified",
            "valid_from": "2024-04-01",
            "source": "Regulamento Azul Fidelidade Cláusula 9.2",
        },
        "eventual_ascendente": {
            "id": "ACT-ANTECIPACAO-NIVEL",
            "name": "antecipacao_de_nivel",
            "channel": "app",
            "msg_template": "Você está a apenas {meta_falta}% da meta para o próximo nível no Azul Fidelidade! Complete mais 2 trechos até o fim do trimestre e garanta upgrade assistido.",
            "fact_id": "AF-TIER-PROGRESSION",
            "fact_verif": "official_current_verified",
            "valid_from": "2024-04-01",
            "source": "Regulamento Azul Fidelidade Tabela de Qualificação",
        },
        "eventual_promocional": {
            "id": "ACT-BONUS-PONTOS",
            "name": "gesto_reconhecimento_bonus_pontos",
            "channel": "email",
            "msg_template": "Reative seus pontos Azul! Ganhe 2.000 pontos bônus no seu próximo voo reservado até o fim do mês.",
            "fact_id": "AF-QUALIFYING-POINTS",
            "fact_verif": "official_current_verified",
            "valid_from": "2024-04-01",
            "source": "Regulamento de Campanhas Promocionais Azul",
        },
    }

    now_iso = dt.datetime(2026, 9, 1, 10, 0, 0).isoformat()
    for _, c in df_customers.iterrows():
        p_key = c["persona"]
        act_info = actions_map.get(p_key, actions_map["maximizador_milhas"])

        meta_falta = max(5, int((1.0 - min(c["meta_proximo_nivel_pct"], 0.95)) * 100))
        tier_fmt = c["tier"].replace("_", " ").title()
        msg = act_info["msg_template"].format(
            rota=c["rota_favorita"],
            tier_fmt=tier_fmt,
            saldo=f"{c['saldo_pontos']:,}".replace(",", "."),
            meta_falta=meta_falta,
        )

        justification = {
            "shap_top3": json.loads(c["shap_top3"]),
            "atritos_dominantes": [c["atritos_dominantes"]],
            "regras": [f"tier_{c['tier']}_elegivel", f"risk_state_{c['risk_state']}"],
            "valor_em_risco_brl": c["valor_em_risco"],
        }

        citations = [
            {
                "fact_id": act_info["fact_id"],
                "verification_status": act_info["fact_verif"],
                "valid_from": act_info["valid_from"],
                "source": act_info["source"],
            }
        ]

        # Flag de revisão humana se cliente tem risco alto mas confiança intermediária ou tier extremo
        needs_human = bool(c["churn_prob"] > 0.75 and c["clv_12m_previsto"] > 12000.0)

        recs_rows.append(
            {
                "customer_id": c["customer_id"],
                "action_id": act_info["id"],
                "action_name": act_info["name"],
                "channel": act_info["channel"],
                "message": msg,
                "justification_json": json.dumps(justification),
                "citations_json": json.dumps(citations),
                "confidence": round(float(np.random.uniform(0.85, 0.98)), 3),
                "human_review": needs_human,
                "mode": "offline",
                "snapshot_version": "research-2026-10-12",
                "recommended_at": now_iso,
            }
        )

    df_recs = pd.DataFrame(recs_rows)
    df_recs.to_parquet(out_dir / "agent_recommendations.parquet", index=False)

    # 5. FRICTION MAP (conforming to schemas/friction_map.yaml)
    aspects = ["atraso", "bagagem", "atendimento", "app_checkin", "resgate_milhas", "preco", "conforto"]
    semesters = ["2024-S1", "2024-S2", "2025-S1", "2025-S2", "2026-S1", "2026-S2"]

    fric_rows = []
    for asp in aspects:
        base_neg = {
            "atraso": 0.72,
            "bagagem": 0.65,
            "atendimento": 0.58,
            "app_checkin": 0.62,
            "resgate_milhas": 0.78,
            "preco": 0.70,
            "conforto": 0.45,
        }[asp]

        # Tendência com ligeira redução ao longo do tempo (impacto de melhorias operacionais)
        for i, sem in enumerate(semesters):
            mentions = int(np.random.normal(120, 15))
            trend_factor = 1.0 - (i * 0.02) + float(np.random.normal(0, 0.03))
            neg_rate = float(np.clip(base_neg * trend_factor, 0.30, 0.90))
            neg_count = int(round(mentions * neg_rate))
            neu_count = int(round(mentions * 0.15))
            pos_count = max(0, mentions - neg_count - neu_count)

            fric_rows.append(
                {
                    "friction_id": f"{asp}_{sem}",
                    "aspect": asp,
                    "semester": sem,
                    "mention_count": mentions,
                    "negative_count": neg_count,
                    "neutral_count": neu_count,
                    "positive_count": pos_count,
                    "negative_rate": round(neg_rate, 3),
                }
            )

    df_friction = pd.DataFrame(fric_rows)
    df_friction.to_parquet(out_dir / "friction_map.parquet", index=False)

    # 6. FAIRNESS METRICS
    fairness_rows = []

    for dim in ["faixa_etaria", "genero", "regiao"]:
        groups = df_customers[dim].unique()
        # Referência de seleção maior no grupo
        group_rates = df_customers.groupby(dim)["alto_valor"].mean()
        max_rate = float(group_rates.max())

        for g in sorted(groups):
            sub_g = df_customers[df_customers[dim] == g]
            cnt = len(sub_g)
            av_cnt = int(sub_g["alto_valor"].sum())
            sel_rate = float(av_cnt / cnt) if cnt > 0 else 0.0
            avg_churn = float(sub_g["churn_prob"].mean())
            ratio = float(sel_rate / max_rate) if max_rate > 0 else 1.0

            fairness_rows.append(
                {
                    "sensitive_attribute": dim,
                    "group_value": str(g),
                    "group_size": cnt,
                    "alto_valor_count": av_cnt,
                    "selection_rate": round(sel_rate, 4),
                    "avg_predicted_churn": round(avg_churn, 4),
                    "selection_ratio_vs_max": round(ratio, 4),
                    "four_fifths_compliant": bool(ratio >= 0.80),
                }
            )

    df_fairness = pd.DataFrame(fairness_rows)
    df_fairness.to_parquet(out_dir / "fairness_metrics.parquet", index=False)

    return {
        "customers_scores": df_customers,
        "personas_summary": df_personas_summary,
        "customer_timeline": df_timeline,
        "agent_recommendations": df_recs,
        "friction_map": df_friction,
        "fairness_metrics": df_fairness,
    }


if __name__ == "__main__":
    res = build_all_fixtures()
    print(f"Fixtures geradas com sucesso em {FIXTURES_DIR}:")
    for k, v in res.items():
        print(f" - {k}: {len(v)} linhas")
