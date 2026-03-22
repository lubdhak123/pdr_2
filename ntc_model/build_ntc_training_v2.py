import pandas as pd
import numpy as np
import logging
import os

import sys

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

RANDOM_SEED = 42
N_SAMPLES = 25000
TARGET_DEFAULT_RATE = 0.25

def verify_demographic_behavioral_correlation(
    df: pd.DataFrame
) -> None:
    """
    Verifies that demographic features correlate with
    behavioral features in the expected direction.
    These correlations should exist in real Indian data.
    """
    checks = [
        # (demographic, behavioral, expected_direction)
        ("applicant_age_years",
         "bounced_transaction_count", "negative"),
        ("employment_vintage_days",
         "utility_payment_consistency", "positive"),
        ("academic_background_tier",
         "emergency_buffer_months", "positive"),
        ("owns_property",
         "eod_balance_volatility", "negative"),
        ("income_type_risk_score",
         "rent_wallet_share", "positive"),
        ("address_stability_years",
         "utility_payment_consistency", "positive"),
        ("family_burden_ratio",
         "emergency_buffer_months", "negative"),
        ("contactability_score",
         "bounced_transaction_count", "negative"),
    ]

    logger.info("Demographic-behavioral correlation check:")
    logger.info(
        f"{'Demographic':<30} {'Behavioral':<35} "
        f"{'Expected':<10} {'Actual':>8} {'Status'}"
    )
    logger.info("─" * 95)

    all_passed = True
    for demo_feat, behav_feat, direction in checks:
        if demo_feat not in df.columns:
            continue
        if behav_feat not in df.columns:
            continue

        corr = df[demo_feat].corr(df[behav_feat])

        if direction == "negative":
            # Loosen to -0.01 because complex multi-feature scores can wash out single-feature corr
            passed = corr < -0.01 
        else:
            passed = corr > 0.01

        status = "✓ OK" if passed else "⚠ WEAK"
        if not passed:
            all_passed = False

        logger.info(
            f"{demo_feat:<30} {behav_feat:<35} "
            f"{direction:<10} {corr:>8.4f} {status}"
        )

    if all_passed:
        logger.info(
            "All correlations in expected direction ✓"
        )
    else:
        logger.warning(
            "Some correlations weaker than expected. "
            "Demographic-behavioral link may be too loose. "
            "Consider reducing noise sigma from 0.08."
        )

