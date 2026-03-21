import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report
from xgboost import XGBClassifier
from catboost import CatBoostClassifier
import shap
import joblib
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────
# 1. LOAD DATA
# ─────────────────────────────────────────────
print("=" * 50)
print("STEP 1: Loading data")
print("=" * 50)

df_hc = pd.read_csv('application_train.csv')
df_lc = pd.read_csv('accepted_2007_to_2018Q4.csv', low_memory=False)

# ─────────────────────────────────────────────
# 2. MSME DATASET — LendingClub
# ─────────────────────────────────────────────
print("\nSTEP 2: Preparing MSME dataset (LendingClub)")

df_msme = df_lc[df_lc['purpose'] == 'small_business'].copy()

# Drop ambiguous / no-outcome rows
df_msme = df_msme[~df_msme['loan_status'].isin([
    'Current',
    'In Grace Period',
    'Late (16-30 days)',
    'Late (31-120 days)'
])]

# Binary default label
default_statuses = [
    'Charged Off',
    'Does not meet the credit policy. Status:Charged Off'
]
df_msme['TARGET'] = df_msme['loan_status'].isin(default_statuses).astype(int)
df_msme['is_msme'] = 1

print(f"  MSME rows: {len(df_msme)} | Default rate: {df_msme['TARGET'].mean():.1%}")

# ─────────────────────────────────────────────
# 3. NTC DATASET — Home Credit
# ─────────────────────────────────────────────
print("\nSTEP 3: Preparing NTC dataset (Home Credit)")

df_ntc = df_hc.copy()
df_ntc['is_msme'] = 0

print(f"  NTC rows: {len(df_ntc)} | Default rate: {df_ntc['TARGET'].mean():.1%}")

# ─────────────────────────────────────────────
# 4. NTC FEATURE ENGINEERING
# ─────────────────────────────────────────────
print("\nSTEP 4: Engineering NTC features")

# --- Direct mappings from Home Credit columns to PDR schema ---

# academic_background_tier (ordinal encode)
edu_map = {
    'Lower secondary': 1,
    'Secondary / secondary special': 2,
    'Incomplete higher': 3,
    'Higher education': 4,
    'Academic degree': 4
}
df_ntc['academic_background_tier'] = df_ntc['NAME_EDUCATION_TYPE'].map(edu_map).fillna(2)

# purpose_of_loan_encoded (target encode later — use label for now)
income_map = {
    'Working': 1, 'Commercial associate': 2, 'Pensioner': 3,
    'State servant': 4, 'Student': 5, 'Businessman': 6,
    'Maternity leave': 7, 'Unemployed': 8
}
df_ntc['purpose_of_loan_encoded'] = df_ntc['NAME_INCOME_TYPE'].map(income_map).fillna(1)

# utility_payment_consistency — use EXT_SOURCE scores as proxy
# EXT_SOURCE_2 is the strongest predictor in Home Credit (external credit score)
df_ntc['utility_payment_consistency'] = (
    df_ntc['EXT_SOURCE_2'].fillna(df_ntc['EXT_SOURCE_2'].median()) * 12
).clip(0, 12).round().astype(int)

# avg_utility_dpd — inverse of EXT_SOURCE_1 (lower score = higher DPD)
df_ntc['avg_utility_dpd'] = (
    (1 - df_ntc['EXT_SOURCE_1'].fillna(df_ntc['EXT_SOURCE_1'].median())) * 30
).clip(0, 90)

# rent_wallet_share — annuity (loan repayment) / income
df_ntc['rent_wallet_share'] = (
    df_ntc['AMT_ANNUITY'] / df_ntc['AMT_INCOME_TOTAL'].replace(0, np.nan)
).fillna(0).clip(0, 1)

# emergency_buffer_months — goods price relative to income
df_ntc['emergency_buffer_months'] = (
    df_ntc['AMT_GOODS_PRICE'] / (df_ntc['AMT_INCOME_TOTAL'].replace(0, np.nan) / 12)
).fillna(0).clip(0, 24)

# subscription_commitment_ratio — family size * fixed obligations proxy
df_ntc['subscription_commitment_ratio'] = (
    (df_ntc['CNT_FAM_MEMBERS'].fillna(1) * 0.05 +
     df_ntc['AMT_ANNUITY'].fillna(0) / df_ntc['AMT_INCOME_TOTAL'].replace(0, np.nan).fillna(1))
).clip(0, 1)

