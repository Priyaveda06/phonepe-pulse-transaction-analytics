"""
ETL: PhonePe Pulse (aggregated/transaction/country/india/state/<state>/<year>/<q>.json)
-> flat table -> SQLite

Grain: one row per (state, year, quarter, transaction_category)
"""
import json, glob, os, sqlite3
import pandas as pd

BASE = "data/aggregated/transaction/country/india/state"
rows = []

for state_dir in sorted(glob.glob(f"{BASE}/*")):
    state = os.path.basename(state_dir).replace("-", " ").title()
    for year_dir in sorted(glob.glob(f"{state_dir}/*")):
        year = os.path.basename(year_dir)
        if not year.isdigit():
            continue
        for qfile in sorted(glob.glob(f"{year_dir}/*.json")):
            quarter = int(os.path.basename(qfile).replace(".json", ""))
            with open(qfile) as f:
                payload = json.load(f)
            tdata = (payload.get("data") or {}).get("transactionData") or []
            for cat in tdata:
                cat_name = cat.get("name")
                for pi in cat.get("paymentInstruments", []):
                    rows.append({
                        "state": state,
                        "year": int(year),
                        "quarter": quarter,
                        "category": cat_name,
                        "txn_count": pi.get("count"),
                        "txn_amount": pi.get("amount"),
                    })

df = pd.DataFrame(rows)
print("Rows parsed:", len(df))
print(df.head())
print("States:", df['state'].nunique(), "| Years:", sorted(df['year'].unique()))

df.to_csv("phonepe_transactions.csv", index=False)

conn = sqlite3.connect("phonepe_pulse.db")
df.to_sql("transactions", conn, if_exists="replace", index=False)
conn.execute("CREATE INDEX IF NOT EXISTS idx_state_year_q ON transactions(state, year, quarter)")
conn.commit()
conn.close()
print("Loaded into phonepe_pulse.db -> table 'transactions'")
