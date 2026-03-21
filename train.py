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

# academic_background_tier (ordinal encode)
edu_map = {
    'Lower secondary': 1,
    'Secondary / secondary special': 2,
    'Incomplete higher': 3,
    'Higher education': 4,
    'Academic degree': 4
}
df_ntc['academic_background_tier'] = df_ntc['NAME_EDUCATION_TYPE'].map(edu_map).fillna(2)

# purpose_of_loan_encoded
income_map = {
    'Working': 1, 'Commercial associate': 2, 'Pensioner': 3,
    'State servant': 4, 'Student': 5, 'Businessman': 6,
    'Maternity leave': 7, 'Unemployed': 8
}
df_ntc['purpose_of_loan_encoded'] = df_ntc['NAME_INCOME_TYPE'].map(income_map).fillna(1)

# utility_payment_consistency — EXT_SOURCE_2 proxy
df_ntc['utility_payment_consistency'] = (
    df_ntc['EXT_SOURCE_2'].fillna(df_ntc['EXT_SOURCE_2'].median()) * 12
).clip(0, 12).round().astype(int)

# avg_utility_dpd — inverse of EXT_SOURCE_1
df_ntc['avg_utility_dpd'] = (
    (1 - df_ntc['EXT_SOURCE_1'].fillna(df_ntc['EXT_SOURCE_1'].median())) * 30
).clip(0, 90)

# rent_wallet_share — annuity / income
df_ntc['rent_wallet_share'] = (
    df_ntc['AMT_ANNUITY'] / df_ntc['AMT_INCOME_TOTAL'].replace(0, np.nan)
).fillna(0).clip(0, 1)

# emergency_buffer_months
df_ntc['emergency_buffer_months'] = (
    df_ntc['AMT_GOODS_PRICE'] / (df_ntc['AMT_INCOME_TOTAL'].replace(0, np.nan) / 12)
).fillna(0).clip(0, 24)

# subscription_commitment_ratio
df_ntc['subscription_commitment_ratio'] = (
    (df_ntc['CNT_FAM_MEMBERS'].fillna(1) * 0.05 +
     df_ntc['AMT_ANNUITY'].fillna(0) / df_ntc['AMT_INCOME_TOTAL'].replace(0, np.nan).fillna(1))
).clip(0, 1)

# employment_vintage_days
df_ntc['employment_vintage_days'] = df_ntc['DAYS_EMPLOYED'].abs().fillna(0)

# bounced_transaction_count proxy
doc_flags = [c for c in df_ntc.columns if c.startswith('FLAG_DOCUMENT')]
df_ntc['bounced_transaction_count'] = df_ntc[doc_flags].sum(axis=1)

# cash_withdrawal_dependency proxy
df_ntc['cash_withdrawal_dependency'] = (
    (df_ntc['NAME_CONTRACT_TYPE'] == 'Cash loans').astype(int) * 0.6 +
    df_ntc['FLAG_OWN_CAR'].map({'Y': 0.2, 'N': 0.0}).fillna(0)
).clip(0, 1)

# eod_balance_volatility proxy
df_ntc['eod_balance_volatility'] = (
    abs(df_ntc['AMT_CREDIT'] - df_ntc['AMT_GOODS_PRICE'].fillna(df_ntc['AMT_CREDIT'])) /
    df_ntc['AMT_CREDIT'].replace(0, np.nan)
).fillna(0).clip(0, 2)

# essential_vs_lifestyle_ratio proxy
df_ntc['essential_vs_lifestyle_ratio'] = (
    df_ntc['REGION_RATING_CLIENT'].fillna(2) / 3.0
)

# telecom_number_vintage_days proxy
df_ntc['telecom_number_vintage_days'] = df_ntc['DAYS_BIRTH'].abs().fillna(365 * 30)

# telecom_recharge_drop_ratio — correlated with EXT_SOURCE_2, no TARGET
rng = np.random.default_rng(seed=42)
n = len(df_ntc)
ext2 = df_ntc['EXT_SOURCE_2'].fillna(0.5).values
df_ntc['telecom_recharge_drop_ratio'] = (
    ext2 + rng.normal(0, 0.1, n)
).clip(0.3, 1.5)

# min_balance_violation_count — derived from DAYS_CREDIT_UPDATE recency proxy
# (no TARGET dependency — uses OWN_CAR_AGE as instability proxy)
df_ntc['min_balance_violation_count'] = (
    (df_ntc['OWN_CAR_AGE'].fillna(0).clip(0, 20) / 4).round().astype(int).clip(0, 5) +
    df_ntc['bounced_transaction_count'].clip(0, 3)
).clip(0, 7)

