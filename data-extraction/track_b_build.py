from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ENCODED = ROOT / "encoded_data"


def normalize_customer_id(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    match = re.search(r"CUST-\d+", text)
    if match:
        return match.group(0)
    return text.strip() if text.strip() else None


def pick_column(columns: list[str], candidates: list[str]) -> str | None:
    norm_map = {c.lower(): c for c in columns}
    for cand in candidates:
        if cand.lower() in norm_map:
            return norm_map[cand.lower()]
    for cand in candidates:
        for col in columns:
            if cand.lower() in col.lower():
                return col
    return None


def build_monthly_merged_table() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, float]]:
    pnl = pd.read_csv(ENCODED / "monthly_pnl_summary.csv")
    pnl["Month"] = pnl["Month"].astype(str)
    pnl_clean = pnl.sort_values("Month").drop_duplicates(subset=["Month"], keep="first").copy()

    marketing = pd.read_excel(ENCODED / "marketing_spend_history.xlsx")
    marketing["Month"] = marketing["Month"].astype(str).str[:7]
    marketing["AdSpend"] = pd.to_numeric(marketing["AdSpend"], errors="coerce").fillna(0.0)

    marketing_total = (
        marketing.groupby("Month", as_index=False)["AdSpend"].sum().rename(columns={"AdSpend": "MarketingSpend"})
    )
    marketing_by_channel = marketing.pivot_table(
        index="Month", columns="Channel", values="AdSpend", aggfunc="sum", fill_value=0.0
    ).reset_index()
    marketing_by_channel.columns = [
        "Month" if col == "Month" else f"Marketing_{str(col).strip().replace(' ', '_')}" for col in marketing_by_channel.columns
    ]

    sku = pd.read_csv(ENCODED / "sku_summary.csv")
    rate_card = pd.read_excel(ENCODED / "warehouse_rate_card.xlsx")

    sku["EcoFriendly"] = sku["EcoFriendly"].astype(str).str.lower().isin(["true", "1", "yes"])
    sku["Handling_Type"] = np.where(sku["EcoFriendly"], "Eco-Friendly", "Standard")

    fee_col = pick_column(rate_card.columns.tolist(), ["Monthly_Storage_Fee_Per_Unit"])
    if fee_col is None:
        raise ValueError("Warehouse rate card missing Monthly_Storage_Fee_Per_Unit column")

    sku_merged = sku.merge(
        rate_card[["Category", "Handling_Type", fee_col]], on=["Category", "Handling_Type"], how="left"
    )
    sku_merged[fee_col] = pd.to_numeric(sku_merged[fee_col], errors="coerce")
    sku_merged["StorageCostPerUnit"] = pd.to_numeric(sku_merged["StorageCostPerUnit"], errors="coerce")
    sku_merged["AppliedStorageFeePerUnit"] = sku_merged[fee_col].fillna(sku_merged["StorageCostPerUnit"]).fillna(0.0)
    sku_merged["TotalUnitsSold"] = pd.to_numeric(sku_merged["TotalUnitsSold"], errors="coerce").fillna(0.0)

    storage_cost_total_period = float((sku_merged["TotalUnitsSold"] * sku_merged["AppliedStorageFeePerUnit"]).sum())
    gross_total = float(pd.to_numeric(pnl_clean["GrossRevenue"], errors="coerce").fillna(0.0).sum())
    monthly_weight = pd.to_numeric(pnl_clean["GrossRevenue"], errors="coerce").fillna(0.0) / max(gross_total, 1e-9)
    pnl_clean["EstimatedWarehouseStorageCost"] = storage_cost_total_period * monthly_weight

    merged = pnl_clean.merge(marketing_total, on="Month", how="left").merge(marketing_by_channel, on="Month", how="left")
    merged = merged.fillna(0.0)

    numeric_cols = [
        "GrossRevenue",
        "TotalCOGS",
        "TotalDiscounts",
        "TotalShipping",
        "TotalPaymentFees",
        "ActualNetRevenue",
        "MonthlyLaborCost",
        "WarehouseRent",
        "MarketingSpend",
        "EstimatedWarehouseStorageCost",
    ]
    for col in numeric_cols:
        merged[col] = pd.to_numeric(merged[col], errors="coerce").fillna(0.0)

    merged["EBITDA_Proxy"] = (
        merged["ActualNetRevenue"]
        - merged["TotalCOGS"]
        - merged["MonthlyLaborCost"]
        - merged["WarehouseRent"]
        - merged["MarketingSpend"]
        - merged["EstimatedWarehouseStorageCost"]
    )
    merged["EBITDA_Proxy_MarginPct"] = np.where(
        merged["ActualNetRevenue"] != 0,
        100.0 * merged["EBITDA_Proxy"] / merged["ActualNetRevenue"],
        0.0,
    )

    out_monthly = ENCODED / "track_b_monthly_merged_table.csv"
    merged.to_csv(out_monthly, index=False)

    assumptions = {
        "storage_cost_total_period": storage_cost_total_period,
        "pnl_months": float(len(merged)),
    }
    return merged, marketing, sku_merged, assumptions


