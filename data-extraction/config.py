"""
config.py
---------
Single place for all file paths and constants.
If a path changes, you only update it here.
"""

from pathlib import Path

# Root of the project (one level up from data-extraction/)
PROJECT_ROOT = Path(__file__).parent.parent

# Raw source files
RAW_DATA_DIR = PROJECT_ROOT / "encoded_data"

SQLITE_PATH          = RAW_DATA_DIR / "zenith_core_db.sqlite"
CUSTOMERS_JSON_PATH  = RAW_DATA_DIR / "customer_profiles_v2.json"
SKU_CSV_PATH         = RAW_DATA_DIR / "sku_summary.csv"
PNL_CSV_PATH         = RAW_DATA_DIR / "monthly_pnl_summary.csv"
OPS_LOG_PATH         = RAW_DATA_DIR / "sys_ops_log_archive.sys"
MARKETING_XLSX_PATH  = RAW_DATA_DIR / "marketing_spend_history.xlsx"
WAREHOUSE_XLSX_PATH  = RAW_DATA_DIR / "warehouse_rate_card.xlsx"

# Output destinations
OUTPUT_DIR = PROJECT_ROOT / "data-extraction" / "output"

MASTER_CSV_PATH              = OUTPUT_DIR / "master_transactions.csv"
MASTER_JSON_PATH             = OUTPUT_DIR / "master_transactions.json"
CUSTOMERS_CLEAN_CSV_PATH     = OUTPUT_DIR / "customers_clean.csv"
SKU_CLEAN_CSV_PATH           = OUTPUT_DIR / "sku_clean.csv"
PNL_CLEAN_CSV_PATH           = OUTPUT_DIR / "pnl_clean.csv"
OPS_CLEAN_CSV_PATH           = OUTPUT_DIR / "ops_clean.csv"
MARKETING_CLEAN_CSV_PATH     = OUTPUT_DIR / "marketing_clean.csv"
WAREHOUSE_CLEAN_CSV_PATH     = OUTPUT_DIR / "warehouse_clean.csv"

# Business-ready analytical datasets (derived from the master)
CUSTOMERS_BY_CHANNEL_PATH    = OUTPUT_DIR / "analytics_customers_by_channel_month.csv"
SKU_PERFORMANCE_PATH         = OUTPUT_DIR / "analytics_sku_performance.csv"
COHORT_RETENTION_PATH        = OUTPUT_DIR / "analytics_cohort_retention.csv"

# The ops log uses tilde as a separator and has no header row.
# Column names are assigned based on manual inspection of the file.
OPS_LOG_SEPARATOR = "~"
OPS_LOG_COLUMNS = [
    "Month",
    "Supervisor",
    "LaborCost",
    "WarehouseRent",
    "OrdersProcessed",
    "Incidents",
    "ErrorRate",
    "AvgPickTimeMin",
    "AvgPackTimeMin",
]
