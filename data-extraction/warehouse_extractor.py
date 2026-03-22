"""
warehouse_extractor.py
-----------------------
Loads the warehouse storage rate card.

Source: warehouse_rate_card.xlsx

This file contains the vendor's storage cost schedule by product category.
It is used to cross-reference and validate the StorageCostPerUnit figures
found in sku_summary.csv.

Expected format:
  Category | StorageRatePerUnitPerDay | Notes (or similar)

Cleaning steps:
  - Strip whitespace from column names
  - Ensure Category values match the categories in sku_summary.csv
    so joins work correctly (case-normalised to title case)
"""

from pathlib import Path

import pandas as pd

from base_extractor import BaseExtractor


class WarehouseExtractor(BaseExtractor):
    """Loads the warehouse vendor rate card from Excel."""

    def extract(self) -> pd.DataFrame:
        df = pd.read_excel(self.file_path)

        df = self._clean_column_names(df)
        df = self._normalise_category(df)

        return df

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove trailing/leading spaces from Excel header cells."""
        df.columns = df.columns.str.strip()
        return df

    def _normalise_category(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Category names must match those in sku_summary.csv exactly
        for joins to work. Title-casing both sides is the safest approach.
        """
        if "Category" in df.columns:
            df["Category"] = df["Category"].str.strip().str.title()
        return df
