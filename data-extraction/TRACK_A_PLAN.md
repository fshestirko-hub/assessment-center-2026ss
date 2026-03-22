# Track A — Data Engineering & Analytics: Full Execution Plan

## 1. Mission Statement

Build a reproducible, clean data foundation for Zenith Active Solutions from 7 incompatible raw sources. Produce a merged "Single Source of Truth" dataset, 3 business-ready analytical datasets, 4 diagnostic charts, and a lightweight ETL pipeline — all connected back to the core profitability crisis narrative.

---

## 2. Data Room Inventory & Schema Analysis

### 2.1 `zenith_core_db.sqlite` — Core Transaction Ledger

**Table:** `transactions_master` | **Rows:** 50,000

| Column | Type | Notes |
|---|---|---|
| `OrderID` | TEXT | Primary key |
| `OrderDate` | TEXT | Needs parsing → datetime |
| `CustomerID` | TEXT | Join key to JSON profiles |
| `ProductID` | TEXT | Join key to sku_summary |
| `Category` | TEXT | Apparel / Accessories / Equipment |
| `Region` | TEXT | Geographic dimension |
| `Quantity` | INTEGER | Units per order line |
| `SellingPrice` | REAL | Revenue per unit |
| `CostPrice` | REAL | COGS per unit |
| `ShippingCost` | REAL | Fulfilment cost |
| `PaymentProcessingFee` | REAL | Payment cost |
| `ShippingProvider` | TEXT | Carrier identifier |
| `ReturnFlag` | INTEGER | 0/1 return indicator |
| `Transaction_Log` | TEXT | Raw log blob — needs parsing |

**Known issues to handle:**
- `OrderDate` stored as TEXT, not DATE — must cast
- `Transaction_Log` is a raw blob column — needs inspection for embedded metadata
- Duplicate `ReturnFlag` handling (returns may inflate unit counts)

---

### 2.2 `customer_profiles_v2.json` — Deeply Nested User Telemetry

**Format:** Single dict keyed by `usr_profile_CUST-XXXX` → nested object

**Nested structure per profile:**
```
usr_profile_CUST-0001
├── sys_meta
│   ├── uuid
│   ├── last_login_ip
│   ├── browser_agent
│   └── session_flags[]
├── account_details
│   ├── geo_segmentation { macro_region, micro_zone }
│   └── preferences { primary_goal, secondary_goals[] }
├── acquisition_telemetry
│   ├── source { utm_medium, click_id }
│   └── hardware { primary_device }
└── financial_metrics_v2
    ├── status { tier, reward_points }
    ├── projected_ltv_at_signup_usd
    ├── last_model_update
    └── risk_factors { return_rate_pct, fraud_lock }
```

**Fields to extract and flatten:**
- `CustomerID` (derived from key: strip `usr_profile_`)
- `utm_medium` → acquisition channel
- `macro_region`, `micro_zone` → geography
- `primary_goal` → customer segment
- `tier` → loyalty tier (Bronze / Silver / Gold)
- `projected_ltv_at_signup_usd` → LTV signal
- `return_rate_pct` → risk signal
- `fraud_lock` → filter flag

**Known issues to handle:**
- Key format is `usr_profile_CUST-XXXX` — must normalize to `CUST-XXXX`
- `secondary_goals` is a list — flatten to pipe-separated string or take first
- `session_flags` is a list of booleans — likely noise, can drop
- `last_model_update` is a date string — parse where needed

---

### 2.3 `sku_summary.csv` — Product Catalog

| Column | Notes |
|---|---|
| `ProductID` | Join key to transactions |
| `Category` | Apparel / Accessories / Equipment |
| `Color` | Product variant |
| `EcoFriendly` | Boolean flag |
| `TotalRevenue` | Aggregate revenue (pre-calculated) |
| `TotalUnitsSold` | Aggregate units |
| `GrossMargin%` | Pre-calculated margin (0–1 decimal) |
| `AverageDaysInInventory` | Inventory age signal |
| `ReturnRate` | Product-level return % |
| `StorageCostPerUnit` | Cost driver for dead stock analysis |

**Known issues:**
- `GrossMargin%` is a decimal (0.645 = 64.5%) — label carefully in outputs
- `EcoFriendly` is `True`/`False` string — cast to boolean
- `StorageCostPerUnit` varies wildly (0.15 → 4.0) — key signal for inventory burden

