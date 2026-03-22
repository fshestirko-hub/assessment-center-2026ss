"""
analytics.py
-------------
Produces the three business-ready analytical datasets required by Track A.
All three are derived from df_master — the Single Source of Truth.

Why a separate file?
  - pipeline.py handles raw → clean → merge
  - analytics.py handles clean master → business questions
  - Keeping them separate means you can re-run just the analytics
    without re-extracting all raw sources

Datasets produced:
  1. Customers per month by acquisition channel
  2. SKU performance (revenue, margin, return rate, storage burden)
  3. Cohort retention (repeat purchase behaviour over time)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd


class Analytics:
    """
    Generates business-ready summary datasets from the master transaction table.
    Each method takes df_master and returns a clean, aggregated DataFrame.
    """

    # ------------------------------------------------------------------
    # Dataset 1: Customers per month by acquisition channel
    # ------------------------------------------------------------------

    def customers_by_channel_month(self, df_master: pd.DataFrame) -> pd.DataFrame:
        """
        Answers: which channels are acquiring customers, and are those
        customers spending? High volume channels with low AOV are a red flag.

        Grain: one row per Month + AcqChannel combination.

        Columns produced:
          Month, AcqChannel, UniqueCustomers, TotalOrders,
          TotalRevenue, AvgOrderValue, AvgProjectedLTV
        """
        df = (
            df_master
            .groupby(["Month", "AcqChannel"])
            .agg(
                UniqueCustomers = ("CustomerID",    "nunique"),
                TotalOrders     = ("OrderID",       "nunique"),
                TotalRevenue    = ("LineRevenue",   "sum"),
                AvgProjectedLTV = ("ProjectedLTV",  "mean"),
            )
            .reset_index()
        )

        # Average order value = total revenue ÷ number of orders
        df["AvgOrderValue"] = df["TotalRevenue"] / df["TotalOrders"]

        # Round for readability
        df["TotalRevenue"]    = df["TotalRevenue"].round(2)
        df["AvgOrderValue"]   = df["AvgOrderValue"].round(2)
        df["AvgProjectedLTV"] = df["AvgProjectedLTV"].round(2)

        df = df.sort_values(["Month", "AcqChannel"]).reset_index(drop=True)
        return df

    # ------------------------------------------------------------------
    # Dataset 2: SKU performance
    # ------------------------------------------------------------------

    def sku_performance(self, df_master: pd.DataFrame) -> pd.DataFrame:
        """
        Answers: which products make money and which destroy it?
        Combines transaction-level actuals with the SKU catalog attributes.

        Grain: one row per ProductID.

        Columns produced:
          ProductID, Category, TotalRevenue, TotalUnitsSold,
          TotalLineMargin, AvgSellingPrice, GrossMarginPct,
          ReturnRate, StorageCostPerUnit, InventoryCostBurden,
          IsDeadStock, ReturnedOrders
        """
        df = (
            df_master
            .groupby(["ProductID", "Category"])
            .agg(
                TotalRevenue        = ("LineRevenue",         "sum"),
                TotalUnitsSold      = ("Quantity",            "sum"),
                TotalLineMargin     = ("LineMargin",          "sum"),
                AvgSellingPrice     = ("SellingPrice",        "mean"),
                ReturnedOrders      = ("ReturnFlag",          "sum"),
                TotalOrders         = ("OrderID",             "nunique"),
                # These are SKU-level attributes — same value on every row for
                # a given ProductID, so taking the first value is correct.
                GrossMarginPct      = ("GrossMarginPct",      "first"),
                ReturnRate          = ("ReturnRate",          "first"),
                StorageCostPerUnit  = ("StorageCostPerUnit",  "first"),
                InventoryCostBurden = ("InventoryCostBurden", "first"),
                IsDeadStock         = ("IsDeadStock",         "first"),
            )
            .reset_index()
        )

        df["AvgSellingPrice"] = df["AvgSellingPrice"].round(2)
        df["TotalRevenue"]    = df["TotalRevenue"].round(2)
        df["TotalLineMargin"] = df["TotalLineMargin"].round(2)

        df = df.sort_values("TotalRevenue", ascending=False).reset_index(drop=True)
        return df

    # ------------------------------------------------------------------
    # Dataset 3: Cohort retention
    # ------------------------------------------------------------------

    def cohort_retention(self, df_master: pd.DataFrame) -> pd.DataFrame:
        """
        Answers: do customers come back after their first purchase?
        Cohort analysis is the clearest signal of whether the business
        model is sustainable or relying on constant new acquisition.

        Method:
          1. For each customer, find their first order month (CohortMonth)
          2. For each subsequent order, calculate how many months later it was
          3. Pivot into a retention table: rows = cohort, cols = months since first

        Grain: one row per CohortMonth + MonthsLater combination.

        Columns produced:
          CohortMonth, MonthsLater, CustomersActive, CohortSize, RetentionRate
        """
        # Step 1: find each customer's first purchase month
        first_order = (
            df_master
            .groupby("CustomerID")["Month"]
            .min()
            .rename("CohortMonth")
            .reset_index()
        )

        # Step 2: attach CohortMonth to every transaction
        df = df_master.merge(first_order, on="CustomerID", how="left")

        # Step 3: convert Month strings to integers for arithmetic
        # Format is "YYYY-MM" — we compute total months since epoch
        def month_to_int(m: str) -> int:
            year, month = m.split("-")
            return int(year) * 12 + int(month)

        df["MonthInt"]       = df["Month"].apply(month_to_int)
        df["CohortMonthInt"] = df["CohortMonth"].apply(month_to_int)
        df["MonthsLater"]    = df["MonthInt"] - df["CohortMonthInt"]

        # Step 4: count distinct active customers per cohort + period
        cohort_data = (
            df
            .groupby(["CohortMonth", "MonthsLater"])["CustomerID"]
            .nunique()
            .reset_index()
            .rename(columns={"CustomerID": "CustomersActive"})
        )

        # Step 5: get cohort sizes (customers who made their first purchase
        # in that month = MonthsLater == 0)
        cohort_sizes = (
            cohort_data[cohort_data["MonthsLater"] == 0]
            [["CohortMonth", "CustomersActive"]]
            .rename(columns={"CustomersActive": "CohortSize"})
        )

        # Step 6: merge cohort size back in and calculate retention rate
        cohort_data = cohort_data.merge(cohort_sizes, on="CohortMonth", how="left")
        cohort_data["RetentionRate"] = (
            cohort_data["CustomersActive"] / cohort_data["CohortSize"]
        ).round(4)

        cohort_data = cohort_data.sort_values(["CohortMonth", "MonthsLater"]).reset_index(drop=True)
        return cohort_data