def load_sqlite_behavior() -> tuple[pd.DataFrame, pd.DataFrame, str]:
    db_path = ENCODED / "zenith_core_db.sqlite"
    conn = sqlite3.connect(db_path)

    tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name", conn)["name"].tolist()
    best_table = None
    best_score = -1
    best_cols: list[str] = []

    for table in tables:
        cols = pd.read_sql_query(f"PRAGMA table_info({table})", conn)["name"].tolist()
        low = [c.lower() for c in cols]

        has_customer = any("customer" in c or "cust" in c or "user" in c for c in low)
        has_date = any("date" in c or "created" in c or "time" in c for c in low)
        has_amount = any("amount" in c or "revenue" in c or "total" in c or "net" in c for c in low)
        has_order = any("order" in c for c in low)

        score = int(has_customer) + int(has_date) + int(has_amount) + int(has_order)
        if score > best_score:
            best_score = score
            best_table = table
            best_cols = cols

    if best_table is None:
        conn.close()
        raise ValueError("No SQLite tables found")

    orders = pd.read_sql_query(f"SELECT * FROM {best_table}", conn)
    conn.close()

    cust_col = pick_column(best_cols, ["CustomerID", "customer_id", "cust_id", "user_id", "customer"])
    date_col = pick_column(best_cols, ["OrderDate", "order_date", "purchase_date", "created_at", "date", "timestamp"])
    order_col = pick_column(best_cols, ["OrderID", "order_id", "transaction_id", "invoice_id"])
    amount_col = pick_column(best_cols, ["OrderTotal", "order_total", "TotalAmount", "amount", "net_revenue", "revenue", "total"])

    if cust_col is None or date_col is None:
        raise ValueError(f"Selected table {best_table} does not include customer/date columns")

    orders = orders.copy()
    orders["CustomerID_Normalized"] = orders[cust_col].map(normalize_customer_id)
    orders["OrderDate_Normalized"] = pd.to_datetime(orders[date_col], errors="coerce")
    orders = orders.dropna(subset=["CustomerID_Normalized", "OrderDate_Normalized"])

    if order_col is None:
        orders["OrderID_Normalized"] = np.arange(len(orders)).astype(str)
    else:
        orders["OrderID_Normalized"] = orders[order_col].astype(str)

    if amount_col is not None:
        orders["Revenue_Normalized"] = pd.to_numeric(orders[amount_col], errors="coerce").fillna(0.0)
    else:
        qty_col = pick_column(best_cols, ["Quantity", "qty", "units"])
        price_col = pick_column(best_cols, ["UnitPrice", "unit_price", "price"])
        if qty_col is not None and price_col is not None:
            orders["Revenue_Normalized"] = (
                pd.to_numeric(orders[qty_col], errors="coerce").fillna(0.0)
                * pd.to_numeric(orders[price_col], errors="coerce").fillna(0.0)
            )
        else:
            orders["Revenue_Normalized"] = 0.0

    customer_behavior = (
        orders.groupby("CustomerID_Normalized", as_index=False)
        .agg(
            Orders=("OrderID_Normalized", "nunique"),
            Revenue=("Revenue_Normalized", "sum"),
            FirstOrderDate=("OrderDate_Normalized", "min"),
            LastOrderDate=("OrderDate_Normalized", "max"),
        )
        .copy()
    )

    span_days = (customer_behavior["LastOrderDate"] - customer_behavior["FirstOrderDate"]).dt.days + 1
    span_months = np.maximum(1.0, span_days / 30.4)
    customer_behavior["AOV"] = np.where(customer_behavior["Orders"] != 0, customer_behavior["Revenue"] / customer_behavior["Orders"], 0.0)
    customer_behavior["PurchaseFrequencyPerMonth"] = customer_behavior["Orders"] / span_months
    customer_behavior["RepeatCustomer"] = customer_behavior["Orders"] > 1
    customer_behavior["CohortMonth"] = customer_behavior["FirstOrderDate"].dt.to_period("M").astype(str)

    customer_behavior.to_csv(ENCODED / "track_b_customer_purchase_behavior.csv", index=False)
    return orders, customer_behavior, best_table