---

### 2.4 `monthly_pnl_summary.csv` — Monthly P&L

| Column | Notes |
|---|---|
| `Month` | Format `YYYY-MM` |
| `GrossRevenue` | Top-line revenue |
| `TotalCOGS` | Cost of goods |
| `TotalDiscounts` | Discount spend |
| `TotalShipping` | Shipping cost |
| `TotalPaymentFees` | Payment processing |
| `ActualNetRevenue` | Revenue after discounts |
| `MonthlyLaborCost` | Labour |
| `WarehouseRent` | Fixed overhead |

**Known issues:**
- Month `2022-01` appears **twice** with different `MonthlyLaborCost` — likely duplicate rows for different shift supervisors; must deduplicate or aggregate
- EBITDA is not pre-calculated — must derive: `GrossRevenue - COGS - Discounts - Shipping - PaymentFees - LaborCost - WarehouseRent`

---

### 2.5 `sys_ops_log_archive.sys` — Non-Standard Shift Log

**Format:** Tilde (`~`) delimited, no header

**Inferred columns (from sample rows):**
```
2022-01 ~ M. Johnson ~ 48375 ~ 25000 ~ 96 ~ 0 ~ 0.013 ~ 3.1 ~ 45.2
```

| Position | Inferred Meaning |
|---|---|
| 0 | Month (YYYY-MM) |
| 1 | Shift Supervisor Name |
| 2 | Monthly Labour Cost |
| 3 | Warehouse Rent |
| 4 | Orders Processed |
| 5 | Incidents / Errors |
| 6 | Error Rate |
| 7 | Avg Pick Time (min) |
| 8 | Avg Packing Time (min) |

**Known issues:**
- No header — must assign column names manually
- Cross-reference with `monthly_pnl_summary.csv` to validate labour cost figures
- Multiple rows per month (different supervisors) — aggregate per month for joining

---

### 2.6 `marketing_spend_history.xlsx` — Ad Spend by Channel

- Monthly breakdown of marketing spend per channel
- Key for CAC calculation when joined to customer acquisition data (JSON `utm_medium`)
- Requires `openpyxl` to read in Python

---

### 2.7 `warehouse_rate_card.xlsx` — Storage Cost by Category

- Vendor storage rate schedule per product category
- Cross-reference with `sku_summary.csv` `StorageCostPerUnit` and `AverageDaysInInventory`
- Requires `openpyxl` to read

---

## 3. Deliverables Map

| # | Deliverable | Source Data | Output File |
|---|---|---|---|
| D1 | Single Source of Truth (merged dataset) | SQLite + JSON + SKU CSV | `output/master_transactions.csv` + SQLite tables |
| D2 | Customers per month by acquisition channel | SSoT + JSON channels | `output/customers_by_channel_month.csv` |
| D3 | Revenue & margin per SKU | SSoT + SKU summary | `output/sku_performance.csv` |
| D4 | Repeat purchase / cohort metrics | SSoT (OrderDate + CustomerID) | `output/cohort_retention.csv` |
| D5 | EBITDA waterfall (monthly) | P&L CSV + SPY log | `output/pnl_ebitda_monthly.csv` |
| C1 | Chart: EBITDA margin collapse over time | P&L data | `charts/ebitda_trend.png` |
| C2 | Chart: Cost breakdown waterfall | P&L data | `charts/cost_waterfall.png` |
| C3 | Chart: SKU storage burden vs margin | SKU summary | `charts/sku_storage_margin.png` |
| C4 | Chart: Acquisition channel CAC trend | JSON + marketing spend | `charts/channel_cac.png` |
| ETL | Automated pipeline script | All sources | `pipeline/etl_pipeline.py` |

---

## 4. Step-by-Step Execution Plan

### Phase 0: Environment Setup

**What to run:**
```bash
pip install pandas sqlite3 openpyxl matplotlib seaborn jupyter
```

**Directory structure to create:**
```
src/
├── pipeline/
│   ├── etl_pipeline.py        ← main ETL script (raw → clean → final)
│   ├── 01_extract.py          ← load all raw sources
│   ├── 02_transform.py        ← clean, flatten, merge
│   └── 03_load.py             ← write outputs to /output and SQLite
├── analysis/
│   ├── eda.ipynb              ← exploratory notebook
│   └── charts.py              ← chart generation script
└── output/                    ← all final datasets land here
    ├── master_transactions.csv
    ├── customers_by_channel_month.csv
    ├── sku_performance.csv
    ├── cohort_retention.csv
    └── pnl_ebitda_monthly.csv
charts/
├── ebitda_trend.png
├── cost_waterfall.png
├── sku_storage_margin.png
└── channel_cac.png
```