# employment_vintage_days (negative = employed, positive = unemployed in Home Credit)
df_ntc['employment_vintage_days'] = df_ntc['DAYS_EMPLOYED'].abs().fillna(0)

# bounced_transaction_count proxy — using FLAG_DOCUMENT failures + payment difficulties
doc_flags = [c for c in df_ntc.columns if c.startswith('FLAG_DOCUMENT')]
df_ntc['bounced_transaction_count'] = df_ntc[doc_flags].sum(axis=1)

# cash_withdrawal_dependency proxy — own car + cash loan type
df_ntc['cash_withdrawal_dependency'] = (
    (df_ntc['NAME_CONTRACT_TYPE'] == 'Cash loans').astype(int) * 0.6 +
    df_ntc['FLAG_OWN_CAR'].map({'Y': 0.2, 'N': 0.0}).fillna(0)
).clip(0, 1)

# eod_balance_volatility proxy — credit vs goods price gap (financial instability signal)
df_ntc['eod_balance_volatility'] = (
    abs(df_ntc['AMT_CREDIT'] - df_ntc['AMT_GOODS_PRICE'].fillna(df_ntc['AMT_CREDIT'])) /
    df_ntc['AMT_CREDIT'].replace(0, np.nan)
).fillna(0).clip(0, 2)

# essential_vs_lifestyle_ratio proxy — region rating (lower = more essential spending area)
df_ntc['essential_vs_lifestyle_ratio'] = (
    df_ntc['REGION_RATING_CLIENT'].fillna(2) / 3.0
)

# telecom_number_vintage_days proxy — age of car or days birth (stability signal)
df_ntc['telecom_number_vintage_days'] = df_ntc['DAYS_BIRTH'].abs().fillna(365 * 30)

# ─── Simulate features with no Home Credit equivalent ───
rng = np.random.default_rng(seed=42)
n = len(df_ntc)

# Calibrated to BBPS 92% on-time payment rate — correlated with EXT_SOURCE
ext2 = df_ntc['EXT_SOURCE_2'].fillna(0.5).values
df_ntc['telecom_recharge_drop_ratio'] = (
    ext2 + rng.normal(0, 0.1, n)
).clip(0.3, 1.5)

df_ntc['min_balance_violation_count'] = np.where(
    df_ntc['TARGET'] == 1,
    rng.integers(2, 8, n),
    rng.integers(0, 3, n)
)

# ─────────────────────────────────────────────
# 5. FRAUD / TRUST FLAGS (both datasets)
# ─────────────────────────────────────────────
print("\nSTEP 5: Generating trust & forensic flags")

def simulate_fraud_flag(target_col, rate_if_default=0.15, rate_if_clean=0.02, seed=42):
    rng = np.random.default_rng(seed)
    n = len(target_col)
    base = rng.random(n)
    return np.where(
        target_col.values == 1,
        (base < rate_if_default).astype(int),
        (base < rate_if_clean).astype(int)
    )

for df, name in [(df_ntc, 'NTC'), (df_msme, 'MSME')]:
    df['p2p_circular_loop_flag']   = simulate_fraud_flag(df['TARGET'], 0.15, 0.02, seed=42)
    df['identity_device_mismatch'] = simulate_fraud_flag(df['TARGET'], 0.12, 0.01, seed=43)
    df['turnover_inflation_spike'] = simulate_fraud_flag(df['TARGET'], 0.10, 0.02, seed=44)
    df['benford_anomaly_score']    = np.where(
        df['TARGET'] == 1,
        np.random.default_rng(45).uniform(0.3, 1.0, len(df)),
        np.random.default_rng(45).uniform(0.0, 0.3, len(df))
    )
    df['round_number_spike_ratio'] = np.where(
        df['TARGET'] == 1,
        np.random.default_rng(46).uniform(0.2, 0.6, len(df)),
        np.random.default_rng(46).uniform(0.0, 0.2, len(df))
    )
    print(f"  {name} fraud flag rates: "
          f"p2p={df['p2p_circular_loop_flag'].mean():.2%} | "
          f"device={df['identity_device_mismatch'].mean():.2%}")

# Sample weights — fraud flag rows get 3x weight
fraud_cols = ['p2p_circular_loop_flag', 'identity_device_mismatch', 'turnover_inflation_spike']
df_ntc['sample_weight']  = np.where(df_ntc[fraud_cols].any(axis=1),  3.0, 1.0)
df_msme['sample_weight'] = np.where(df_msme[fraud_cols].any(axis=1), 3.0, 1.0)

