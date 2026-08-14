import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from statsmodels.tsa.holtwinters import ExponentialSmoothing

conn = sqlite3.connect("phonepe_pulse.db")
df = pd.read_sql("SELECT * FROM transactions", conn)
latest_year = df.year.max()

# ---------------------------------------------------------------
# 1. STATE SEGMENTATION (K-Means on latest-year category mix + growth)
# ---------------------------------------------------------------
latest = df[df.year == latest_year]
mix = (latest.groupby(["state", "category"])["txn_amount"].sum()
       .unstack(fill_value=0))
mix_pct = mix.div(mix.sum(axis=1), axis=0) * 100  # % share per category

vol = latest.groupby("state")["txn_amount"].sum().rename("total_value")
first = df[df.year == 2018].groupby("state")["txn_amount"].sum()
growth = ((vol - first) / first.replace(0, np.nan) * 100).rename("growth_since_2018_pct")

features = mix_pct.join(vol).join(growth).dropna()
X = StandardScaler().fit_transform(features[["P2P", "Retail", "Utility", "total_value", "growth_since_2018_pct"]])

km = KMeans(n_clusters=4, random_state=42, n_init=10)
features["segment"] = km.fit_predict(X)

seg_profile = features.groupby("segment")[["P2P", "Retail", "Utility", "total_value", "growth_since_2018_pct"]].mean().round(1)
seg_profile["n_states"] = features.groupby("segment").size()

# Human-readable labels: rank segments by value and growth so labels are distinct
val_rank = seg_profile["total_value"].rank(ascending=False)
growth_rank = seg_profile["growth_since_2018_pct"].rank(ascending=False)
labels = {}
for seg in seg_profile.index:
    v, g = val_rank[seg], growth_rank[seg]
    if v <= 2 and seg_profile.loc[seg, "Retail"] >= seg_profile["Retail"].median():
        labels[seg] = "Mature & Merchant-Heavy"
    elif g <= 2:
        labels[seg] = "High-Growth Emerging"
    elif v <= 2:
        labels[seg] = "Large P2P-Dominant"
    else:
        labels[seg] = "Low-Penetration / Nascent"
features["segment_label"] = features["segment"].map(labels)

features[["segment", "segment_label", "P2P", "Retail", "Utility", "total_value", "growth_since_2018_pct"]] \
    .sort_values("segment").to_csv("state_segments.csv")

print("=== State Segments (K-Means, k=4) ===")
print(seg_profile.assign(label=seg_profile.index.map(labels)))
print()
print(features[["segment_label"]].reset_index().groupby("segment_label")["state"].apply(list).to_string())

# Segment scatter plot
plt.figure(figsize=(7, 5))
colors = plt.cm.Set2(features["segment"] / features["segment"].max())
plt.scatter(features["total_value"], features["growth_since_2018_pct"], c=colors, s=60)
for state, row in features.iterrows():
    if row["total_value"] > features["total_value"].quantile(0.75) or row["growth_since_2018_pct"] > features["growth_since_2018_pct"].quantile(0.9):
        plt.annotate(state, (row["total_value"], row["growth_since_2018_pct"]), fontsize=7)
plt.xlabel("Total transaction value, latest FY (Rs.)")
plt.ylabel("Growth since 2018 (%)")
plt.title("State Segments: Digital Payment Maturity vs Growth")
plt.tight_layout()
plt.savefig("segment_scatter.png", dpi=140)
plt.close()

# ---------------------------------------------------------------
# 2. FORECASTING national quarterly transaction value (Holt-Winters)
# ---------------------------------------------------------------
national = df.groupby(["year", "quarter"])["txn_amount"].sum().reset_index()
national["period"] = national["year"].astype(str) + "Q" + national["quarter"].astype(str)
ts = national.set_index("period")["txn_amount"]
ts.index = pd.PeriodIndex(national["year"].astype(str) + "Q" + national["quarter"].astype(str), freq="Q")

# Exclude an incomplete final quarter if the newest year has < 4 quarters
model = ExponentialSmoothing(ts, trend="add", seasonal="add", seasonal_periods=4).fit()
forecast = model.forecast(4)

print("\n=== National Quarterly Transaction Value Forecast (next 4 quarters, Rs.) ===")
print(forecast.round(0))

plt.figure(figsize=(9, 5))
ts.plot(label="Actual", marker="o")
forecast.plot(label="Forecast", marker="o", linestyle="--")
plt.title("PhonePe National Transaction Value: Actual vs Forecast (Holt-Winters)")
plt.ylabel("Transaction value (Rs.)")
plt.legend()
plt.tight_layout()
plt.savefig("forecast_national.png", dpi=140)
plt.close()

national.to_csv("national_quarterly.csv", index=False)
forecast.to_frame("forecast_txn_amount").to_csv("forecast_next_4q.csv")

print("\nSaved: state_segments.csv, segment_scatter.png, national_quarterly.csv, forecast_next_4q.csv, forecast_national.png")