---

### Phase 1: Extract — Load All Raw Sources

**Script: `pipeline/01_extract.py`**

Tasks:
1. Load `zenith_core_db.sqlite` → `df_transactions` (50k rows)
2. Load `customer_profiles_v2.json` → raw dict
3. Load `sku_summary.csv` → `df_sku`
4. Load `monthly_pnl_summary.csv` → `df_pnl`
5. Load `sys_ops_log_archive.sys` → `df_ops` (assign column names manually, separator `~`)
6. Load `marketing_spend_history.xlsx` → `df_marketing`
7. Load `warehouse_rate_card.xlsx` → `df_warehouse`

**Output:** All 7 raw dataframes in memory, ready for transform.

---

### Phase 2: Transform — Clean & Flatten Each Source

**Script: `pipeline/02_transform.py`**

#### 2A — Transactions (`df_transactions`)
- Cast `OrderDate` from string to `datetime`
- Derive `Month` column: `OrderDate.dt.to_period('M')`
- Derive `LineRevenue = Quantity * SellingPrice`
- Derive `LineCOGS = Quantity * CostPrice`
- Derive `LineMargin = LineRevenue - LineCOGS - ShippingCost - PaymentProcessingFee`
- Flag high-cost returns: rows where `ReturnFlag == 1`
- Drop or quarantine rows with null `CustomerID` or `OrderDate`

#### 2B — Customer Profiles JSON (flatten)
- Iterate dict → build list of flat dicts
- Extract `CustomerID` = key stripped of `usr_profile_`
- Extract: `utm_medium`, `macro_region`, `micro_zone`, `primary_goal`, `tier`, `projected_ltv_at_signup_usd`, `return_rate_pct`, `fraud_lock`
- Cast `fraud_lock` to boolean, filter out `fraud_lock == True` customers from main analysis
- Result: `df_customers` (one row per customer)

#### 2C — SKU Summary
- Cast `EcoFriendly` string → boolean
- Rename `GrossMargin%` → `GrossMarginPct`
- Derive `InventoryCostBurden = StorageCostPerUnit * AverageDaysInInventory`
- Flag dead stock: `AverageDaysInInventory > 60` AND `GrossMarginPct < 0.5`

#### 2D — P&L Data
- Parse `Month` to period
- Deduplicate: group by `Month` and **sum** `MonthlyLaborCost` (two supervisors per month need to be combined)
- Derive `EBITDA = GrossRevenue - TotalCOGS - TotalDiscounts - TotalShipping - TotalPaymentFees - MonthlyLaborCost - WarehouseRent`
- Derive `EBITDAMarginPct = EBITDA / GrossRevenue`
- Derive `DiscountRatePct = TotalDiscounts / GrossRevenue`

#### 2E — Ops Log
- Assign column names: `[Month, Supervisor, LaborCost, WarehouseRent, OrdersProcessed, Incidents, ErrorRate, AvgPickTime, AvgPackTime]`
- Parse `Month` to period
- Aggregate per month: sum labour, mean pick/pack times, sum incidents
- Cross-validate `LaborCost` totals against `monthly_pnl_summary` — flag discrepancies

#### 2F — Marketing Spend
- Melt from wide (channel columns) to long format: `[Month, Channel, Spend]`
- Parse `Month` to period

---

### Phase 3: Merge — Build Single Source of Truth

**Script merge logic in `pipeline/02_transform.py` or `etl_pipeline.py`**

**Master join sequence:**
```
df_transactions
  ← LEFT JOIN df_customers ON CustomerID          (adds: channel, tier, region, LTV)
  ← LEFT JOIN df_sku ON ProductID                 (adds: margin%, storage cost, category)
```

Result: `df_master` — one row per transaction line enriched with customer and product dimensions.

**Schema of `df_master`:**

