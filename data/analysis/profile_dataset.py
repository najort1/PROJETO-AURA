import os
import sys
import json
import pandas as pd
import numpy as np

file_path = 'data/raw/Airline_review.csv'
file_size_bytes = os.path.getsize(file_path)
file_size_mb = file_size_bytes / (1024 * 1024)

print(f"File size: {file_size_bytes} bytes ({file_size_mb:.2f} MB)")

df = pd.read_csv(file_path)
total_rows, total_cols = df.shape
print(f"Total rows: {total_rows}, Total cols: {total_cols}")

# Columns and data types
col_info = []
for col in df.columns:
    null_count = int(df[col].isnull().sum())
    null_pct = (null_count / total_rows) * 100
    n_unique = int(df[col].nunique(dropna=True))
    col_info.append({
        "column": col,
        "dtype": str(df[col].dtype),
        "null_count": null_count,
        "null_pct": round(null_pct, 2),
        "n_unique": n_unique,
        "sample_values": df[col].dropna().head(3).tolist()
    })

# Check duplicates
content_cols = [c for c in df.columns if c != 'Unnamed: 0']
content_duplicates = int(df.duplicated(subset=content_cols).sum())

# Overall_Rating inspection
# Let's check non-numeric or strange values in Overall_Rating
print("\n--- Overall Rating Analysis ---")
df['Overall_Rating_num'] = pd.to_numeric(df['Overall_Rating'], errors='coerce')
invalid_ratings = df[df['Overall_Rating'].notnull() & df['Overall_Rating_num'].isnull()]
print(f"Invalid non-numeric Overall_Rating count: {len(invalid_ratings)}")
if len(invalid_ratings) > 0:
    print("Invalid values sample:", invalid_ratings['Overall_Rating'].value_counts().head(10).to_dict())

rating_stats = df['Overall_Rating_num'].describe().to_dict()
rating_dist = df['Overall_Rating_num'].value_counts().sort_index().to_dict()

# Recommended inspection
print("\n--- Recommended Analysis ---")
rec_dist = df['Recommended'].value_counts(dropna=False).to_dict()
rec_pct = (df['Recommended'].value_counts(normalize=True, dropna=False) * 100).round(2).to_dict()

# Cross tab of Recommended vs Overall_Rating
cross_rec_rating = df.groupby('Recommended')['Overall_Rating_num'].agg(['count', 'mean', 'median', 'std', lambda x: (x <= 3).sum() / len(x) if len(x)>0 else 0]).to_dict()

# Airline inspection
print("\n--- Airline Analysis ---")
n_airlines = int(df['Airline Name'].nunique())
top_airlines = df['Airline Name'].value_counts().head(20).to_dict()

# Search for Azul, Brazilian airlines, Brazilian routes
azul_exact = df[df['Airline Name'].str.contains(r'\bAzul\b', case=False, na=False)]
print(f"Airlines matching 'Azul': {azul_exact['Airline Name'].unique().tolist()}")

brazilian_airlines_search = ['azul', 'gol', 'tam', 'latam', 'passaredo', 'voepass', 'avianca brasil', 'varig']
found_airlines = {}
for term in brazilian_airlines_search:
    matches = df[df['Airline Name'].str.contains(rf'\b{term}\b', case=False, na=False)]['Airline Name'].unique().tolist()
    if matches:
        found_airlines[term] = matches
print(f"Brazilian airlines found in Airline Name: {found_airlines}")

# Search for Brazil / Brazilian routes in 'Route' or 'Review'
brazil_route_terms = ['brazil', 'brasil', 'sao paulo', 'são paulo', 'rio de janeiro', 'gru', 'gig', 'bsb', 'vcp', 'campinas', 'porto alegre', 'recife', 'salvador', 'fortaleza', 'curitiba', 'florianopolis']
route_matches = {}
for term in brazil_route_terms:
    m = df[df['Route'].str.contains(rf'\b{term}\b', case=False, na=False)]
    if len(m) > 0:
        route_matches[term] = len(m)
print(f"Mentions of Brazilian cities/airports in Route: {route_matches}")

# Review text mentions of Azul
azul_in_review = df[df['Review'].str.contains(r'\bAzul\b', case=False, na=False)]
print(f"Reviews mentioning 'Azul': {len(azul_in_review)}")
if len(azul_in_review) > 0:
    print("Airlines where 'Azul' was mentioned in review:", azul_in_review['Airline Name'].value_counts().head(5).to_dict())

# Summary of sub-ratings (Seat Comfort, Cabin Staff, Food, Ground Service, Entertainment, Wifi, Value)
sub_ratings = ['Seat Comfort', 'Cabin Staff Service', 'Food & Beverages', 'Ground Service', 'Inflight Entertainment', 'Wifi & Connectivity', 'Value For Money']
sub_rating_summary = {}
for sr in sub_ratings:
    if sr in df.columns:
        s_num = pd.to_numeric(df[sr], errors='coerce')
        sub_rating_summary[sr] = {
            "mean": round(float(s_num.mean()), 2),
            "median": float(s_num.median()),
            "missing_pct": round(float(df[sr].isnull().mean()) * 100, 2),
            "pct_rating_1": round(float((s_num == 1).sum() / s_num.count() * 100), 2) if s_num.count() > 0 else 0
        }

# Correlation with Overall_Rating_num
corr = {}
for sr in sub_ratings:
    if sr in df.columns:
        s_num = pd.to_numeric(df[sr], errors='coerce')
        corr[sr] = round(float(df['Overall_Rating_num'].corr(s_num)), 3)

results = {
    "file_size_bytes": file_size_bytes,
    "file_size_mb": round(file_size_mb, 2),
    "total_rows": total_rows,
    "total_cols": total_cols,
    "content_duplicates": content_duplicates,
    "columns": col_info,
    "overall_rating_stats": {k: round(v, 2) if isinstance(v, float) else v for k, v in rating_stats.items()},
    "overall_rating_dist": {str(k): int(v) for k, v in rating_dist.items()},
    "recommended_dist": {str(k): int(v) for k, v in rec_dist.items()},
    "recommended_pct": {str(k): float(v) for k, v in rec_pct.items()},
    "n_unique_airlines": n_airlines,
    "top_airlines": top_airlines,
    "brazilian_airlines_found": found_airlines,
    "brazilian_route_mentions": route_matches,
    "reviews_mentioning_azul": len(azul_in_review),
    "sub_rating_summary": sub_rating_summary,
    "correlations_with_overall": corr
}

with open('data/analysis/profiling_summary.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("\nProfiling completed successfully and saved to data/analysis/profiling_summary.json")
