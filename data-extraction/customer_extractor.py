"""
customer_extractor.py
----------------------
Loads and flattens the deeply nested customer profiles JSON.

Source: customer_profiles_v2.json
Format: dict keyed by "usr_profile_CUST-XXXX" → nested object (4 levels deep)

The JSON structure per profile:
  usr_profile_CUST-0001
  ├── sys_meta              (device / session metadata — mostly noise)
  ├── account_details       (region, goals)
  ├── acquisition_telemetry (utm_medium = acquisition channel)
  └── financial_metrics_v2  (tier, LTV, return rate, fraud flag)

Cleaning steps performed here:
  - Normalize the key → CustomerID (strip "usr_profile_" prefix)
  - Extract all business-relevant nested fields into flat columns
  - Exclude fraud-locked customers from the clean dataset
"""

import json
from pathlib import Path
from typing import Any

import pandas as pd

from base_extractor import BaseExtractor


class CustomerExtractor(BaseExtractor):
    """Flattens the nested customer profiles JSON into a flat DataFrame."""

    def extract(self) -> pd.DataFrame:
        raw_dict = self._load_json()
        flat_rows = [self._flatten_profile(key, profile) for key, profile in raw_dict.items()]

        df = pd.DataFrame(flat_rows)
        df = self._remove_fraud_locked(df)

        return df

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_json(self) -> dict:
        with open(self.file_path, "r") as f:
            return json.load(f)

    def _flatten_profile(self, key: str, profile: dict) -> dict:
        """
        Pull each useful field out of its nested location and return a
        simple flat dictionary for one customer.

        We use .get() with a default of None at every level so a missing
        nested key never throws a KeyError — it just becomes a null value.
        """
        customer_id = key.replace("usr_profile_", "")

        # Navigate nested sections — each is its own variable for clarity
        account      = profile.get("account_details", {})
        geo          = account.get("geo_segmentation", {})
        preferences  = account.get("preferences", {})

        telemetry    = profile.get("acquisition_telemetry", {})
        source       = telemetry.get("source", {})
        hardware     = telemetry.get("hardware", {})

        financials   = profile.get("financial_metrics_v2", {})
        status       = financials.get("status", {})
        risk         = financials.get("risk_factors", {})

        return {
            "CustomerID":           customer_id,
            "AcqChannel":           source.get("utm_medium"),
            "Device":               hardware.get("primary_device"),
            "MacroRegion":          geo.get("macro_region"),
            "MicroZone":            geo.get("micro_zone"),
            "PrimaryGoal":          preferences.get("primary_goal"),
            "LoyaltyTier":          status.get("tier"),
            "RewardPoints":         status.get("reward_points"),
            "ProjectedLTV":         financials.get("projected_ltv_at_signup_usd"),
            "CustomerReturnRatePct": risk.get("return_rate_pct"),
            "FraudLock":            risk.get("fraud_lock", False),
        }

    def _remove_fraud_locked(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fraud-locked customers are excluded from all analysis.
        We log how many were removed so the pipeline run summary is transparent.
        """
        fraud_count = df["FraudLock"].sum()
        df = df[df["FraudLock"] == False].copy()
        df = df.drop(columns=["FraudLock"])  # no longer needed downstream

        if fraud_count > 0:
            print(f"[CustomerExtractor] Excluded {fraud_count} fraud-locked customers")

        return df
