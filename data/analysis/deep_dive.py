import json

import pandas as pd

df = pd.read_csv("data/raw/Airline_review.csv")

# 1. TAM and LATAM analysis
tam_df = df[df["Airline Name"] == "TAM Airlines"]
latam_df = df[df["Airline Name"] == "LATAM Airlines"]

print(f"TAM Airlines count: {len(tam_df)}")
print(f"LATAM Airlines count: {len(latam_df)}")

# 2. Azul mention in reviews
azul_in_review = df[df["Review"].str.contains(r"\bAzul\b", case=False, na=False)]
print(f"\nAzul mentioned in {len(azul_in_review)} review(s):")
for idx, row in azul_in_review.iterrows():
    print(
        f"Row {idx} | Airline: {row['Airline Name']} | Route: {row['Route']} | Rating: {row['Overall_Rating']}"
    )
    print(f"Title: {row['Review_Title']}")
    print(f"Review Snippet: {row['Review'][:400]}...")

# 3. Brazilian routes detail
brazil_keywords = [
    "sao paulo",
    "são paulo",
    "rio de janeiro",
    "gru",
    "gig",
    "brasilia",
    "bsb",
    "campinas",
    "vcp",
    "porto alegre",
    "recife",
    "salvador",
    "curitiba",
    "belo horizonte",
    "manaus",
    "brazil",
    "brasil",
]
brazil_routes_df = df[df["Route"].str.contains("|".join(brazil_keywords), case=False, na=False)]
print(f"\nTotal reviews with Brazilian routes/airports: {len(brazil_routes_df)}")
print("Airlines operating these Brazilian routes (Top 10):")
print(brazil_routes_df["Airline Name"].value_counts().head(10))

# 4. Date ranges
print("\n--- Date Ranges ---")
# Date Flown
print("Date Flown non-null count:", df["Date Flown"].notnull().sum())
print(
    "Date Flown samples:",
    df["Date Flown"].dropna().unique()[:5],
    "...",
    df["Date Flown"].dropna().unique()[-5:],
)

# Review Date
print("Review Date non-null count:", df["Review Date"].notnull().sum())
print(
    "Review Date samples:",
    df["Review Date"].dropna().unique()[:5],
    "...",
    df["Review Date"].dropna().unique()[-5:],
)

# Parse Review Date to see actual min and max years
df["Review_Year"] = df["Review Date"].str.extract(r"(\d{4})")[0]
print("Review Year value counts:")
print(df["Review_Year"].value_counts().sort_index())

# 5. Friction Analysis
# Look at low ratings (1-3) vs high ratings (7-9)
negative_reviews = df[df["Overall_Rating"].isin(["1", "2", "3"])]
positive_reviews = df[df["Overall_Rating"].isin(["7", "8", "9"])]

friction_terms = {
    "delay_cancellation": r"delay|delayed|late|cancel|cancelled|cancellation",
    "baggage_lost": r"bag|baggage|luggage|lost bag|damaged",
    "refund_cost": r"refund|money|compensation|charge|fee|expensive|cost|voucher",
    "customer_service_rude": r"rude|unhelpful|unprofessional|attitude|arrogant|ignored|disrespectful",
    "boarding_checkin_queue": r"check-in|check in|boarding|gate|queue|line|wait",
    "seat_comfort_space": r"seat|uncomfortable|legroom|cramped|space|broken seat|pitch",
    "food_beverage": r"food|meal|drink|water|snack|beverage|hungry|taste",
    "communication_information": r"information|no communication|nobody told|told nothing|announcement|communication",
    "connection_missed": r"connection|missed flight|transit|transfer",
}

print(
    f"\n--- Friction Prevalences in Negative Reviews (Overall_Rating 1-3, N={len(negative_reviews)}) ---"
)
friction_stats = {}
for category, regex in friction_terms.items():
    neg_pct = (
        negative_reviews["Review"].str.contains(regex, case=False, na=False).sum()
        / len(negative_reviews)
    ) * 100
    pos_pct = (
        positive_reviews["Review"].str.contains(regex, case=False, na=False).sum()
        / len(positive_reviews)
    ) * 100
    friction_stats[category] = {
        "negative_pct": round(neg_pct, 2),
        "positive_pct": round(pos_pct, 2),
        "gap": round(neg_pct - pos_pct, 2),
    }
    print(
        f"{category:30s}: Neg={neg_pct:5.2f}% | Pos={pos_pct:5.2f}% | Gap={neg_pct - pos_pct:5.2f}%"
    )

with open("data/analysis/friction_analysis.json", "w", encoding="utf-8") as f:
    json.dump(
        {
            "tam_count": len(tam_df),
            "latam_count": len(latam_df),
            "brazil_routes_count": len(brazil_routes_df),
            "review_years": df["Review_Year"].value_counts().sort_index().to_dict(),
            "friction_stats": friction_stats,
        },
        f,
        indent=2,
    )
