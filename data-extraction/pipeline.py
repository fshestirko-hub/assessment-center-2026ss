"""
pipeline.py
------------
Orchestrates the entire ETL process from raw files → Single Source of Truth.

This is the only file that knows about all the extractors and the merger.

--- SETUP (first time on any machine) ---

    pip install -r requirements.txt          # from the project root

--- RUNNING THE PIPELINE ---

From the project root:
    python3 data-extraction/pipeline.py

From inside the data-extraction/ folder:
    python3 pipeline.py

Both work — all paths are anchored to __file__ so the working directory
does not matter.

What it does (in order):
  1. Extracts each raw source using its dedicated extractor class
  2. Saves each cleaned source to output/ as individual CSVs
  3. Merges transactions + customers + SKUs into the master dataset
  4. Saves the master dataset as both CSV and JSON
  5. Generates 3 business-ready analytical datasets from the master

Each step prints progress so you can see where it is and catch errors early.
"""

import sys
from pathlib import Path

# Make sure imports work when running this file directly
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd

from config import (
    SQLITE_PATH, CUSTOMERS_JSON_PATH, SKU_CSV_PATH, PNL_CSV_PATH,
    OPS_LOG_PATH, MARKETING_XLSX_PATH, WAREHOUSE_XLSX_PATH,
    OUTPUT_DIR,
    MASTER_CSV_PATH, MASTER_JSON_PATH,
    CUSTOMERS_CLEAN_CSV_PATH, SKU_CLEAN_CSV_PATH,
    PNL_CLEAN_CSV_PATH, OPS_CLEAN_CSV_PATH, MARKETING_CLEAN_CSV_PATH,
    WAREHOUSE_CLEAN_CSV_PATH,
    CUSTOMERS_BY_CHANNEL_PATH, SKU_PERFORMANCE_PATH, COHORT_RETENTION_PATH,
)

from transactions_extractor import TransactionsExtractor
from customer_extractor      import CustomerExtractor
from sku_extractor           import SkuExtractor
from pnl_extractor           import PnlExtractor
from ops_log_extractor       import OpsLogExtractor
from marketing_extractor     import MarketingExtractor
from warehouse_extractor     import WarehouseExtractor
from merger                  import Merger
from analytics               import Analytics


def run_pipeline():
    """
    Full ETL from raw files to Single Source of Truth.
    Called when this script is run directly.
    """

    # Ensure the output directory exists before we try to write anything
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Step 1: Extract & clean each source
    # ------------------------------------------------------------------

    print("=" * 60)
    print("ZENITH ACTIVE SOLUTIONS — ETL PIPELINE")
    print("=" * 60)

    print("\n[1/7] Loading transactions from SQLite...")
    df_transactions = TransactionsExtractor(SQLITE_PATH).extract()
    print(f"      → {len(df_transactions):,} rows loaded")

    print("\n[2/7] Loading and flattening customer profiles from JSON...")
    df_customers = CustomerExtractor(CUSTOMERS_JSON_PATH).extract()
    print(f"      → {len(df_customers):,} customer profiles loaded")

    print("\n[3/7] Loading SKU catalog from CSV...")
    df_skus = SkuExtractor(SKU_CSV_PATH).extract()
    print(f"      → {len(df_skus):,} SKUs loaded")

    print("\n[4/7] Loading P&L summary from CSV...")
    df_pnl = PnlExtractor(PNL_CSV_PATH).extract()
    print(f"      → {len(df_pnl):,} monthly P&L rows loaded")

    print("\n[5/7] Loading ops log from .sys file...")
    df_ops = OpsLogExtractor(OPS_LOG_PATH).extract()
    print(f"      → {len(df_ops):,} monthly ops rows loaded")

    print("\n[6/7] Loading marketing spend from Excel...")
    df_marketing = MarketingExtractor(MARKETING_XLSX_PATH).extract()
    print(f"      → {len(df_marketing):,} channel-month rows loaded")

    print("\n[7/7] Loading warehouse rate card from Excel...")
    df_warehouse = WarehouseExtractor(WAREHOUSE_XLSX_PATH).extract()
    print(f"      → {len(df_warehouse):,} rate card rows loaded")

    # ------------------------------------------------------------------
    # Step 2: Save each clean source to output/ as a CSV
    # Individual clean files are useful for the analysis notebooks and
    # for other teams (Track B, Track C) who need specific datasets.
    # ------------------------------------------------------------------

    print("\n--- Saving individual clean datasets ---")

    _save(df_transactions, CUSTOMERS_CLEAN_CSV_PATH.parent / "transactions_clean.csv")
    _save(df_customers,    CUSTOMERS_CLEAN_CSV_PATH)
    _save(df_skus,         SKU_CLEAN_CSV_PATH)
    _save(df_pnl,          PNL_CLEAN_CSV_PATH)
    _save(df_ops,          OPS_CLEAN_CSV_PATH)
    _save(df_marketing,    MARKETING_CLEAN_CSV_PATH)
    _save(df_warehouse,    WAREHOUSE_CLEAN_CSV_PATH)

    # ------------------------------------------------------------------
    # Step 3: Build the Single Source of Truth (master dataset)
    # ------------------------------------------------------------------

    print("\n--- Building Single Source of Truth ---")
    merger = Merger()
    df_master = merger.build_master(df_transactions, df_customers, df_skus)

    # ------------------------------------------------------------------
    # Step 4: Save the master dataset as CSV and JSON
    # JSON is required by Track A spec and useful for front-end / BI tools.
    # ------------------------------------------------------------------

    _save(df_master, MASTER_CSV_PATH)
    _save_json(df_master, MASTER_JSON_PATH)

    # ------------------------------------------------------------------
    # Step 5: Generate the 3 business-ready analytical datasets
    # These answer specific business questions directly from the master.
    # ------------------------------------------------------------------

    print("\n--- Building analytical datasets ---")
    analytics = Analytics()

    df_by_channel = analytics.customers_by_channel_month(df_master)
    _save(df_by_channel, CUSTOMERS_BY_CHANNEL_PATH)

    df_sku_perf = analytics.sku_performance(df_master)
    _save(df_sku_perf, SKU_PERFORMANCE_PATH)

    df_cohort = analytics.cohort_retention(df_master)
    _save(df_cohort, COHORT_RETENTION_PATH)

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print(f"Master dataset (CSV):  {MASTER_CSV_PATH}")
    print(f"Master dataset (JSON): {MASTER_JSON_PATH}")
    print(f"All outputs saved to:  {OUTPUT_DIR}")
    print("=" * 60)

    return df_master, df_pnl, df_ops, df_marketing, df_warehouse


# ------------------------------------------------------------------
# Utility
# ------------------------------------------------------------------

def _save(df: pd.DataFrame, path: Path) -> None:
    """Save a DataFrame to CSV and print confirmation."""
    df.to_csv(path, index=False)
    print(f"  ✓ Saved {path.name}  ({len(df):,} rows)")


def _save_json(df: pd.DataFrame, path: Path) -> None:
    """
    Save a DataFrame to JSON (records orientation).
    Each element in the JSON array is one transaction row — easy to
    consume by any BI tool, API, or front-end without extra parsing.
    """
    df.to_json(path, orient="records", indent=2, force_ascii=False)
    size_mb = path.stat().st_size / (1024 * 1024)
    print(f"  ✓ Saved {path.name}  ({len(df):,} rows, {size_mb:.1f} MB)")


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    run_pipeline()