| Column | Source |
|---|---|
| `OrderID` | transactions |
| `OrderDate` | transactions |
| `Month` | derived |
| `CustomerID` | transactions |
| `ProductID` | transactions |
| `Category` | transactions / sku |
| `Region` | transactions |
| `Quantity` | transactions |
| `SellingPrice` | transactions |
| `CostPrice` | transactions |
| `ShippingCost` | transactions |
| `PaymentProcessingFee` | transactions |
| `ReturnFlag` | transactions |
| `LineRevenue` | derived |
| `LineCOGS` | derived |
| `LineMargin` | derived |
| `utm_medium` (AcqChannel) | JSON |
| `macro_region` | JSON |
| `tier` | JSON |
| `projected_ltv` | JSON |
| `GrossMarginPct` | sku |
| `StorageCostPerUnit` | sku |
| `AverageDaysInInventory` | sku |
| `EcoFriendly` | sku |

**Expected row count:** ~50,000 (transaction grain, enriched)

---

### Phase 4: Load — Write Outputs

**Script: `pipeline/03_load.py`**

1. Write `df_master` → `output/master_transactions.csv`
2. Write clean SQLite:
   - `clean.transactions` table
   - `clean.customers` table
   - `clean.skus` table
   - `clean.pnl` table
3. Write all 4 analytical datasets (see Section 5)

---

### Phase 5: Analytical Datasets (Business-Ready Outputs)

#### Dataset 1 — Customers per Month by Acquisition Channel
**Source:** `df_master` grouped by `[Month, utm_medium]`

**Columns:** `Month`, `AcqChannel`, `UniqueCustomers`, `TotalOrders`, `TotalRevenue`, `AvgOrderValue`

**Key insight surfaced:** Which channels drive high volume but low revenue / high churn

---

#### Dataset 2 — Revenue & Margin per SKU
**Source:** `df_master` grouped by `ProductID`, joined with `df_sku`

**Columns:** `ProductID`, `Category`, `TotalRevenue`, `TotalUnits`, `AvgSellingPrice`, `TotalLineMargin`, `GrossMarginPct`, `ReturnRate`, `StorageCostPerUnit`, `InventoryCostBurden`

**Key insight surfaced:** SKUs with high storage burden but thin margin = priority cuts

---

#### Dataset 3 — Cohort Retention / Repeat Purchase
**Source:** `df_master` — first purchase month per customer, count of orders per period

**Columns:** `CohortMonth`, `PeriodsSinceFirst`, `CustomersRetained`, `RetentionRate%`

**Method:**
1. Assign each customer their `FirstOrderMonth`
2. Tag each transaction with `PeriodsSinceFirst = Month - FirstOrderMonth`
3. Pivot to cohort table
4. Divide by cohort size for retention rate

**Key insight surfaced:** Whether the hyper-growth 2021–2022 cohorts were retained or were one-time buyers (major LTV implication)

---

#### Dataset 4 — Monthly EBITDA Waterfall (Bonus — feeds Track B too)
**Source:** `df_pnl` (cleaned)

**Columns:** `Month`, `GrossRevenue`, `afterCOGS`, `afterDiscounts`, `afterShipping`, `afterPaymentFees`, `afterLabor`, `afterWarehouse` (= EBITDA), `EBITDAMarginPct`

**Key insight surfaced:** Exactly where each dollar disappears on the way to EBITDA

---

### Phase 6: Charts

#### Chart 1 — EBITDA Margin Collapse Over Time (Line Chart)
- X: Month | Y: EBITDAMarginPct
- Annotate the inflection point where margin turned negative
- Connecting narrative: "Revenue grew but margin collapsed — this is not a revenue problem"

#### Chart 2 — Cost Waterfall (Bar/Waterfall Chart)
- Bars: GrossRevenue → -COGS → -Discounts → -Shipping → -PaymentFees → -Labor → -Warehouse = EBITDA
- Most recent full year or worst quarter
- Connecting narrative: "Discounts + Labour are the two largest addressable leaks"

#### Chart 3 — SKU Scatter: Storage Burden vs Gross Margin
- X: `InventoryCostBurden` | Y: `GrossMarginPct` | Size: `TotalRevenue` | Color: `Category`
- Quadrants: top-left = stars, bottom-right = dead weight
- Connecting narrative: "15–20 SKUs are destroying margin per unit while tying up warehouse space"

#### Chart 4 — CAC Trend by Channel (Stacked Bar or Line)
- X: Month | Y: New Customers per Channel | Secondary Y: Spend per Channel
- Derived CAC = `ChannelSpend / NewCustomersFromChannel`
- Connecting narrative: "Paid Social CAC has been rising while retention hasn't — we are buying customers who don't come back"