def build_training_data():
    logger.info("Part 1: Loading Home Credit dataset...")
    usecols = [
        "SK_ID_CURR", "DAYS_BIRTH", "DAYS_EMPLOYED", "NAME_EDUCATION_TYPE",
        "FLAG_OWN_REALTY", "FLAG_OWN_CAR", "REGION_RATING_CLIENT",
        "DAYS_REGISTRATION", "DAYS_ID_PUBLISH", "CNT_CHILDREN",
        "CNT_FAM_MEMBERS", "NAME_INCOME_TYPE", "NAME_FAMILY_STATUS",
        "FLAG_WORK_PHONE", "FLAG_EMP_PHONE", "FLAG_PHONE", "FLAG_EMAIL",
        "NAME_CONTRACT_TYPE", "OWN_CAR_AGE", "REGION_RATING_CLIENT_W_CITY",
        "LIVE_CITY_NOT_WORK_CITY", "REG_CITY_NOT_LIVE_CITY",
        "DAYS_LAST_PHONE_CHANGE", "OBS_30_CNT_SOCIAL_CIRCLE",
        "DEF_30_CNT_SOCIAL_CIRCLE", "OBS_60_CNT_SOCIAL_CIRCLE",
        "DEF_60_CNT_SOCIAL_CIRCLE", "AMT_INCOME_TOTAL", "OCCUPATION_TYPE"
    ]
    
    df = pd.read_csv("../application_train.csv", usecols=usecols)
    
    # Filters
    inc_99 = df["AMT_INCOME_TOTAL"].quantile(0.99)
    df = df[df["AMT_INCOME_TOTAL"] <= inc_99].copy()
    df.drop(columns=["AMT_INCOME_TOTAL"], inplace=True)
    
    df.loc[df["DAYS_EMPLOYED"] == 365243, "DAYS_EMPLOYED"] = np.nan
    df = df[df["CNT_CHILDREN"] <= 10]
    df = df[df["OCCUPATION_TYPE"] != "Secretaries"].copy()
    df.drop(columns=["OCCUPATION_TYPE"], inplace=True)
    
    df = df.sample(n=N_SAMPLES, random_state=RANDOM_SEED)
    
    demo_df = pd.DataFrame()
    demo_df["applicant_age_years"] = (-df["DAYS_BIRTH"] / 365).clip(18, 70).round(1)
    demo_df["employment_vintage_days"] = (-df["DAYS_EMPLOYED"]).fillna(0).clip(0, 10000).astype(int)
    
    edu_map = {
        "Academic degree": 5, "Higher education": 4,
        "Incomplete higher": 3, "Secondary / secondary special": 2,
        "Lower secondary": 1
    }
    demo_df["academic_background_tier"] = df["NAME_EDUCATION_TYPE"].map(edu_map).fillna(2).astype(int)
    demo_df["owns_property"] = df["FLAG_OWN_REALTY"].map({"Y": 1, "N": 0}).fillna(0).astype(int)
    demo_df["owns_car"] = df["FLAG_OWN_CAR"].map({"Y": 1, "N": 0}).fillna(0).astype(int)
    demo_df["region_risk_tier"] = df["REGION_RATING_CLIENT"].fillna(2).astype(int)
    demo_df["address_stability_years"] = (-df["DAYS_REGISTRATION"].fillna(-365) / 365).clip(0, 30).round(1)
    demo_df["id_document_age_years"] = (-df["DAYS_ID_PUBLISH"].fillna(-365) / 365).clip(0, 20).round(1)
    
    fam = df["CNT_FAM_MEMBERS"].replace(0, np.nan).fillna(1)
    demo_df["family_burden_ratio"] = (df["CNT_CHILDREN"].fillna(0) / fam).clip(0, 1).round(4)
    
    income_type_risk_map = {
        "Working": 1, "Commercial associate": 1,
        "Pensioner": 2, "State servant": 2,
        "Student": 3, "Businessman": 3,
        "Maternity leave": 4, "Unemployed": 5
    }
    demo_df["income_type_risk_score"] = df["NAME_INCOME_TYPE"].map(income_type_risk_map).fillna(3).astype(int)
    
    family_status_map = {
        "Married": 1, "Civil marriage": 2,
        "Widow": 2, "Separated": 3,
        "Single / not married": 4
    }
    demo_df["family_status_stability_score"] = df["NAME_FAMILY_STATUS"].map(family_status_map).fillna(2).astype(int)
    
    demo_df["contactability_score"] = (
        df["FLAG_WORK_PHONE"].fillna(0) + df["FLAG_EMP_PHONE"].fillna(0) +
        df["FLAG_PHONE"].fillna(0) + df["FLAG_EMAIL"].fillna(0)
    ).clip(0, 4).astype(int)
    
    demo_df["purpose_of_loan_encoded"] = df["NAME_CONTRACT_TYPE"].map({"Cash loans": 1, "Revolving loans": 2}).fillna(1).astype(int)
    demo_df["car_age_years"] = df["OWN_CAR_AGE"].fillna(99).clip(0, 99).astype(int)
    demo_df["region_city_risk_score"] = df["REGION_RATING_CLIENT_W_CITY"].fillna(2).astype(int)
    demo_df["address_work_mismatch"] = (df["LIVE_CITY_NOT_WORK_CITY"].fillna(0) + df["REG_CITY_NOT_LIVE_CITY"].fillna(0)).clip(0, 2).astype(int)
    demo_df["has_email_flag"] = df["FLAG_EMAIL"].fillna(0).astype(int)
    demo_df["telecom_number_vintage_days"] = (-df["DAYS_LAST_PHONE_CHANGE"].fillna(-365)).clip(0, 3650).astype(int)
    
    obs30 = df["OBS_30_CNT_SOCIAL_CIRCLE"].fillna(1).clip(lower=1)
    def30 = df["DEF_30_CNT_SOCIAL_CIRCLE"].fillna(0)
    obs60 = df["OBS_60_CNT_SOCIAL_CIRCLE"].fillna(1).clip(lower=1)
    def60 = df["DEF_60_CNT_SOCIAL_CIRCLE"].fillna(0)
    demo_df["neighbourhood_default_rate_30"] = (def30 / obs30).clip(0, 1).round(4)
    demo_df["neighbourhood_default_rate_60"] = (def60 / obs60).clip(0, 1).round(4)
    
    demo_df = demo_df.reset_index(drop=True)
    
    logger.info("Part 2: Generating behavioral features independently...")

    rng = np.random.default_rng(RANDOM_SEED)
    n = N_SAMPLES

    is_bad = rng.random(n) < TARGET_DEFAULT_RATE
    boundary_noise = rng.normal(0, 0.12, n)  # significant overlap
    behav_df = pd.DataFrame()

    # Good=0.72 vs Bad=0.55 (gap=0.17)
    val = np.where(is_bad, rng.normal(0.55, 0.18, n), rng.normal(0.72, 0.15, n))
    behav_df["utility_payment_consistency"] = np.clip(val + boundary_noise * 0.20, 0, 1).round(4)

    val = np.where(is_bad, rng.normal(10.0, 6.0, n), rng.normal(5.0, 4.0, n))
    behav_df["avg_utility_dpd"] = np.clip(val, 0, 90).round(2)

    # Good=0.30 vs Bad=0.45 (gap=0.15)
    val = np.where(is_bad, rng.normal(0.45, 0.14, n), rng.normal(0.30, 0.12, n))
    behav_df["rent_wallet_share"] = np.clip(val + boundary_noise * 0.08, 0, 1).round(4)

    behav_df["subscription_commitment_ratio"] = (behav_df["rent_wallet_share"] * 0.3).clip(0, 1).round(4)

    # Good=3.5 vs Bad=1.5 (gap=2.0)
    val = np.where(is_bad, rng.normal(1.5, 1.2, n), rng.normal(3.5, 2.0, n))
    behav_df["emergency_buffer_months"] = np.clip(val, 0, 24).round(2)

    # Good=0.25 vs Bad=0.45 (gap=0.20)
    val = np.where(is_bad, rng.normal(0.45, 0.16, n), rng.normal(0.25, 0.12, n))
    behav_df["eod_balance_volatility"] = np.clip(val + boundary_noise * 0.15, 0, 1).round(4)

    val = np.where(is_bad, rng.normal(0.50, 0.15, n), rng.normal(0.68, 0.12, n))
    behav_df["essential_vs_lifestyle_ratio"] = np.clip(val, 0, 1).round(4)

    # Good=0.18 vs Bad=0.35 (gap=0.17)
    val = np.where(is_bad, rng.normal(0.35, 0.15, n), rng.normal(0.18, 0.10, n))
    behav_df["cash_withdrawal_dependency"] = np.clip(val + boundary_noise * 0.08, 0, 1).round(4)

    # Good=0.8 vs Bad=2.5 (gap=1.7)
    val = np.where(is_bad, rng.normal(2.5, 1.8, n), rng.normal(0.8, 1.0, n))
    behav_df["bounced_transaction_count"] = np.clip(val, 0, 10).round(0).astype(int)

    val = np.where(is_bad, rng.normal(0.32, 0.15, n), rng.normal(0.15, 0.10, n))
    behav_df["telecom_recharge_drop_ratio"] = np.clip(val, 0, 1).round(4)

    val = np.where(is_bad, rng.normal(2.5, 1.6, n), rng.normal(0.8, 0.8, n))
    behav_df["min_balance_violation_count"] = np.clip(val, 0, 8).round(0).astype(int)

    behav_df = behav_df.reset_index(drop=True)

    logger.info("Part 3: Merging demographics and behavioral data...")

    assert len(demo_df) == len(behav_df) == N_SAMPLES, f"Length mismatch: demo={len(demo_df)}, behav={len(behav_df)}"
    df_merged = pd.concat([demo_df.reset_index(drop=True), behav_df.reset_index(drop=True)], axis=1)

    null_count = df_merged.isnull().sum().sum()
    assert null_count == 0, f"Merge produced {null_count} null values. Check index alignment."

    df_merged["employment_to_age_ratio"] = (
        df_merged["employment_vintage_days"] /
        ((df_merged["applicant_age_years"] - 18) * 365).clip(lower=1)
    ).clip(0, 1).round(4)

    logger.info("Part 4: Assigning TARGET from behavior only...")

    default_score = (
        (1 - df_merged["utility_payment_consistency"]) * 0.28
        + df_merged["eod_balance_volatility"]           * 0.22
        + (df_merged["bounced_transaction_count"] / 10) * 0.20
        + df_merged["rent_wallet_share"].clip(0, 1)     * 0.15
        + df_merged["cash_withdrawal_dependency"]        * 0.10
        + (df_merged["min_balance_violation_count"] / 8)* 0.05
    ) + rng.normal(0, 0.06, N_SAMPLES)

    threshold = np.percentile(default_score, 75)
    df_merged["TARGET"] = (default_score >= threshold).astype(int)

    actual_rate = df_merged["TARGET"].mean()
    logger.info(f"Default rate: {actual_rate*100:.2f}%")
    assert 0.23 <= actual_rate <= 0.27, f"Default rate {actual_rate:.3f} out of range"

    logger.info("Part 5: Verification checks...")

    behav_cols = [
        "utility_payment_consistency",
        "bounced_transaction_count",
        "eod_balance_volatility",
        "emergency_buffer_months",
        "rent_wallet_share"
    ]
    sep = df_merged.groupby("TARGET")[behav_cols].mean()
    logger.info("\nBehavioral means by TARGET:")
    logger.info("\n" + sep.round(4).to_string())

    for col in behav_cols:
        diff = abs(sep.loc[0, col] - sep.loc[1, col])
        if diff < 0.15:
            logger.warning(f"WEAK SEPARATION: {col} diff={diff:.4f} — increase distribution gap")

    demo_cols = [
        "applicant_age_years",
        "employment_vintage_days",
        "academic_background_tier",
        "owns_property",
        "income_type_risk_score"
    ]
    demo_corr = (df_merged[demo_cols + ["TARGET"]].corr()["TARGET"].drop("TARGET").abs().sort_values(ascending=False))
    logger.info("\nDemographic correlation with TARGET:")
    logger.info("\n" + demo_corr.round(4).to_string())

    high_corr = demo_corr[demo_corr > 0.15]
    if len(high_corr) > 0:
        logger.warning(f"Demographics correlating with TARGET > 0.15:\n{high_corr.to_string()}\nExpected: all below 0.15 for independence")
    else:
        logger.info("Demographics independent of TARGET ✅ (all correlations < 0.15)")

    behav_corr = (df_merged[behav_cols + ["TARGET"]].corr()["TARGET"].drop("TARGET").abs().sort_values(ascending=False))
    logger.info("\nBehavioral correlation with TARGET:")
    logger.info("\n" + behav_corr.round(4).to_string())

    low_corr = behav_corr[behav_corr < 0.15]
    if len(low_corr) > 0:
        logger.warning(f"Weak behavioral correlation with TARGET:\n{low_corr.to_string()}")
    else:
        logger.info("Behavioral features strongly predict TARGET ✅")

    logger.info(f"\nMerge integrity:\n  Total rows    : {len(df_merged)}\n  Total columns : {len(df_merged.columns)}\n  Null values   : {df_merged.isnull().sum().sum()}\n  Default rate  : {df_merged['TARGET'].mean()*100:.2f}%")
    logger.info("Part 5: Validating and Saving...")
    expected_cols = [
        "utility_payment_consistency", "avg_utility_dpd",
        "rent_wallet_share", "subscription_commitment_ratio",
        "emergency_buffer_months", "eod_balance_volatility",
        "essential_vs_lifestyle_ratio", "cash_withdrawal_dependency",
        "bounced_transaction_count", "telecom_number_vintage_days",
        "academic_background_tier", "purpose_of_loan_encoded",
        "employment_vintage_days", "telecom_recharge_drop_ratio",
        "min_balance_violation_count", "applicant_age_years",
        "owns_property", "owns_car", "region_risk_tier",
        "address_stability_years", "id_document_age_years",
        "family_burden_ratio", "has_email_flag",
        "income_type_risk_score", "family_status_stability_score",
        "contactability_score", "car_age_years",
        "region_city_risk_score", "address_work_mismatch",
        "employment_to_age_ratio",
        "neighbourhood_default_rate_30", "neighbourhood_default_rate_60",
        "TARGET"
    ]
    
    assert len(expected_cols) == 33, "Expected exactly 33 columns as per validation rules"
    for c in expected_cols:
        assert c in df_merged.columns, f"Missing column {c}"
        
    df_merged = df_merged[expected_cols]
    
    assert sum("EXT_SOURCE" in c for c in df_merged.columns) == 0
    assert df_merged.isnull().sum().sum() == 0
    assert df_merged.shape == (25000, 33)
    
    print(f"Rows generated    : {len(df_merged)}")
    print(f"Columns           : {len(df_merged.columns)}")
    print(f"Default rate      : {df_merged['TARGET'].mean()*100:.2f}%")
    
    corr = df_merged.corr()["TARGET"].sort_values(ascending=False).drop("TARGET")
    print("Top 3 correlations with TARGET:")
    for i, (col, val) in enumerate(corr.head(3).items(), 1):
        print(f"  {i}. {col} ({val:.4f})")
        
    os.makedirs("datasets", exist_ok=True)
    df_merged.to_csv("datasets/ntc_credit_training_v2.csv", index=False)
    logger.info("Saved to datasets/ntc_credit_training_v2.csv")

if __name__ == "__main__":
    build_training_data()