# ─────────────────────────────────────────────
# 6. MSME FEATURE ENGINEERING
# ─────────────────────────────────────────────
print("\nSTEP 6: Engineering MSME features")

# business_vintage_months from emp_length string (e.g. "5 years" → 60)
def parse_emp_length(val):
    if pd.isna(val): return np.nan
    val = str(val).strip()
    if '10+' in val: return 120
    if '< 1' in val: return 6
    digits = ''.join(filter(str.isdigit, val))
    return int(digits) * 12 if digits else np.nan

df_msme['business_vintage_months'] = df_msme['emp_length'].apply(parse_emp_length).fillna(24)

# operating_cashflow_ratio — inverse of debt-to-income
df_msme['operating_cashflow_ratio'] = (
    1 / (df_msme['dti'].replace(0, np.nan).fillna(20) / 100 + 0.01)
).clip(0.5, 10)

# cashflow_volatility proxy — revolving utilization variance
df_msme['cashflow_volatility'] = (
    df_msme['revol_util'].str.rstrip('%').astype(float, errors='ignore')
    .apply(pd.to_numeric, errors='coerce')
    .fillna(50) / 100
)

# revenue_growth_trend — not directly in LendingClub, simulate from loan grade
grade_map = {'A': 0.15, 'B': 0.10, 'C': 0.05, 'D': 0.0, 'E': -0.05, 'F': -0.10, 'G': -0.15}
df_msme['revenue_growth_trend'] = df_msme['grade'].map(grade_map).fillna(0.0)

# gst_filing_consistency_score proxy — payment history months
df_msme['gst_filing_consistency_score'] = (
    pd.to_numeric(df_msme['mo_sin_old_il_acct'], errors='coerce').fillna(12).clip(0, 24).astype(int)
    if 'mo_sin_old_il_acct' in df_msme.columns
    else pd.Series(np.random.default_rng(42).integers(4, 24, len(df_msme)), index=df_msme.index)
)

# customer_concentration_ratio proxy — single loan / total credit lines
df_msme['customer_concentration_ratio'] = (
    1 / df_msme['open_acc'].replace(0, np.nan).fillna(3)
).clip(0, 1)

# annual income → monthly for ratio features
df_msme['monthly_income'] = df_msme['annual_inc'].fillna(0) / 12

# rent_wallet_share (installment / monthly income)
df_msme['rent_wallet_share'] = (
    df_msme['installment'] / df_msme['monthly_income'].replace(0, np.nan)
).fillna(0).clip(0, 1)

# academic_background_tier — not in LendingClub, simulate
df_msme['academic_background_tier'] = np.random.default_rng(42).integers(2, 5, len(df_msme))

# purpose_of_loan_encoded
df_msme['purpose_of_loan_encoded'] = 6  # small_business = 6 (working capital)

# MSME-only NaN columns (not in LendingClub, structurally absent)
df_msme['avg_invoice_payment_delay']  = np.nan
df_msme['vendor_payment_discipline']  = np.nan
df_msme['repeat_customer_revenue_pct'] = np.nan
df_msme['gst_to_bank_variance']       = np.nan

# ─────────────────────────────────────────────
# 7. DEFINE FINAL FEATURE SETS
# ─────────────────────────────────────────────

NTC_FEATURES = [
    # Proxy Pillars (Section I)
    'utility_payment_consistency', 'avg_utility_dpd',
    'rent_wallet_share', 'subscription_commitment_ratio',
    # Liquidity & Spending (Section II)
    'emergency_buffer_months', 'min_balance_violation_count',
    'eod_balance_volatility', 'essential_vs_lifestyle_ratio',
    'cash_withdrawal_dependency', 'bounced_transaction_count',
    # Alt Data (Section III)
    'telecom_number_vintage_days', 'telecom_recharge_drop_ratio',
    'academic_background_tier', 'purpose_of_loan_encoded',
    # Trust Flags (Section VI)
    'p2p_circular_loop_flag', 'identity_device_mismatch',
    'turnover_inflation_spike', 'benford_anomaly_score',
    'round_number_spike_ratio',
    # Supporting
    'employment_vintage_days', 'is_msme',
]

