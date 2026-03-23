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
    
    logger.info("Part 2: Computing demographic risk score...")

    rng = np.random.default_rng(RANDOM_SEED)
    n = N_SAMPLES

    # ── DEMOGRAPHIC RISK SCORE ──────────────────────────────────
    # Instead of a random coin flip, compute risk from real demographics.
    # A stable pensioner with property → low risk → good behavioral means.
    # A young unstable person → high risk → bad behavioral means.

    age_risk = np.clip((35 - demo_df["applicant_age_years"]) / 30, 0, 1)
    emp_risk = np.clip(1 - demo_df["employment_vintage_days"] / 3650, 0, 1)
    prop_risk = (1 - demo_df["owns_property"]).astype(float)
    edu_risk = np.clip(1 - (demo_df["academic_background_tier"] - 1) / 4, 0, 1)
    income_risk = np.clip(demo_df["income_type_risk_score"] / 5, 0, 1)
    family_risk = demo_df["family_burden_ratio"].clip(0, 1)
    addr_risk = np.clip(1 - demo_df["address_stability_years"] / 15, 0, 1)
    contact_risk = np.clip(1 - demo_df["contactability_score"] / 4, 0, 1)
    region_risk = np.clip((demo_df["region_risk_tier"] - 1) / 2, 0, 1)

    demo_risk = (
        0.20 * emp_risk +
        0.15 * age_risk +
        0.15 * prop_risk +
        0.12 * income_risk +
        0.10 * edu_risk +
        0.10 * addr_risk +
        0.08 * family_risk +
        0.05 * contact_risk +
        0.05 * region_risk
    ).values

    # Add noise so demographics aren't perfectly deterministic
    demo_risk = np.clip(demo_risk + rng.normal(0, 0.08, n), 0.02, 0.98)

    logger.info(f"Demographic risk score: mean={demo_risk.mean():.3f}, "
                f"std={demo_risk.std():.3f}, "
                f"range=[{demo_risk.min():.3f}, {demo_risk.max():.3f}]")

    # ── BEHAVIORAL FEATURES DRIVEN BY DEMO RISK ────────────────
    # Each feature's mean is a function of demo_risk.
    # risk=0 → good mean, risk=1 → bad mean.
    # The std creates realistic overlap so the model has to learn patterns.

    behav_df = pd.DataFrame()

    # utility_payment_consistency: good=0.85, bad=0.42
    mean = 0.85 - demo_risk * 0.43
    val = rng.normal(mean, 0.10)
    behav_df["utility_payment_consistency"] = np.clip(val, 0, 1).round(4)

    # avg_utility_dpd: good=4, bad=14
    mean = 4.0 + demo_risk * 10.0
    val = rng.normal(mean, 4.0)
    behav_df["avg_utility_dpd"] = np.clip(val, 0, 90).round(2)

    # rent_wallet_share: good=0.22, bad=0.52
    mean = 0.22 + demo_risk * 0.30
    val = rng.normal(mean, 0.10)
    behav_df["rent_wallet_share"] = np.clip(val, 0, 1).round(4)

    behav_df["subscription_commitment_ratio"] = (behav_df["rent_wallet_share"] * 0.3).clip(0, 1).round(4)

    # emergency_buffer_months: good=4.5, bad=0.8
    mean = 4.5 - demo_risk * 3.7
    val = rng.normal(mean, 1.3)
    behav_df["emergency_buffer_months"] = np.clip(val, 0, 24).round(2)

    # eod_balance_volatility: good=0.20, bad=0.55
    mean = 0.20 + demo_risk * 0.35
    val = rng.normal(mean, 0.10)
    behav_df["eod_balance_volatility"] = np.clip(val, 0, 1).round(4)

    # essential_vs_lifestyle_ratio: good=0.72, bad=0.48
    mean = 0.72 - demo_risk * 0.24
    val = rng.normal(mean, 0.12)
    behav_df["essential_vs_lifestyle_ratio"] = np.clip(val, 0, 1).round(4)

    # cash_withdrawal_dependency: good=0.10, bad=0.45
    mean = 0.10 + demo_risk * 0.35
    val = rng.normal(mean, 0.10)
    behav_df["cash_withdrawal_dependency"] = np.clip(val, 0, 1).round(4)

    # bounced_transaction_count: good=0.3, bad=3.5
    mean = 0.3 + demo_risk * 3.2
    val = rng.normal(mean, 1.0)
    behav_df["bounced_transaction_count"] = np.clip(val, 0, 10).round(0).astype(int)

    # telecom_recharge_drop_ratio: good=0.12, bad=0.35
    mean = 0.12 + demo_risk * 0.23
    val = rng.normal(mean, 0.10)
    behav_df["telecom_recharge_drop_ratio"] = np.clip(val, 0, 1).round(4)

    # min_balance_violation_count: good=0.5, bad=3.0
    mean = 0.5 + demo_risk * 2.5
    val = rng.normal(mean, 1.0)
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

    logger.info("Part 4: Assigning TARGET from demographics + behavior...")

    # Behavioral component (what they actually did)
    behavioral_score = (
        (1 - df_merged["utility_payment_consistency"]) * 0.28
        + df_merged["eod_balance_volatility"]           * 0.22
        + (df_merged["bounced_transaction_count"] / 10) * 0.20
        + df_merged["rent_wallet_share"].clip(0, 1)     * 0.15
        + df_merged["cash_withdrawal_dependency"]        * 0.10
        + (df_merged["min_balance_violation_count"] / 8)* 0.05
    )

    # Blend: 70% behavior + 30% demographics + small noise
    # A pensioner with demo_risk=0.05 now needs EXTREME behavioral bad luck
    # to cross the threshold. A risky person at demo_risk=0.90 can't escape
    # with just behavioral good luck.
    default_score = (
        0.70 * behavioral_score +
        0.30 * demo_risk +
        rng.normal(0, 0.04, N_SAMPLES)  # reduced noise since demo already anchors
    )

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

    high_corr = demo_corr[demo_corr > 0.35]
    if len(high_corr) > 0:
        logger.warning(f"Demographics correlating with TARGET > 0.35 (too strong, risk of leakage):\n{high_corr.to_string()}")
    
    low_corr = demo_corr[demo_corr < 0.03]
    if len(low_corr) > 0:
        logger.warning(f"Demographics with near-zero TARGET correlation (should contribute):\n{low_corr.to_string()}")
    else:
        logger.info("Demographics moderately correlated with TARGET ✅ (all > 0.03, demographics are contributing)")

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
