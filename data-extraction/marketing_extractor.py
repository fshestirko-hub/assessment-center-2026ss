"""
marketing_extractor.py
-----------------------
Loads the monthly marketing spend breakdown by channel.

Source: marketing_spend_history.xlsx

The Excel file is already in long format:
  Month   | Channel      | AdSpend
  2022-01 | Paid Social  | 14510.18
  2022-01 | Organic      | 1395.07
  ...

Some months have duplicate rows for the same channel (multiple submissions).
We aggregate by summing AdSpend per Month + Channel.

Cleaning steps:
  - Strip whitespace from column names and string values
  - Rename AdSpend → Spend for a consistent name across the project
  - Sum duplicate rows (same Month + Channel) into one row
  - Drop rows where Spend is null

Output schema:
  Month, Channel, Spend
"""

from pathlib import Path

import pandas as pd

from base_extractor import BaseExtractor


class MarketingExtractor(BaseExtractor):
    """Loads the marketing spend Excel file (already in long format)."""

    def extract(self) -> pd.DataFrame:
        df = pd.read_excel(self.file_path)

        df = self._clean_column_names(df)
        df = self._clean_string_values(df)
        df = self._rename_spend_column(df)
        df = self._aggregate_duplicates(df)
        df = self._drop_empty_rows(df)

        return df

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Excel files often have invisible trailing spaces in headers."""
        df.columns = df.columns.str.strip()
        return df

    def _clean_string_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Strip whitespace from text columns so joins work correctly."""
        if "Channel" in df.columns:
            df["Channel"] = df["Channel"].str.strip()
        if "Month" in df.columns:
            df["Month"] = df["Month"].astype(str).str.strip()
        return df

    def _rename_spend_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """The Excel calls the column 'AdSpend'. Rename to 'Spend' for
        a consistent name across all datasets in this project."""
        df = df.rename(columns={"AdSpend": "Spend"})
        return df

    def _aggregate_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Some months have multiple rows for the same channel.
        Sum them so there is exactly one row per Month + Channel combination.
        """
        df = df.groupby(["Month", "Channel"], as_index=False).agg(Spend=("Spend", "sum"))
        return df

    def _drop_empty_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove rows where Spend is missing — likely blank spreadsheet rows."""
        before = len(df)
        df = df.dropna(subset=["Spend"])
        dropped = before - len(df)
        if dropped > 0:
            print(f"[MarketingExtractor] Dropped {dropped} rows with null Spend")
        return df