---

### Phase 7: ETL Pipeline (Differentiator)

**Script: `pipeline/etl_pipeline.py`**

This is a single callable script that:
1. Reads all 7 raw sources from `encoded_data/`
2. Runs all transformations (Phases 2A–2F)
3. Runs the master join (Phase 3)
4. Writes all outputs to `output/` and SQLite (Phase 4)
5. Generates all 4 charts to `charts/`
6. Prints a run summary: row counts, null counts, output file sizes

**Run command:**
```bash
python src/pipeline/etl_pipeline.py
```

**Pipeline flow diagram:**
```
RAW SOURCES                   TRANSFORM                   OUTPUTS
─────────────────────         ──────────────────────      ──────────────────────────
zenith_core_db.sqlite  ──→    parse dates, derive         master_transactions.csv
customer_profiles.json ──→    flatten JSON, filter   ──→  customers_by_channel.csv
sku_summary.csv        ──→    cast types, flag SKUs        sku_performance.csv
monthly_pnl.csv        ──→    dedup, derive EBITDA    ──→  pnl_ebitda_monthly.csv
sys_ops_log.sys        ──→    assign headers, agg          cohort_retention.csv
marketing_spend.xlsx   ──→    melt to long format    ──→   charts/ (4 PNG files)
warehouse_rate.xlsx    ──→    rate lookups                 clean_analytics.sqlite
```

---

## 5. Key Data Quality Issues Summary

| Issue | Source | Handling |
|---|---|---|
| Duplicate month rows | `monthly_pnl_summary.csv` (two supervisors) | Sum labour per month |
| TEXT dates | `transactions_master.OrderDate` | `pd.to_datetime()` |
| Nested JSON (4 levels deep) | `customer_profiles_v2.json` | Recursive flatten |
| No header, tilde delimiter | `sys_ops_log_archive.sys` | Manual column assignment |
| `GrossMargin%` as decimal string | `sku_summary.csv` | Cast to float, rename |
| `EcoFriendly` as `"True"`/`"False"` string | `sku_summary.csv` | `map({'True': True})` |
| Fraud-locked customers | `customer_profiles_v2.json` | Filter from main analysis |
| `Transaction_Log` blob column | `transactions_master` | Inspect & decide — drop or parse |
| Left join nulls (customers missing from JSON) | merge step | Track unmatched rate |

---

## 6. Narrative Connection to Profitability Crisis

Every deliverable must be tied back to the core problem statement:

> "EBITDA has collapsed to near-zero despite high top-line revenue."

| Deliverable | Business question it answers |
|---|---|
| EBITDA waterfall dataset + chart | Where exactly does each revenue dollar disappear? |
| SKU performance dataset + chart | Which products are eating margin through storage & returns? |
| Channel cohort retention | Are we spending more to acquire customers who don't come back? |
| Customers by channel/month | Is our growth buying the wrong customers? |
| Ops log analysis | Is warehouse operational inefficiency showing up in labour cost trends? |

---

## 7. Python Libraries Required

```
pandas          # DataFrames, CSV, groupby, merge
sqlite3         # Read zenith_core_db.sqlite (stdlib)
json            # Parse customer_profiles_v2.json (stdlib)
openpyxl        # Read .xlsx files
matplotlib      # Base charting
seaborn         # Statistical charts (scatter, trends)
pathlib         # File path management (stdlib)
```

**Install command:**
```bash
pip install pandas openpyxl matplotlib seaborn
```

---

## 8. Presentation Talking Points (from Track A)

1. **The chaos problem:** 7 incompatible sources, no single truth — this alone prevents any informed decision-making
2. **What the data shows:** EBITDA margin has been negative/near-zero since [X month] — we can pinpoint the exact cost that tipped it
3. **The SKU problem:** ~20% of SKUs carry disproportionate storage cost with thin margins — immediate cuts would recover margin
4. **The acquisition problem:** Paid Social is the dominant channel but cohort retention from those customers is the weakest — we are spending to grow ourselves backward
5. **What we built:** A reproducible pipeline — anyone can re-run it with updated data in one command; this is the foundation the board needs to make data-driven decisions going forward

---

*Plan version: 2026-03-22 | Track A | Zenith Active Solutions Assessment*