# ─────────────────────────────────────────────
# 5. FRAUD / TRUST FLAGS (both datasets) — TARGET-FREE
# ─────────────────────────────────────────────
print("\nSTEP 5: Generating trust & forensic flags")

def benford_score(series):
    """Deviation from Benford's Law first-digit distribution."""
    first_digit = pd.to_numeric(
        series.abs().astype(str).str.lstrip('0').str[0],
        errors='coerce'
    ).fillna(1).astype(int).clip(1, 9)
    benford_expected = {1:0.301,2:0.176,3:0.125,4:0.097,5:0.079,
                        6:0.067,7:0.058,8:0.051,9:0.046}
    # Higher deviation = higher anomaly score
    return (1 - first_digit.map(benford_expected).fillna(0.1)).clip(0, 1)

# ── NTC flags (Home Credit columns) ──────────────────────────────────────

df_ntc['benford_anomaly_score'] = benford_score(df_ntc['AMT_CREDIT'])

df_ntc['round_number_spike_ratio'] = (
    (df_ntc['AMT_CREDIT'] % 10000 == 0).astype(float) * 0.6 +
    (df_ntc['AMT_CREDIT'] % 5000  == 0).astype(float) * 0.3 +
    (df_ntc['AMT_CREDIT'] % 1000  == 0).astype(float) * 0.1
).clip(0, 1)

# P2P proxy: high repayment burden + large family = informal cash cycling risk
df_ntc['p2p_circular_loop_flag'] = (
    (df_ntc['AMT_ANNUITY'] / df_ntc['AMT_INCOME_TOTAL'].replace(0, np.nan) > 0.4) &
    (df_ntc['CNT_FAM_MEMBERS'].fillna(1) > 3)
).fillna(False).astype(int)

# Identity mismatch proxy: document submission failures
df_ntc['identity_device_mismatch'] = (
    df_ntc[doc_flags].sum(axis=1) > 3
).astype(int)

# Turnover inflation proxy: credit amount >> goods price (inflated loan)
df_ntc['turnover_inflation_spike'] = (
    (df_ntc['AMT_CREDIT'] > df_ntc['AMT_GOODS_PRICE'].fillna(0) * 1.5)
).astype(int)

print(f"  NTC fraud flag rates: "
      f"p2p={df_ntc['p2p_circular_loop_flag'].mean():.2%} | "
      f"device={df_ntc['identity_device_mismatch'].mean():.2%}")

# ── MSME flags (LendingClub columns) ─────────────────────────────────────

df_msme['benford_anomaly_score'] = benford_score(df_msme['loan_amnt'])

df_msme['round_number_spike_ratio'] = (
    (df_msme['loan_amnt'] % 10000 == 0).astype(float) * 0.6 +
    (df_msme['loan_amnt'] % 5000  == 0).astype(float) * 0.3 +
    (df_msme['loan_amnt'] % 1000  == 0).astype(float) * 0.1
).clip(0, 1)

# P2P proxy: high DTI + low income = informal borrowing risk
df_msme['p2p_circular_loop_flag'] = (
    (df_msme['dti'].fillna(20) > 30) &
    (df_msme['annual_inc'].fillna(0) < 30000)
).astype(int)

# Identity mismatch proxy: very short employment + high loan amount
_revol_bal = pd.to_numeric(df_msme.get('revol_bal', pd.Series(0, index=df_msme.index)), errors='coerce').fillna(0)
df_msme['identity_device_mismatch'] = (
    (_revol_bal > df_msme['annual_inc'].fillna(1) * 0.8)
).astype(int)

# Turnover inflation proxy: loan amount >> stated income supports
df_msme['turnover_inflation_spike'] = (
    (df_msme['loan_amnt'] > df_msme['annual_inc'].fillna(0) * 0.5)
).astype(int)

print(f"  MSME fraud flag rates: "
      f"p2p={df_msme['p2p_circular_loop_flag'].mean():.2%} | "
      f"device={df_msme['identity_device_mismatch'].mean():.2%}")

# Sample weights — fraud flag rows get 3x weight
fraud_cols = ['p2p_circular_loop_flag', 'identity_device_mismatch', 'turnover_inflation_spike']
df_ntc['sample_weight']  = np.where(df_ntc[fraud_cols].any(axis=1),  3.0, 1.0)
df_msme['sample_weight'] = np.where(df_msme[fraud_cols].any(axis=1), 3.0, 1.0)

# ─────────────────────────────────────────────
# 6. MSME FEATURE ENGINEERING
# ─────────────────────────────────────────────
print("\nSTEP 6: Engineering MSME features")

