"""Real data sanity test script.
Loads MyTransaction.csv, maps categories, extracts features using
ntc_model/feature_engine.py (read-only), and runs pre-layer rules.
Does NOT modify anything inside ntc_model/.
"""
import pandas as pd
import sys
import os

# Add project root to path so we can import from root-level modules
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
# Also add ntc_model so we can import feature_engine (read-only usage)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "ntc_model"))

from feature_engine import extract_features
from pre_layer import apply_pre_layer

DATA_PATH = os.path.join(PROJECT_ROOT, "MyTransaction.csv")

CATEGORY_MAP = {
    "Food": "essential",
    "Shopping": "lifestyle",
    "Rent": "rent",
    "Salary": "income",
    "Misc": "misc",
}

# Mapping from our simplified categories to the feature_engine expected categories
FEATURE_ENGINE_CATEGORY_MAP = {
    "essential": "UTILITY",
    "lifestyle": "LIFESTYLE",
    "rent": "RENT",
    "income": "INCOME",
    "misc": "MISC",
}


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names to lowercase with underscores."""
    df.columns = df.columns.astype(str).str.strip().str.lower().str.replace(" ", "_")
    return df


def run_test():
    print(f"Loading transactions from {DATA_PATH}")
    try:
        df = pd.read_csv(DATA_PATH)
    except Exception as e:
        print(f"ERROR: Could not read {DATA_PATH}: {e}")
        return

    df = clean_columns(df)

    total_loaded = len(df)
    categories_found = set()
    defaulted_fields = []

    transactions = []
    for _, row in df.iterrows():
        raw_cat = str(row.get("category", "Misc"))
        mapped = CATEGORY_MAP.get(raw_cat, "misc")
        categories_found.add(mapped)
        engine_cat = FEATURE_ENGINE_CATEGORY_MAP.get(mapped, "MISC")

        date_val = str(row.get("date", "2025-01-01"))
        if pd.isna(row.get("date")):
            date_val = "2025-01-01"

        txn = {
            "date": date_val,
            "amount": float(row.get("amount", 0.0)),
            "type": str(row.get("type", "DR")).upper(),
            "category": engine_cat,
            "description": str(row.get("description", "")),
        }
        if "balance" in df.columns and pd.notna(row.get("balance")):
            txn["balance"] = float(row["balance"])

        transactions.append(txn)

    applicant_metadata = {
        "applicant_age_years": 32,
        "business_vintage_months": 24,
        "monthly_income": 45000,
        "loan_amount_requested": 150000,
        "owns_property": 1,
        "academic_background_tier": 2,
        "purpose_of_loan_encoded": 1,
        "gst_filing_consistency_score": 5,
        "telecom_number_vintage_days": 800,
    }

    dates = [t["date"] for t in transactions if t["date"] != "2025-01-01"]
    stmt_start = min(dates) if dates else "2025-01-01"
    stmt_end = max(dates) if dates else "2025-12-31"

    statement = {
        "statement_start": stmt_start,
        "statement_end": stmt_end,
        "transactions": transactions,
        "applicant_metadata": applicant_metadata,
    }

    # Step A: extract_features
    print("-" * 50)
    print("Step A: Extracting features...")
    try:
        features = extract_features(statement)
        print(f"  Extracted {len(features)} features successfully.")
        for k, v in features.items():
            print(f"    {k}: {v}")

        # Flag defaults
        if (
            features.get("utility_payment_consistency") == 0.75
            and features.get("avg_utility_dpd") == 5.0
        ):
            defaulted_fields.extend(["utility_payment_consistency", "avg_utility_dpd"])

        if defaulted_fields:
            print(
                f"\n  [WARNING] Defaulted fields (no matching data): "
                f"{', '.join(defaulted_fields)}"
            )
    except Exception as e:
        print(f"  Feature extraction FAILED: {e}")
        return

    # Step B: apply_pre_layer
    print("-" * 50)
    print("Step B: Applying pre-layer rules...")
    result = apply_pre_layer(features)
    if result is None:
        print("  Pre-layer result: PASS — no rule fired, would go to ML model.")
    else:
        grade, status, reason = result
        print(f"  Pre-layer result: RULE FIRED")
        print(f"    Grade:  {grade}")
        print(f"    Status: {status}")
        print(f"    Reason: {reason}")

    # Step C: Model inference — skipped
    print("-" * 50)
    print("Step C: Model inference skipped — NTC scope frozen")

    # Final Summary
    print("-" * 50)
    print("FINAL SUMMARY")
    print(f"  Total transactions loaded : {total_loaded}")
    print(f"  Categories found          : {categories_found}")
    print(f"  Features extracted         : {len(features)}")
    print(f"  Missing/defaulted fields   : {len(defaulted_fields)}")
    if defaulted_fields:
        print(f"  Defaulted field names      : {defaulted_fields}")


if __name__ == "__main__":
    run_test()
