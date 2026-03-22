"""
sku_extractor.py
-----------------
Loads and cleans the SKU product catalog.

Source: sku_summary.csv

Cleaning steps performed here:
  - Cast EcoFriendly from string ("True"/"False") to proper boolean
  - Rename "GrossMargin%" → GrossMarginPct (avoids the % in column names)
  - Derive InventoryCostBurden = StorageCostPerUnit × AverageDaysInInventory
    This is a compound signal: a SKU sitting in the warehouse a long time AND
    costing a lot to store is the worst case for margin.
  - Flag dead-stock SKUs: high inventory age + low margin
"""

from pathlib import Path

import pandas as pd

from base_extractor import BaseExtractor


class SkuExtractor(BaseExtractor):
    """Extracts and enriches the SKU product catalog from CSV."""

    # A SKU is flagged as dead stock if it exceeds both thresholds.
    DEAD_STOCK_DAYS_THRESHOLD   = 60    # days sitting in inventory
    DEAD_STOCK_MARGIN_THRESHOLD = 0.50  # gross margin below 50%

    def extract(self) -> pd.DataFrame:
        df = pd.read_csv(self.file_path)

        df = self._rename_margin_column(df)
        df = self._cast_eco_friendly(df)
        df = self._derive_inventory_cost_burden(df)
        df = self._flag_dead_stock(df)

        return df

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _rename_margin_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rename 'GrossMargin%' to 'GrossMarginPct' — the % sign in a column
        name causes issues with many tools and is easy to misread."""
        df = df.rename(columns={"GrossMargin%": "GrossMarginPct"})
        return df

    def _cast_eco_friendly(self, df: pd.DataFrame) -> pd.DataFrame:
        """The CSV stores True/False as plain strings. Cast to actual booleans."""
        df["EcoFriendly"] = df["EcoFriendly"].map({"True": True, "False": False})
        return df

    def _derive_inventory_cost_burden(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        InventoryCostBurden = StorageCostPerUnit × AverageDaysInInventory

        This tells us the total storage spend per unit from when it arrives
        until it sells. A high value here is a direct margin killer.
        """
        df["InventoryCostBurden"] = df["StorageCostPerUnit"] * df["AverageDaysInInventory"]
        return df

    def _flag_dead_stock(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Mark SKUs that are both slow-moving AND low-margin.
        These are the first candidates for discontinuation or clearance.
        """
        is_slow_moving = df["AverageDaysInInventory"] > self.DEAD_STOCK_DAYS_THRESHOLD
        is_low_margin  = df["GrossMarginPct"] < self.DEAD_STOCK_MARGIN_THRESHOLD
        df["IsDeadStock"] = is_slow_moving & is_low_margin
        return df
