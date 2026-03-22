"""
merger.py
----------
Combines all cleaned DataFrames into the Single Source of Truth (SSoT).

This class only does joins — it does NOT load files or clean data.
Each extractor is responsible for cleaning its own source.
The merger trusts that the DataFrames it receives are already clean.

Join strategy:
  transactions
    LEFT JOIN customers  ON CustomerID    → adds channel, tier, region, LTV
    LEFT JOIN skus       ON ProductID     → adds margin %, storage cost, category

LEFT JOINs are used throughout so we never silently lose transaction rows.
If a transaction has no matching customer profile or SKU record, the
transaction row is kept and the enrichment columns will be null.
We log how many nulls result so data quality is visible.

Output: df_master — one row per transaction line, fully enriched.
This is the table every downstream analysis and chart builds from.
"""

import pandas as pd


class Merger:
    """Merges cleaned DataFrames into a single enriched master dataset."""

    def build_master(
        self,
        df_transactions: pd.DataFrame,
        df_customers: pd.DataFrame,
        df_skus: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Produces the Single Source of Truth by enriching each transaction
        row with customer attributes and product/SKU attributes.

        Parameters
        ----------
        df_transactions : cleaned transactions from TransactionsExtractor
        df_customers    : flattened customers from CustomerExtractor
        df_skus         : enriched SKU catalog from SkuExtractor

        Returns
        -------
        pd.DataFrame with ~50,000 rows and all enrichment columns attached
        """

        # Step 1: add customer attributes to each transaction
        df = self._join_customers(df_transactions, df_customers)

        # Step 2: add product attributes to each transaction
        df = self._join_skus(df, df_skus)

        # Step 3: report on join quality so we can spot problems early
        self._report_null_counts(df)

        return df

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _join_customers(
        self,
        df_transactions: pd.DataFrame,
        df_customers: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Left join transactions → customers on CustomerID.
        We keep all transactions even if no matching customer profile exists.
        """
        df = df_transactions.merge(
            df_customers,
            on="CustomerID",
            how="left",
            suffixes=("", "_customer"),
        )
        return df

    def _join_skus(
        self,
        df: pd.DataFrame,
        df_skus: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Left join the working DataFrame → SKU catalog on ProductID.
        We keep all transactions even if no matching SKU record exists.
        """
        # Only bring in the SKU attributes we want — avoid column name clashes
        # with columns that already exist from the transactions table (e.g. Category).
        sku_columns_to_add = [
            "ProductID",
            "GrossMarginPct",
            "StorageCostPerUnit",
            "AverageDaysInInventory",
            "InventoryCostBurden",
            "ReturnRate",
            "EcoFriendly",
            "IsDeadStock",
        ]
        df_skus_slim = df_skus[sku_columns_to_add]

        df = df.merge(
            df_skus_slim,
            on="ProductID",
            how="left",
            suffixes=("", "_sku"),
        )
        return df

    def _report_null_counts(self, df: pd.DataFrame) -> None:
        """
        Print a summary of null values in the key enrichment columns.
        A high null count in AcqChannel or GrossMarginPct means the join
        didn't work well and we should investigate.
        """
        key_columns = ["AcqChannel", "LoyaltyTier", "GrossMarginPct", "InventoryCostBurden"]

        print("\n[Merger] Join quality report — null counts in enrichment columns:")
        for col in key_columns:
            if col in df.columns:
                null_count = df[col].isna().sum()
                null_pct   = 100 * null_count / len(df)
                print(f"  {col:<25}: {null_count:>6} nulls  ({null_pct:.1f}%)")

        print(f"\n[Merger] Master dataset: {len(df):,} rows × {len(df.columns)} columns")
