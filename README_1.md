# PhonePe Pulse — Transaction Analytics, Segmentation & Forecasting

End-to-end SQL + Python analytics project built on **PhonePe's own public Pulse dataset**
(open data, CDLA-Permissive-2.0 license, https://github.com/PhonePe/pulse), covering
2018–2026 state-level transaction data across 33+ Indian states/UTs.

## What this project does
1. **ETL** (`etl_load.py`) — parses ~1,250 nested JSON files into a flat
   `(state, year, quarter, category, txn_count, txn_amount)` table (3,671 rows) and loads it
   into a SQLite database (`phonepe_pulse.db`).
2. **SQL business analysis** (`analysis_queries.sql`) — CTEs and window functions to answer:
   - National transaction value/volume trend by quarter
   - YoY growth by payment category (P2P, Retail/Merchant, Utility)
   - Top states by transaction value
   - Category mix (% share) per state — used as clustering features
   - States with fastest-growing merchant (Retail) adoption since 2018
3. **State segmentation** (`analysis.py`) — K-Means clustering (k=4) of states on
   transaction-category mix, total value and growth-since-2018, producing labeled segments
   (e.g. *Mature & Merchant-Heavy*, *High-Growth Emerging*, *Low-Penetration/Nascent*) —
   useful for a merchant-acquisition or marketing-prioritization decision.
4. **Forecasting** (`analysis.py`) — Holt-Winters exponential smoothing on the national
   quarterly time series to project the next 4 quarters of transaction value.

## Key findings
- National transaction value grew from ~₹1,725 Cr (Q1 2018) to ~₹45.5 lakh Cr (Q2 2026).
- Forecast: national transaction value projected to reach ~₹53.6 lakh Cr by Q2 2027.
- Merchant (Retail) payment adoption grew fastest in smaller states/UTs off a low base
  (Andaman & Nicobar, Arunachal Pradesh, Ladakh), signalling under-penetrated
  merchant-acquisition opportunity outside the large metros.
- Maharashtra, Karnataka and Telangana lead in absolute transaction value; Bihar,
  Rajasthan and Andhra Pradesh combine high value with high growth.

## Files
| File | Purpose |
|---|---|
| `etl_load.py` | JSON → flat table → SQLite |
| `analysis_queries.sql` | Core SQL business queries |
| `analysis.py` | Segmentation (K-Means) + forecasting (Holt-Winters) + charts |
| `state_segments.csv`, `national_quarterly.csv`, `forecast_next_4q.csv` | Output tables |
| `segment_scatter.png`, `forecast_national.png` | Visuals |

## Stack
Python (pandas, scikit-learn, statsmodels, matplotlib), SQL (SQLite), Git.
