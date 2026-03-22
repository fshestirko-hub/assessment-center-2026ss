"""
pnl_extractor.py
-----------------
Loads and cleans the monthly profit & loss summary.

Source: monthly_pnl_summary.csv

Known issues handled here:
  - Month 2022-01 appears TWICE (two different shift supervisors filed it).
    The fix: group by Month and sum the labour/numeric columns so each
    month becomes one row. All other columns are identical per group.
  - EBITDA is not in the file — we derive it step by step so the waterfall
    is transparent (each step shows one cost being subtracted).
  - Discount rate as a percentage of revenue is also derived here because
    it is a cleaner signal than the raw discount dollar amount.
"""

from pathlib import Path

import pandas as pd

from base_extractor import BaseExtractor


class PnlExtractor(BaseExtractor):
    """Extracts, deduplicates, and enriches the monthly P&L CSV."""

    def extract(self) -> pd.DataFrame:
        df = pd.read_csv(self.file_path)

        df = self._deduplicate_months(df)
        df = self._derive_ebitda_waterfall(df)
        df = self._derive_ratios(df)

        return df

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _deduplicate_months(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Some months have two rows because different supervisors submitted
        separate records for the same month. Summing all numeric columns
        per month collapses them into one correct row.
        """
        # Sum every numeric column grouped by Month.
        # Non-numeric columns are dropped automatically by groupby + sum.
        df = df.groupby("Month", as_index=False).sum(numeric_only=True)
        return df

    def _derive_ebitda_waterfall(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Build a step-by-step EBITDA waterfall so we can see exactly where
        each dollar of gross revenue is consumed.

        Each column = revenue remaining AFTER subtracting that cost line.
        """
        df["AfterCOGS"]        = df["GrossRevenue"]     - df["TotalCOGS"]
        df["AfterDiscounts"]   = df["AfterCOGS"]         - df["TotalDiscounts"]
        df["AfterShipping"]    = df["AfterDiscounts"]    - df["TotalShipping"]
        df["AfterPaymentFees"] = df["AfterShipping"]     - df["TotalPaymentFees"]
        df["AfterLabor"]       = df["AfterPaymentFees"]  - df["MonthlyLaborCost"]
        df["EBITDA"]           = df["AfterLabor"]        - df["WarehouseRent"]
        return df

    def _derive_ratios(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Percentage metrics give a sense of scale regardless of revenue size.
        Useful for trend charts where absolute dollar amounts change.
        """
        df["EBITDAMarginPct"]  = df["EBITDA"]          / df["GrossRevenue"]
        df["DiscountRatePct"]  = df["TotalDiscounts"]   / df["GrossRevenue"]
        df["COGSRatePct"]      = df["TotalCOGS"]        / df["GrossRevenue"]
        df["LaborRatePct"]     = df["MonthlyLaborCost"] / df["GrossRevenue"]
        return df