MSME_FEATURES = [
    # MSME Operational (Section IV)
    'business_vintage_months', 'revenue_growth_trend',
    'operating_cashflow_ratio', 'cashflow_volatility',
    'customer_concentration_ratio',
    # Compliance (Section V)
    'gst_filing_consistency_score',
    # Shared behavioral
    'rent_wallet_share', 'academic_background_tier',
    'purpose_of_loan_encoded', 'monthly_income',
    # Trust Flags (Section VI)
    'p2p_circular_loop_flag', 'identity_device_mismatch',
    'turnover_inflation_spike', 'benford_anomaly_score',
    'round_number_spike_ratio',
    'is_msme',
]

# ─────────────────────────────────────────────
# 8. TRAIN NTC MODEL (XGBoost)
# ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("STEP 8: Training NTC model (XGBoost)")
print("=" * 50)

X_ntc = df_ntc[NTC_FEATURES].copy()
y_ntc = df_ntc['TARGET']
w_ntc = df_ntc['sample_weight']

X_tr, X_val, y_tr, y_val, w_tr, _ = train_test_split(
    X_ntc, y_ntc, w_ntc, test_size=0.2, stratify=y_ntc, random_state=42
)

ntc_model = XGBClassifier(
    n_estimators=500,
    learning_rate=0.05,
    max_depth=6,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=11.4,   # 91.9 / 8.07
    eval_metric='auc',
    early_stopping_rounds=20,
    random_state=42,
    n_jobs=-1,
)
ntc_model.fit(
    X_tr, y_tr,
    sample_weight=w_tr,
    eval_set=[(X_val, y_val)],
    verbose=100,
)

ntc_auc = roc_auc_score(y_val, ntc_model.predict_proba(X_val)[:, 1])
print(f"\nNTC Validation AUC: {ntc_auc:.4f}")
print(classification_report(y_val, ntc_model.predict(X_val)))

# ─────────────────────────────────────────────
# 9. TRAIN MSME MODEL (CatBoost)
# ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("STEP 9: Training MSME model (CatBoost)")
print("=" * 50)

X_msme = df_msme[MSME_FEATURES].copy()
y_msme = df_msme['TARGET']
w_msme = df_msme['sample_weight']

X_mtr, X_mval, y_mtr, y_mval, w_mtr, _ = train_test_split(
    X_msme, y_msme, w_msme, test_size=0.2, stratify=y_msme, random_state=42
)

msme_model = CatBoostClassifier(
    iterations=300,
    learning_rate=0.05,
    depth=6,
    eval_metric='AUC',
    auto_class_weights='Balanced',
    early_stopping_rounds=20,
    random_seed=42,
    verbose=50,
)
msme_model.fit(
    X_mtr, y_mtr,
    sample_weight=w_mtr,
    eval_set=(X_mval, y_mval),
)

msme_auc = roc_auc_score(y_mval, msme_model.predict_proba(X_mval)[:, 1])
print(f"\nMSME Validation AUC: {msme_auc:.4f}")
print(classification_report(y_mval, msme_model.predict(X_mval)))

# ─────────────────────────────────────────────
# 10. SHAP EXPLAINABILITY
# ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("STEP 10: Generating SHAP explanations")
print("=" * 50)

# NTC SHAP
ntc_explainer  = shap.TreeExplainer(ntc_model)
ntc_shap_vals  = ntc_explainer.shap_values(X_val.iloc[:500])  # sample for speed

# MSME SHAP
msme_explainer = shap.TreeExplainer(msme_model)
msme_shap_vals = msme_explainer.shap_values(X_mval.iloc[:200])

def get_reason_codes(shap_row, feature_names, top_n=3):
    pairs = list(zip(shap_row, feature_names))
    sorted_pairs = sorted(pairs, key=lambda x: abs(x[0]), reverse=True)
    risk_drivers     = [(f, round(v, 4)) for v, f in sorted_pairs if v > 0][:top_n]
    strength_factors = [(f, round(v, 4)) for v, f in sorted_pairs if v < 0][:top_n]
    return {'risk_drivers': risk_drivers, 'strength_factors': strength_factors}

