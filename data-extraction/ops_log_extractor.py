"""
ops_log_extractor.py
---------------------
Loads and parses the non-standard warehouse operations log.

Source: sys_ops_log_archive.sys

Format quirks:
  - Tilde (~) delimited, NOT comma-separated
  - NO header row — columns are inferred by position
  - Multiple rows per month (one per shift supervisor)

Example raw row:
  2022-01~M. Johnson~48375~25000~96~0~0.013~3.1~45.2

Column mapping (positional):
  0 → Month             (YYYY-MM)
  1 → Supervisor        (name string)
  2 → LaborCost         (USD)
  3 → WarehouseRent     (USD — should match PnL; used for cross-validation)
  4 → OrdersProcessed   (count)
  5 → Incidents         (count of errors/issues)
  6 → ErrorRate         (decimal, e.g. 0.013 = 1.3%)
  7 → AvgPickTimeMin    (minutes per pick)
  8 → AvgPackTimeMin    (minutes per pack)

Cleaning steps:
  - Assign column names manually (no header in file)
  - Aggregate per month: sum labour/orders/incidents, average pick/pack times
  - This gives one clean row per month, consistent with the P&L data
"""

from pathlib import Path

import pandas as pd

from base_extractor import BaseExtractor
from config import OPS_LOG_COLUMNS, OPS_LOG_SEPARATOR


class OpsLogExtractor(BaseExtractor):
    """Parses the tilde-delimited ops log and aggregates to monthly level."""

    def extract(self) -> pd.DataFrame:
        df = self._load_raw()
        df = self._aggregate_to_monthly(df)
        return df

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_raw(self) -> pd.DataFrame:
        """
        Read the file with an explicit separator and manually assign
        column names since the file has no header row.
        """
        df = pd.read_csv(
            self.file_path,
            sep=OPS_LOG_SEPARATOR,
            header=None,           # file has no header
            names=OPS_LOG_COLUMNS, # assign names from config
            engine="python",       # needed for multi-char or regex separators
        )

        # Strip any accidental whitespace around values (the tilde format is messy)
        df["Month"]      = df["Month"].str.strip()
        df["Supervisor"] = df["Supervisor"].str.strip()

        return df

    def _aggregate_to_monthly(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Multiple supervisors log entries for the same month.
        We collapse to one row per month so this can join to the P&L.

          - LaborCost, OrdersProcessed, Incidents → SUM (they are counts/totals)
          - AvgPickTimeMin, AvgPackTimeMin, ErrorRate → MEAN (they are rates/averages)
          - WarehouseRent → MAX (it's the same fixed value per month, any row works)
        """
        df_monthly = df.groupby("Month", as_index=False).agg(
            TotalLaborCost      = ("LaborCost",       "sum"),
            WarehouseRent       = ("WarehouseRent",   "max"),
            TotalOrdersProcessed = ("OrdersProcessed", "sum"),
            TotalIncidents      = ("Incidents",       "sum"),
            AvgErrorRate        = ("ErrorRate",       "mean"),
            AvgPickTimeMin      = ("AvgPickTimeMin",  "mean"),
            AvgPackTimeMin      = ("AvgPackTimeMin",  "mean"),
        )

        return df_monthly