def enrich_with_profiles(customer_behavior: pd.DataFrame, marketing: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    with open(ENCODED / "customer_profiles_v2.json", "r", encoding="utf-8") as f:
        profiles = json.load(f)

    rows = []
    for key, value in profiles.items():
        rows.append(
            {
                "CustomerID_Normalized": normalize_customer_id(key),
                "AcquisitionChannel": value.get("acquisition_telemetry", {})
                .get("source", {})
                .get("utm_medium"),
                "CustomerTier": value.get("financial_metrics_v2", {}).get("status", {}).get("tier"),
                "ProjectedLTV": value.get("financial_metrics_v2", {}).get("projected_ltv_at_signup_usd"),
                "ModeledReturnRiskPct": value.get("financial_metrics_v2", {})
                .get("risk_factors", {})
                .get("return_rate_pct"),
                "Region": value.get("account_details", {})
                .get("geo_segmentation", {})
                .get("macro_region"),
            }
        )

    profile_df = pd.DataFrame(rows)
    profile_df["ProjectedLTV"] = pd.to_numeric(profile_df["ProjectedLTV"], errors="coerce")
    profile_df["ModeledReturnRiskPct"] = pd.to_numeric(profile_df["ModeledReturnRiskPct"], errors="coerce")

    enriched = customer_behavior.merge(profile_df, on="CustomerID_Normalized", how="left")
    enriched.to_csv(ENCODED / "track_b_customer_behavior_enriched.csv", index=False)

    cohorts = (
        enriched.groupby("CohortMonth", as_index=False)
        .agg(
            Customers=("CustomerID_Normalized", "nunique"),
            RepeatRatePct=("RepeatCustomer", lambda s: 100.0 * float(np.mean(s)) if len(s) else 0.0),
            AvgOrders=("Orders", "mean"),
            AvgAOV=("AOV", "mean"),
            AvgRevenue=("Revenue", "mean"),
            AvgProjectedLTV=("ProjectedLTV", "mean"),
            AvgModeledReturnRiskPct=("ModeledReturnRiskPct", "mean"),
        )
        .sort_values("CohortMonth")
    )
    cohorts.to_csv(ENCODED / "track_b_customer_cohorts.csv", index=False)

    cohort_channel = (
        enriched.groupby(["CohortMonth", "AcquisitionChannel"], as_index=False)
        .agg(
            Customers=("CustomerID_Normalized", "nunique"),
            AvgOrders=("Orders", "mean"),
            AvgRevenue=("Revenue", "mean"),
            AvgProjectedLTV=("ProjectedLTV", "mean"),
        )
        .sort_values(["CohortMonth", "Customers"], ascending=[True, False])
    )
    cohort_channel.to_csv(ENCODED / "track_b_cohort_by_channel.csv", index=False)

    channel_spend = marketing.groupby("Channel", as_index=False)["AdSpend"].sum().rename(columns={"AdSpend": "TotalAdSpend"})
    channel_new_customers = (
        profile_df.dropna(subset=["AcquisitionChannel"])
        .groupby("AcquisitionChannel", as_index=False)["CustomerID_Normalized"]
        .nunique()
        .rename(columns={"AcquisitionChannel": "Channel", "CustomerID_Normalized": "NewCustomers"})
    )
    channel_ltv = (
        profile_df.dropna(subset=["AcquisitionChannel"])
        .groupby("AcquisitionChannel", as_index=False)["ProjectedLTV"]
        .mean()
        .rename(columns={"AcquisitionChannel": "Channel", "ProjectedLTV": "AvgProjectedLTV"})
    )

    channel_eff = channel_spend.merge(channel_new_customers, on="Channel", how="left").merge(channel_ltv, on="Channel", how="left")
    channel_eff["NewCustomers"] = channel_eff["NewCustomers"].fillna(0)
    channel_eff["CAC"] = np.where(channel_eff["NewCustomers"] > 0, channel_eff["TotalAdSpend"] / channel_eff["NewCustomers"], np.nan)
    channel_eff["LTV_to_CAC"] = np.where(channel_eff["CAC"] > 0, channel_eff["AvgProjectedLTV"] / channel_eff["CAC"], np.nan)
    channel_eff = channel_eff.sort_values("LTV_to_CAC", ascending=False)
    channel_eff.to_csv(ENCODED / "track_b_channel_cac_ltv.csv", index=False)

    return enriched, channel_eff


def build_board_summary(monthly: pd.DataFrame, sku_merged: pd.DataFrame, channel_eff: pd.DataFrame, sqlite_table: str) -> None:
    sku_merged = sku_merged.copy()
    sku_merged["TotalRevenue"] = pd.to_numeric(sku_merged["TotalRevenue"], errors="coerce").fillna(0.0)
    sku_merged["GrossMargin%"] = pd.to_numeric(sku_merged["GrossMargin%"], errors="coerce").fillna(0.0)
    sku_merged["ReturnRate"] = pd.to_numeric(sku_merged["ReturnRate"], errors="coerce").fillna(0.0)
    sku_merged["TotalUnitsSold"] = pd.to_numeric(sku_merged["TotalUnitsSold"], errors="coerce").fillna(0.0)

    sku_merged["GrossMarginValue"] = sku_merged["TotalRevenue"] * sku_merged["GrossMargin%"]
    sku_merged["StorageBurden"] = sku_merged["TotalUnitsSold"] * sku_merged["AppliedStorageFeePerUnit"]
    # Assumption: 30% of returned item value is unrecovered contribution loss.
    sku_merged["ReturnLossProxy"] = sku_merged["TotalRevenue"] * sku_merged["ReturnRate"] * 0.30
    sku_merged["ContributionProxy"] = sku_merged["GrossMarginValue"] - sku_merged["StorageBurden"] - sku_merged["ReturnLossProxy"]

    worst_skus = sku_merged.nsmallest(10, "ContributionProxy")[["ProductID", "Category", "ContributionProxy", "ReturnRate", "StorageBurden"]]
    worst_skus.to_csv(ENCODED / "track_b_bottom10_skus_by_contribution.csv", index=False)

    total_ebitda = float(monthly["EBITDA_Proxy"].sum())
    total_net = float(monthly["ActualNetRevenue"].sum())
    ebitda_margin = 100.0 * total_ebitda / max(total_net, 1e-9)

    bottom_20_cutoff = int(np.ceil(0.2 * len(sku_merged)))
    bottom20 = sku_merged.nsmallest(bottom_20_cutoff, "ContributionProxy")
    sku_storage_savings = float(bottom20["StorageBurden"].sum())
    sku_return_savings = float(bottom20["ReturnLossProxy"].sum() * 0.25)
    sku_total_savings = sku_storage_savings + sku_return_savings
    sku_margin_uplift_pts = 100.0 * sku_total_savings / max(total_net, 1e-9)

    channel_eff_valid = channel_eff.dropna(subset=["CAC", "LTV_to_CAC"]).copy()
    if not channel_eff_valid.empty:
        worst_channel = channel_eff_valid.sort_values("LTV_to_CAC", ascending=True).iloc[0]
        best_channel = channel_eff_valid.sort_values("LTV_to_CAC", ascending=False).iloc[0]
        reallocated_spend = float(worst_channel["TotalAdSpend"] * 0.25)
        cac_improvement = float(max(0.0, worst_channel["CAC"] - best_channel["CAC"]))
        marketing_savings = reallocated_spend * (cac_improvement / max(worst_channel["CAC"], 1e-9))
        marketing_margin_uplift_pts = 100.0 * marketing_savings / max(total_net, 1e-9)
        worst_channel_name = str(worst_channel["Channel"])
        best_channel_name = str(best_channel["Channel"])
    else:
        marketing_savings = 0.0
        marketing_margin_uplift_pts = 0.0
        worst_channel_name = "N/A"
        best_channel_name = "N/A"

    summary_path = ROOT / "data-extraction" / "TRACK_B_BOARD_READY_SUMMARY.md"
    lines = [
        "# Track B: Board-Ready Business Intelligence & Strategy Output",
        "",
        "## 1) What Was Built",
        "- Single monthly merged table combining P&L, monthly marketing spend, and warehouse storage-cost proxy from rate card.",
        "- SQLite-driven customer purchase behavior table and cohort views.",
        "- Channel-level CAC vs LTV table.",
        "- SKU contribution proxy and bottom-10 SKU risk list.",
        "",
        "## 2) Core Financial Signals",
        f"- Total net revenue (period): {total_net:,.2f}",
        f"- EBITDA proxy (period): {total_ebitda:,.2f}",
        f"- EBITDA proxy margin: {ebitda_margin:.2f}%",
        "",
        "## 3) Margin Killers (Quantified)",
        f"- Marketing intensity: monthly marketing is now included directly in waterfall-style EBITDA proxy.",
        f"- SKU storage + returns drag: bottom 20% SKU set implies {sku_total_savings:,.2f} recoverable value (storage + return-loss proxy).",
        f"- Contribution upside from SKU rationalization: ~{sku_margin_uplift_pts:.2f} margin points.",
        "",
        "## 4) CAC-LTV Efficiency",
        f"- Lowest LTV/CAC channel: {worst_channel_name}",
        f"- Highest LTV/CAC channel: {best_channel_name}",
        f"- If 25% of lowest-efficiency spend is reallocated: estimated savings {marketing_savings:,.2f} and ~{marketing_margin_uplift_pts:.2f} margin points.",
        "",
        "## 5) Process Redesign (Current -> Future)",
        "- Current: broad SKU catalog, high return-exposed items, and channel mix not explicitly optimized for LTV/CAC.",
        "- Future: bottom-quintile SKU rationalization, channel-budget reallocation to higher LTV/CAC, monthly monitoring of cohort repeat-rate and EBITDA proxy.",
        "",
        "## 6) 30-60-90 Day Plan",
        "- 30 days: freeze long-tail SKU expansion, enforce monthly CAC-LTV review, confirm dead-stock list.",
        "- 60 days: implement SKU delist/bundle actions and channel budget shifts.",
        "- 90 days: complete cohort-driven retention program and lock dashboard governance cadence.",
        "",
        "## 7) Data Assumptions",
        "- Warehouse storage cost proxy uses rate card fee per unit mapped by Category + Handling_Type and distributed monthly by gross-revenue weight.",
        "- Return-loss proxy assumes 30% unrecovered value of returned revenue.",
        "- Marketing reallocation scenario assumes 25% spend shift from the lowest to highest LTV/CAC channel.",
        f"- SQLite customer purchase behavior derived from table: {sqlite_table}",
    ]
    summary_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    monthly, marketing, sku_merged, _ = build_monthly_merged_table()
    _, customer_behavior, sqlite_table = load_sqlite_behavior()
    _, channel_eff = enrich_with_profiles(customer_behavior, marketing)
    build_board_summary(monthly, sku_merged, channel_eff, sqlite_table)

    print("Created:")
    print(ENCODED / "track_b_monthly_merged_table.csv")
    print(ENCODED / "track_b_customer_purchase_behavior.csv")
    print(ENCODED / "track_b_customer_behavior_enriched.csv")
    print(ENCODED / "track_b_customer_cohorts.csv")
    print(ENCODED / "track_b_cohort_by_channel.csv")
    print(ENCODED / "track_b_channel_cac_ltv.csv")
    print(ENCODED / "track_b_bottom10_skus_by_contribution.csv")
    print(ROOT / "data-extraction" / "TRACK_B_BOARD_READY_SUMMARY.md")


if __name__ == "__main__":
    main()