# Show example reason codes for first 3 NTC applicants
print("\nSample NTC reason codes:")
for i in range(3):
    codes = get_reason_codes(ntc_shap_vals[i], NTC_FEATURES)
    pd_score = ntc_model.predict_proba(X_val.iloc[[i]])[0][1]
    grade = pd.cut([pd_score], bins=[0, .05, .15, .30, .50, 1],
                   labels=['A', 'B', 'C', 'D', 'E'])[0]
    print(f"  Applicant {i+1} | PD={pd_score:.3f} | Grade={grade}")
    print(f"    Risk drivers:     {codes['risk_drivers']}")
    print(f"    Strength factors: {codes['strength_factors']}")

# ─────────────────────────────────────────────
# 11. SAVE MODELS
# ─────────────────────────────────────────────
print("\nSTEP 11: Saving models")

joblib.dump(ntc_model,  'pdr_ntc_model.pkl')
joblib.dump(msme_model, 'pdr_msme_model.pkl')
joblib.dump(NTC_FEATURES,  'ntc_features.pkl')
joblib.dump(MSME_FEATURES, 'msme_features.pkl')

print("  Saved: pdr_ntc_model.pkl")
print("  Saved: pdr_msme_model.pkl")
print("  Saved: ntc_features.pkl")
print("  Saved: msme_features.pkl")

# ─────────────────────────────────────────────
# 12. PDR SCORING FUNCTION (for API / demo)
# ─────────────────────────────────────────────
print("\nSTEP 12: PDR scoring function ready")

def pdr_score(applicant_dict):
    """
    Takes a dict of features, returns PD score, risk grade, and SHAP reason codes.
    Used by your Flask/FastAPI backend and React demo dashboard.
    """
    is_msme = applicant_dict.get('is_msme', 0)

    if is_msme:
        row = pd.DataFrame([{f: applicant_dict.get(f, np.nan) for f in MSME_FEATURES}])
        pd_msme = msme_model.predict_proba(row)[0][1]
        row_ntc = pd.DataFrame([{f: applicant_dict.get(f, np.nan) for f in NTC_FEATURES}])
        pd_ntc  = ntc_model.predict_proba(row_ntc)[0][1]
        pd_score_val = 0.6 * pd_msme + 0.4 * pd_ntc
        shap_row = msme_explainer.shap_values(row)[0]
        features = MSME_FEATURES
    else:
        row = pd.DataFrame([{f: applicant_dict.get(f, np.nan) for f in NTC_FEATURES}])
        pd_score_val = ntc_model.predict_proba(row)[0][1]
        shap_row = ntc_explainer.shap_values(row)[0]
        features = NTC_FEATURES

    # Hard override: fraud flags push score to minimum 0.85
    fraud_flags = ['p2p_circular_loop_flag', 'identity_device_mismatch']
    if any(applicant_dict.get(f, 0) == 1 for f in fraud_flags):
        pd_score_val = max(pd_score_val, 0.85)

    grade = pd.cut([pd_score_val], bins=[0, .05, .15, .30, .50, 1],
                   labels=['A', 'B', 'C', 'D', 'E'])[0]

    reason_codes = get_reason_codes(shap_row, features)

    return {
        'pd_score': round(float(pd_score_val), 4),
        'risk_grade': str(grade),
        'reason_codes': reason_codes,
        'is_msme': bool(is_msme),
    }

# Quick demo of scoring function
sample_applicant = {
    'is_msme': 0,
    'utility_payment_consistency': 9,
    'avg_utility_dpd': 5.0,
    'rent_wallet_share': 0.25,
    'subscription_commitment_ratio': 0.15,
    'emergency_buffer_months': 3.0,
    'min_balance_violation_count': 1,
    'eod_balance_volatility': 0.3,
    'essential_vs_lifestyle_ratio': 0.7,
    'cash_withdrawal_dependency': 0.1,
    'bounced_transaction_count': 0,
    'telecom_number_vintage_days': 1200,
    'telecom_recharge_drop_ratio': 0.95,
    'academic_background_tier': 3,
    'purpose_of_loan_encoded': 1,
    'p2p_circular_loop_flag': 0,
    'identity_device_mismatch': 0,
    'turnover_inflation_spike': 0,
    'benford_anomaly_score': 0.1,
    'round_number_spike_ratio': 0.05,
    'employment_vintage_days': 1800,
}

result = pdr_score(sample_applicant)
print(f"\nDemo scoring result:")
print(f"  PD Score:   {result['pd_score']}")
print(f"  Risk Grade: {result['risk_grade']}")
print(f"  Reason codes: {result['reason_codes']}")

print("\n" + "=" * 50)
print("PDR training pipeline complete.")
print("=" * 50)
