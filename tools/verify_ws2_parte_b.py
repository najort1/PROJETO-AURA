# Parte B mecânica (Lead-executada após falhas de subagentes) — replicando definições do pipeline
import glob
import json

import duckdb
import pandas as pd

con = duckdb.connect()
S = "data/curated/synthetic"


def out_of_order(table: str, key_cols: list[str]) -> int:
    """Conta linhas fora da ordem lexicográfica estrita das chaves canônicas."""
    keys = ", ".join(key_cols)
    lags = ", ".join(f"LAG({c}) OVER (ORDER BY {keys}) AS prev_{c}" for c in key_cols)
    cur = [f"{c} AS c{i}" for i, c in enumerate(key_cols)]
    prev = [f"prev_{c} AS p{i}" for i, c in enumerate(key_cols)]
    cond_parts = []
    for i in range(len(key_cols)):
        eqs = " AND ".join(f"c{j} = p{j}" for j in range(i)) + (" AND " if i else "")
        cond_parts.append(f"{eqs}c{i} < p{i}")
    q = (
        f"SELECT COUNT(*) FROM (SELECT {lags}, {', '.join(cur + prev)} "
        f"FROM read_parquet('{S}/{table}.parquet')) "
        f"WHERE {' OR '.join(cond_parts)} AND c0 IS NOT NULL AND p0 IS NOT NULL"
    )
    return con.execute(q).fetchone()[0]


print("== B1b: ordenacao canonica (0 esperado) ==")
for table, keys in [
    ("transactions", ["transaction_date", "customer_id"]),
    ("flights", ["scheduled_departure", "flight_id"]),
    ("interactions", ["interaction_date", "interaction_id"]),
    ("loyalty_events", ["event_date", "event_id"]),
]:
    print(f"  {table}: fora_de_ordem={out_of_order(table, keys)}")

print("== B2a: numeros de fidelidade (definicoes do pipeline) ==")
cust = con.execute(f"SELECT * FROM read_parquet('{S}/customers.parquet')").df()
tx = con.execute(f"SELECT * FROM read_parquet('{S}/transactions.parquet')").df()
inter = con.execute(f"SELECT * FROM read_parquet('{S}/interactions.parquet')").df()
flights = con.execute(f"SELECT departure_date FROM read_parquet('{S}/flights.parquet')").df()
n_cust = len(cust)

tx["year_month"] = tx["transaction_date"].dt.to_period("M")
mau_ratio = tx.groupby("year_month")["customer_id"].nunique().mean() / n_cust
print(f"  MAU mensal medio: {mau_ratio:.4f} (rel. 10.52%)")

spend = tx.groupby("customer_id")["amount_brl"].sum()
all_spend = spend.reindex(cust["customer_id"]).fillna(0.0).sort_values(ascending=False)
top20 = all_spend.head(max(1, int(n_cust * 0.2))).sum() / all_spend.sum()
print(f"  Pareto top-20%: {top20:.4f} (rel. 74.40%)")

tiers = cust["current_tier"].value_counts(normalize=True)
print(
    f"  %azul: {tiers.get('azul', 0):.4f} (rel. 95.61%) | %diamante+unique: "
    f"{tiers.get('diamante', 0) + tiers.get('diamante_unique', 0):.5f} (rel. 0.15%)"
)

nps_missing = inter["nps_rating"].isna().mean()
print(f"  NPS missingness: {nps_missing:.4f} (rel. ~49.2%)")

with open("data/curated/calibration_values.json", encoding="utf-8") as f:
    calib = json.load(f)
anac = calib["market.seasonality_by_route"]["market_monthly_index"]
flights["m"] = flights["departure_date"].dt.month
synth_counts = flights.groupby("m").size()
synth_norm = synth_counts / synth_counts.sum()
anac_norm = {int(k): v for k, v in anac.items()}
anac_s = pd.Series(anac_norm)
anac_share = anac_s / anac_s.sum()
r = (
    pd.concat([synth_norm, anac_share], axis=1, keys=["synth", "anac"])
    .dropna()
    .iloc[:, 0]
    .corr(pd.concat([synth_norm, anac_share], axis=1, keys=["synth", "anac"]).dropna().iloc[:, 1])
)
print(f"  r sazonalidade: {r:.4f} (rel. 0.8744)")

print("== B2c: isolamento ground truth em data/analytics ==")
banned = {
    "arquetipo",
    "arquetipo_latente",
    "clv_real_12m",
    "hazard_latente",
    "churn_latente",
    "propensao",
}
for f in sorted(glob.glob("data/analytics/*.parquet")):
    cols = [
        c.lower() for c in con.execute(f"SELECT * FROM read_parquet('{f}') LIMIT 0").df().columns
    ]
    leaks = sorted(set(cols) & banned)
    print(f"  {f.split(chr(92))[-1]}: {'VAZOU ' + str(leaks) if leaks else 'ok'}")
with open("schemas/ground_truth.yaml", encoding="utf-8") as f:
    gt = f.read()
print(f"  ground_truth consumers evaluation_only: {'evaluation_only' in gt}")

con.close()
print("FIM")
