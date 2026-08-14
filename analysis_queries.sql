-- PhonePe Pulse Transaction Analytics: SQL Business Queries
-- Table: transactions(state, year, quarter, category, txn_count, txn_amount)

-- 1. National transaction value & volume trend by quarter
SELECT year, quarter,
       SUM(txn_count)  AS total_txns,
       ROUND(SUM(txn_amount)/1e7, 2) AS total_value_cr
FROM transactions
GROUP BY year, quarter
ORDER BY year, quarter;

-- 2. YoY growth in transaction value, national, by category
WITH yearly AS (
  SELECT year, category, SUM(txn_amount) AS amt
  FROM transactions GROUP BY year, category
)
SELECT a.category, a.year, a.amt AS curr_year_amt, b.amt AS prev_year_amt,
       ROUND(100.0*(a.amt - b.amt)/b.amt, 1) AS yoy_growth_pct
FROM yearly a
JOIN yearly b ON a.category = b.category AND a.year = b.year + 1
ORDER BY a.category, a.year;

-- 3. Top 10 states by average quarterly transaction value (latest year)
SELECT state, ROUND(AVG(txn_amount)/1e7, 2) AS avg_qtr_value_cr
FROM transactions
WHERE year = (SELECT MAX(year) FROM transactions)
GROUP BY state
ORDER BY avg_qtr_value_cr DESC
LIMIT 10;

-- 4. Category mix (% share of value) per state, latest year -- for segmentation features
SELECT state, category,
       ROUND(100.0 * SUM(txn_amount) / SUM(SUM(txn_amount)) OVER (PARTITION BY state), 1) AS pct_of_state_value
FROM transactions
WHERE year = (SELECT MAX(year) FROM transactions)
GROUP BY state, category
ORDER BY state, pct_of_state_value DESC;

-- 5. States with fastest-growing "Retail" (merchant payments) adoption, 2018 -> latest year
WITH first_last AS (
  SELECT state,
         SUM(CASE WHEN year = 2018 THEN txn_amount ELSE 0 END) AS amt_2018,
         SUM(CASE WHEN year = (SELECT MAX(year) FROM transactions) THEN txn_amount ELSE 0 END) AS amt_latest
  FROM transactions
  WHERE category = 'Retail'
  GROUP BY state
)
SELECT state, amt_2018, amt_latest,
       ROUND((amt_latest - amt_2018) / NULLIF(amt_2018,0), 1) AS growth_multiple
FROM first_last
WHERE amt_2018 > 0
ORDER BY growth_multiple DESC
LIMIT 10;
