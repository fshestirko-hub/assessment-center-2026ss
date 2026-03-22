# Track A — Status & Observations

## What Has Been Done

### ETL Pipeline (`pipeline.py`)
Single command (`python3 pipeline.py`) runs the entire flow:
raw sources → clean → merge → analytics → output

### Data Sources Ingested (7 / 7)
| Source | Format | Rows | Key Challenge |
|---|---|---|---|
| `zenith_core_db.sqlite` | SQLite | 50,000 | TEXT dates, blob column |
| `customer_profiles_v2.json` | Nested JSON | 5,000 | 4-level nesting, fraud filter |
| `sku_summary.csv` | CSV | 200 | String booleans, % column name |
| `monthly_pnl_summary.csv` | CSV | 22 | Duplicate rows per month (two supervisors summed) |
| `sys_ops_log_archive.sys` | Tilde-delimited, no header | 22 | Manual column assignment |
| `marketing_spend_history.xlsx` | Excel (long format) | 88 | Already long — melt would have broken it |
| `warehouse_rate_card.xlsx` | Excel | 8 | Category name normalisation |

### Output Files (`output/`)
| File | Description | Rows |
|---|---|---|
| `master_transactions.csv` | **Single Source of Truth** — all sources merged | 50,000 |
| `master_transactions.json` | Same data in JSON (records orientation, 46 MB) | 50,000 |
| `transactions_clean.csv` | Cleaned transactions only | 50,000 |
| `customers_clean.csv` | Flattened customer profiles | 5,000 |
| `sku_clean.csv` | Cleaned SKU catalog with derived fields | 200 |
| `pnl_clean.csv` | Monthly P&L with EBITDA waterfall columns | 22 |
| `ops_clean.csv` | Warehouse ops aggregated to monthly level | 22 |
| `marketing_clean.csv` | Marketing spend by month + channel | 88 |
| `warehouse_clean.csv` | Storage rate card | 8 |
| `analytics_customers_by_channel_month.csv` | Customers, revenue, LTV by channel per month | 96 |
| `analytics_sku_performance.csv` | Aggregated revenue, margin, return rate per SKU | 200 |
| `analytics_cohort_retention.csv` | Repeat purchase rates by acquisition cohort | 292 |

### How the Master Dataset Is Produced
```
zenith_core_db.sqlite
    ↓ TransactionsExtractor
    ↓ parse dates, derive LineRevenue / LineCOGS / LineMargin, add Month column
    ↓
    LEFT JOIN customers_clean  ON CustomerID  →  adds AcqChannel, LoyaltyTier, MacroRegion, ProjectedLTV
    LEFT JOIN sku_clean        ON ProductID   →  adds GrossMarginPct, StorageCostPerUnit, InventoryCostBurden, IsDeadStock
    ↓
master_transactions.csv  (50,000 rows × 34 columns, 0% null in join keys)
```

The join is LEFT on both sides — no transaction rows are ever dropped, even if a customer profile or SKU record is missing. The merger reports null counts after every run.

---

## What Is Still Missing

### ❌ Charts (Track A requirement: 2–4 charts)
The biggest remaining item. Four charts are planned in `TRACK_A_PLAN.md`:
1. EBITDA margin over time (line chart) — data is ready in `pnl_clean.csv`
2. Cost waterfall for worst month — data is ready in `pnl_clean.csv`
3. SKU scatter: storage burden vs gross margin — data in `analytics_sku_performance.csv`
4. CAC trend by channel — data in `analytics_customers_by_channel_month.csv` + `marketing_clean.csv`

**To implement:** create `charts.py` using `matplotlib` / `seaborn` and call it from `pipeline.py`.

---

## Key Observations from the Data

### 1. Half the SKU catalogue actively destroys margin
**93 of 200 SKUs (46.5%) are flagged as dead stock** — slow-moving AND below 50% gross margin.
Several have *negative* gross margins, meaning the company loses money on every unit sold:

| SKU | Category | Gross Margin | Total Margin Lost |
|---|---|---|---|
| SKU-124 | Apparel | -298% | -$754 |
| SKU-187 | Apparel | -211% | -$875 |
| SKU-165 | Supplements | -158% | -$811 |
| SKU-169 | Supplements | -150% | -$1,070 |

These SKUs should be the first candidates for immediate discontinuation.

### 2. 2022 was entirely loss-making — then revenue tripled in 2023
**11 of 22 months had negative EBITDA — all of them in 2022.**
In 2022, monthly revenue was ~$120–130k with EBITDA margins as bad as -18%.
In January 2023, revenue jumped to $387k and EBITDA turned to +25% — and stayed there.

This is the central anomaly: **what changed in January 2023?** Possible explanations:
- A major product launch or pricing correction
- Discontinuation of loss-making SKUs
- A channel mix shift away from high-discount acquisition
- A large one-time order that inflated the base

This cliff-edge demands investigation before any EBITDA narrative is presented to the board.

### 3. Influencer channel customers have 36% lower projected LTV
| Channel | Customers | Total Revenue | Avg Projected LTV |
|---|---|---|---|
| Paid Social | 15,872 | $2,395,597 | $1,131 |
| Organic | 11,657 | $1,763,247 | $1,148 |
| Search | 7,799 | $1,191,797 | $1,141 |
| Influencer | 3,857 | $586,893 | **$728** |

Influencer is the smallest channel by revenue AND delivers the lowest quality customers. If influencer spend is growing, it is buying customers who are unlikely to return.

### 4. Cohort retention is flat, not degrading — which is suspicious
Average retention at month 1, 3, and 6 is nearly identical (~34–37%).
Normally retention curves drop sharply after month 1.
This flat pattern either means the data is synthetic, or there is genuine reactivation happening — worth investigating before presenting.

### 5. Marketing spend data has a structural gap
`marketing_clean.csv` contains spend by channel but does **not** contain new customer counts by channel per month — that is in `analytics_customers_by_channel_month.csv`.
To compute true CAC, these two datasets must be joined on `Month + Channel`.
**This join is not yet implemented** — it requires confirming that channel labels match exactly between both files.

---

## For Track B (Business Intelligence)

Track B can use the following files directly — no further coding needed:

| File | Use |
|---|---|
| `pnl_clean.csv` | EBITDA waterfall, cost breakdown, trend analysis |
| `analytics_sku_performance.csv` | High vs low performing SKUs, storage burden table |
| `analytics_customers_by_channel_month.csv` | CAC proxy, channel revenue trends |
| `marketing_clean.csv` | Spend by channel for CAC denominator |
| `master_transactions.csv` | Any custom aggregation needed in Excel/PowerBI |

**The master dataset is the SSoT** — all other files are either clean source inputs or pre-aggregated views derived from it.
