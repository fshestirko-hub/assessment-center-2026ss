"""
transactions_extractor.py
--------------------------
Loads the core transaction ledger from the SQLite database.

Source: zenith_core_db.sqlite → table: transactions_master (50,000 rows)

Cleaning steps performed here:
  - Parse OrderDate from TEXT to datetime
  - Add a Month column (YYYY-MM period string) for time-based grouping
  - Derive per-line financial figures (revenue, COGS, margin)
  - Keep ReturnFlag as-is (0/1 integer) — consumers can filter as needed
"""

import sqlite3
from pathlib import Path

import pandas as pd

from base_extractor import BaseExtractor


class TransactionsExtractor(BaseExtractor):
    """Extracts and cleans the transactions_master table from SQLite."""

    TABLE_NAME = "transactions_master"

    def extract(self) -> pd.DataFrame:
        connection = sqlite3.connect(self.file_path)
        df = pd.read_sql_query(f"SELECT * FROM {self.TABLE_NAME}", connection)
        connection.close()

        df = self._parse_dates(df)
        df = self._add_month_column(df)
        df = self._derive_financials(df)
        df = self._drop_invalid_rows(df)

        return df

    # ------------------------------------------------------------------
    # Private helpers — each does one thing
    # ------------------------------------------------------------------

    def _parse_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cast OrderDate from TEXT to datetime so date math works."""
        df["OrderDate"] = pd.to_datetime(df["OrderDate"], errors="coerce")
        return df

    def _add_month_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add a Month column (e.g. '2023-04') for time-based grouping."""
        df["Month"] = df["OrderDate"].dt.to_period("M").astype(str)
        return df

    def _derive_financials(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate per-transaction-line financial figures.
        These are the building blocks for every downstream analysis.
        """
        df["LineRevenue"] = df["Quantity"] * df["SellingPrice"]
        df["LineCOGS"]    = df["Quantity"] * df["CostPrice"]
        df["LineMargin"]  = (
            df["LineRevenue"]
            - df["LineCOGS"]
            - df["ShippingCost"]
            - df["PaymentProcessingFee"]
        )
        return df

    def _drop_invalid_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove rows that cannot be used for analysis:
          - Missing CustomerID means we cannot join to customer profiles
          - Missing OrderDate means we cannot place the order in time
        """
        before = len(df)
        df = df.dropna(subset=["CustomerID", "OrderDate"])
        dropped = before - len(df)

        if dropped > 0:
            print(f"[TransactionsExtractor] Dropped {dropped} rows with null CustomerID or OrderDate")

        return df