def parse_emp_length(val):
    if pd.isna(val): return np.nan
    val = str(val).strip()
    if '10+' in val: return 120
    if '< 1' in val: return 6
    digits = ''.join(filter(str.isdigit, val))
    return int(digits) * 12 if digits else np.nan

df_msme['business_vintage_months'] = df_msme['emp_length'].apply(parse_emp_length).fillna(24)

df_msme['operating_cashflow_ratio'] = (
    1 / (df_msme['dti'].replace(0, np.nan).fillna(20) / 100 + 0.01)
).clip(0.5, 10)

_revol = df_msme['revol_util']
if _revol.dtype == object:
    _revol = _revol.str.rstrip('%').astype(float, errors='ignore')
df_msme['cashflow_volatility'] = (
    pd.to_numeric(_revol, errors='coerce').fillna(50) / 100
)

# revenue_growth_trend — from loan grade (structural, not TARGET-derived)
grade_map = {'A': 0.15, 'B': 0.10, 'C': 0.05, 'D': 0.0, 'E': -0.05, 'F': -0.10, 'G': -0.15}
df_msme['revenue_growth_trend'] = df_msme['grade'].map(grade_map).fillna(0.0)

df_msme['gst_filing_consistency_score'] = (
    pd.to_numeric(df_msme['mo_sin_old_il_acct'], errors='coerce').fillna(12).clip(0, 24).astype(int)
    if 'mo_sin_old_il_acct' in df_msme.columns
    else pd.Series(np.random.default_rng(42).integers(4, 24, len(df_msme)), index=df_msme.index)
)

df_msme['customer_concentration_ratio'] = (
    1 / df_msme['open_acc'].replace(0, np.nan).fillna(3)
).clip(0, 1)

df_msme['monthly_income'] = df_msme['annual_inc'].fillna(0) / 12

df_msme['rent_wallet_share'] = (
    df_msme['installment'] / df_msme['monthly_income'].replace(0, np.nan)
).fillna(0).clip(0, 1)

df_msme['academic_background_tier'] = np.random.default_rng(42).integers(2, 5, len(df_msme))
df_msme['purpose_of_loan_encoded'] = 6

df_msme['avg_invoice_payment_delay']   = np.nan
df_msme['vendor_payment_discipline']   = np.nan
df_msme['repeat_customer_revenue_pct'] = np.nan
df_msme['gst_to_bank_variance']        = np.nan

# ─────────────────────────────────────────────
# 7. DEFINE FINAL FEATURE SETS
# ─────────────────────────────────────────────

NTC_FEATURES = [
    'utility_payment_consistency', 'avg_utility_dpd',
    'rent_wallet_share', 'subscription_commitment_ratio',
    'emergency_buffer_months', 'min_balance_violation_count',
    'eod_balance_volatility', 'essential_vs_lifestyle_ratio',
    'cash_withdrawal_dependency', 'bounced_transaction_count',
    'telecom_number_vintage_days', 'telecom_recharge_drop_ratio',
    'academic_background_tier', 'purpose_of_loan_encoded',
    'p2p_circular_loop_flag', 'identity_device_mismatch',
    'turnover_inflation_spike', 'benford_anomaly_score',
    'round_number_spike_ratio',
    'employment_vintage_days', 'is_msme',
]

MSME_FEATURES = [
    'business_vintage_months', 'revenue_growth_trend',
    'operating_cashflow_ratio', 'cashflow_volatility',
    'customer_concentration_ratio',
    'gst_filing_consistency_score',
    'rent_wallet_share', 'academic_background_tier',
    'purpose_of_loan_encoded', 'monthly_income',
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
    scale_pos_weight=11.4,
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

ntc_explainer  = shap.TreeExplainer(ntc_model)
ntc_shap_vals  = ntc_explainer.shap_values(X_val.iloc[:500])

msme_explainer = shap.TreeExplainer(msme_model)
msme_shap_vals = msme_explainer.shap_values(X_mval.iloc[:200])

def get_reason_codes(shap_row, feature_names, top_n=3):
    pairs = list(zip(shap_row, feature_names))
    sorted_pairs = sorted(pairs, key=lambda x: abs(x[0]), reverse=True)
    risk_drivers     = [(f, round(v, 4)) for v, f in sorted_pairs if v > 0][:top_n]
    strength_factors = [(f, round(v, 4)) for v, f in sorted_pairs if v < 0][:top_n]
    return {'risk_drivers': risk_drivers, 'strength_factors': strength_factors}

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

joblib.dump(ntc_model,     'pdr_ntc_model.pkl')
joblib.dump(msme_model,    'pdr_msme_model.pkl')
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