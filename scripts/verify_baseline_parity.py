"""Script de verificação independente da paridade matemática (QA Revisor Adversarial).
Calcula o ground truth direto dos artefatos Parquet em data/analytics/
"""
import pandas as pd
import numpy as np

def run_checks():
    print("=== 01 CARTEIRA ===")
    df_c = pd.read_parquet("data/analytics/customers_scores.parquet")
    n = len(df_c)
    clv_total = float(df_c["clv_12m_previsto"].sum())
    var_total = float((df_c["clv_12m_previsto"] * df_c["churn_prob"]).sum())
    alto_valor_cnt = int(df_c["alto_valor"].sum())
    alto_valor_pct = float(df_c["alto_valor"].mean())
    print(f"N: {n}")
    print(f"CLV Total: {clv_total:.2f}")
    print(f"CLV Medio: {clv_total / n:.2f}")
    print(f"VaR Total: {var_total:.2f}")
    print(f"Alto Valor: {alto_valor_cnt} ({alto_valor_pct*100:.2f}%)")

    # Lorenz / Gini
    sorted_clv = np.sort(df_c["clv_12m_previsto"].values)
    cum_clv = np.cumsum(sorted_clv) / np.sum(sorted_clv)
    cum_pop = np.arange(1, len(sorted_clv) + 1) / len(sorted_clv)
    trap_fn = getattr(np, "trapezoid", getattr(np, "trapz", None))
    gini = 1.0 - 2.0 * float(trap_fn(cum_clv, cum_pop))
    idx_80 = int(len(sorted_clv) * 0.8)
    top_20_share = 1.0 - cum_clv[idx_80]
    print(f"Gini: {gini:.4f} (aprox {gini:.2f})")
    print(f"Top 20% detem: {top_20_share*100:.2f}% (aprox {top_20_share*100:.1f}%)")

    print("\n=== 02 PERSONAS ===")
    df_p = pd.read_parquet("data/analytics/personas_summary.parquet")
    print(df_p[["persona", "nome_display", "clientes_count", "share_pct", "clv_medio", "churn_medio"]])

    print("\n=== 03 CLIENTE 360 & TIMELINE ===")
    df_sorted = df_c.sort_values("valor_em_risco", ascending=False)
    top1 = df_sorted.iloc[0]
    print(f"Top 1 VaR: ID={top1['customer_id']}, VaR={top1['valor_em_risco']:.2f}, Churn={top1['churn_prob']*100:.1f}%, CLV={top1['clv_12m_previsto']:.2f}, Persona={top1['persona']}, Tier={top1['tier']}")

    df_t = pd.read_parquet("data/analytics/customer_timeline.parquet")
    max_date = df_t["data"].max()
    post_cutoff = df_t[df_t["data"] > "2025-08-31"]
    print(f"Timeline max date: {max_date}")
    print(f"Eventos post-cutoff (> 2025-08-31): {len(post_cutoff)}")

    print("\n=== 05 ATRITOS ===")
    df_f = pd.read_parquet("data/analytics/friction_map.parquet")
    print(f"Friction rows: {len(df_f)}")
    print(f"Aspectos unicos: {df_f['aspect'].nunique()}")
    print(f"Semestres unicos: {df_f['semester'].nunique()}")
    print(f"Total mencoes: {df_f['mention_count'].sum()}")

    print("\n=== 06 SIMULADOR (CENARIO BASE) ===")
    orcamento = 80000.0
    custo_por_acao = 45.0
    taxa_resp = 0.18
    efeito_acao = 0.25
    margem = 0.22

    max_clientes_alcancaveis = int(orcamento // custo_por_acao)
    n_alvo = min(len(df_sorted), max_clientes_alcancaveis)
    df_target = df_sorted.iloc[:n_alvo].copy()

    p_evitada = df_target["churn_prob"] * efeito_acao * taxa_resp
    receita_salva_bruta = float((p_evitada * df_target["clv_12m_previsto"] * margem).sum())
    evasoes_evitadas_abs = float(p_evitada.sum())
    custo_total_campanha = float(n_alvo * custo_por_acao)
    delta_receita_liquida = receita_salva_bruta - custo_total_campanha
    roi_liquido = delta_receita_liquida / custo_total_campanha

    print(f"n_alvo: {n_alvo}")
    print(f"Custo total: R$ {custo_total_campanha:.2f}")
    print(f"Evasoes evitadas: {evasoes_evitadas_abs:.2f}")
    print(f"Receita salva: R$ {receita_salva_bruta:.2f}")
    print(f"Delta receita liquida: R$ {delta_receita_liquida:.2f}")
    print(f"ROI liquido: {roi_liquido*100:.2f}%")

    print("\n=== 07 IA RESPONSAVEL (FAIRNESS) ===")
    df_fair = pd.read_parquet("data/analytics/fairness_metrics.parquet")
    print(f"Total rows fairness: {len(df_fair)}")
    is_nao_inf = df_fair["group_value"].str.lower().str.contains("informado", na=False) & ~df_fair["group_value"].str.lower().str.contains("prefiro", na=False)
    df_inf = df_fair[~is_nao_inf]
    print(f"Grupos informados: {len(df_inf)}")
    print(f"Conformes: {int(df_inf['four_fifths_compliant'].sum())}")
    print(f"Nao conformes: {len(df_inf) - int(df_inf['four_fifths_compliant'].sum())}")
    nao_conf = df_inf[~df_inf["four_fifths_compliant"]]
    for _, r in nao_conf.iterrows():
        print(f"  - {r['sensitive_attribute']} | {r['group_value']}: ratio={r['selection_ratio_vs_max']:.4f}")

if __name__ == "__main__":
    run_checks()
