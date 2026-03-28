"""
AUDIT: NTC Model Feature Usage & Training Data Quality
Validates all training datasets, features, mappings, and model integrity.
"""
import pandas as pd
import numpy as np
import joblib
import os
from pathlib import Path

# ============================================================================
# CONFIG
# ============================================================================

DATASETS_PATH = Path(r"C:\Users\kanis\OneDrive\Desktop\ecirricula\datasets")
REPO_PATH = Path(r"C:\Users\kanis\OneDrive\Documents\alternative_credit_scoring")

f = open(REPO_PATH / "audit_report.txt", "w", encoding="utf-8")
def p(t=""): f.write(t + "\n"); print(t)

p("=" * 80)
p("NTC MODEL FEATURE USAGE AUDIT")
p("=" * 80)
p(f"\n[CONFIG]")
p(f"  Datasets path: {DATASETS_PATH}")
p(f"  Repo path: {REPO_PATH}")

# ============================================================================
# STEP 1: Load Training Data Sources
# ============================================================================
p(f"\n{'=' * 80}")
p("STEP 1: LOAD SOURCE DATASETS")
p(f"{'=' * 80}")

# 1.1 cs-training.csv
cs_path = DATASETS_PATH / "new dataset" / "archive (1)" / "cs-training.csv"
p(f"\n[1.1] cs-training.csv (Kaggle 'Give Me Some Credit')")
p(f"      Path: {cs_path}")
p(f"      Exists: {cs_path.exists()}")

cs_df = None
if cs_path.exists():
    cs_df = pd.read_csv(cs_path)
    p(f"      Shape: {cs_df.shape}")
    p(f"      Columns ({len(cs_df.columns)}):")
    for i, col in enumerate(cs_df.columns, 1):
        nulls = cs_df[col].isnull().sum()
        null_pct = nulls / len(cs_df) * 100
        uniq = cs_df[col].nunique()
        p(f"        {i:2d}. {col:45s} | {str(cs_df[col].dtype):8s} | nulls: {nulls:6d} ({null_pct:5.1f}%) | unique: {uniq:6d}")
    
    # Target distribution
    if 'SeriousDlqin2yrs' in cs_df.columns:
        tgt = cs_df['SeriousDlqin2yrs']
        p(f"\n      TARGET ('SeriousDlqin2yrs') distribution:")
        p(f"        0 (non-default): {(tgt == 0).sum():6d} ({(tgt == 0).mean() * 100:.1f}%)")
        p(f"        1 (default):     {(tgt == 1).sum():6d} ({(tgt == 1).mean() * 100:.1f}%)")
else:
    p(f"      NOT FOUND")

# 1.2 application_train.csv
app_path = DATASETS_PATH / "new dataset" / "archive (1)" / "application_train.csv"
if not app_path.exists():
    app_path = REPO_PATH / "application_train.csv"
p(f"\n[1.2] application_train.csv (Home Credit demographics)")
p(f"      Path: {app_path}")
p(f"      Exists: {app_path.exists()}")

app_df = None
if app_path.exists():
    app_df = pd.read_csv(app_path, nrows=5000)
    full_shape = pd.read_csv(app_path, nrows=0)
    p(f"      Columns: {len(full_shape.columns)}")
    p(f"      Sample rows loaded: {len(app_df)}")
    
    key_demo_cols = ['SK_ID_CURR', 'TARGET', 'DAYS_BIRTH', 'DAYS_EMPLOYED', 'AMT_INCOME_TOTAL',
                     'NAME_EDUCATION_TYPE', 'FLAG_OWN_CAR', 'FLAG_OWN_REALTY', 'CNT_CHILDREN',
                     'REGION_RATING_CLIENT', 'DAYS_REGISTRATION', 'DAYS_ID_PUBLISH']
    p(f"      Key demographic columns:")
    for col in key_demo_cols:
        exists = col in app_df.columns
        status = "OK" if exists else "MISSING"
        if exists:
            p(f"        {col:40s} | {status} | sample: {app_df[col].iloc[0]}")
        else:
            p(f"        {col:40s} | {status}")
else:
    p(f"      NOT FOUND")

# 1.3 loan_dataset_20000.csv
loan_path = DATASETS_PATH / "new dataset" / "archive (1)" / "loan_dataset_20000.csv"
p(f"\n[1.3] loan_dataset_20000.csv")
p(f"      Path: {loan_path}")
p(f"      Exists: {loan_path.exists()}")
if loan_path.exists():
    loan_df = pd.read_csv(loan_path, nrows=5)
    p(f"      Columns: {list(loan_df.columns)}")

# ============================================================================
# STEP 2: Check Generated Training Data
# ============================================================================
p(f"\n{'=' * 80}")
p("STEP 2: NTC TRAINING DATA (GENERATED)")
p(f"{'=' * 80}")

train_csv = REPO_PATH / "ntc_model" / "datasets" / "ntc_credit_training_v2.csv"
p(f"\n[2.1] ntc_credit_training_v2.csv")
p(f"      Path: {train_csv}")
p(f"      Exists: {train_csv.exists()}")

ntc_df = None
if train_csv.exists():
    ntc_df = pd.read_csv(train_csv)
    p(f"      Shape: {ntc_df.shape}")
    p(f"      Columns ({len(ntc_df.columns)}):")
    
    for i, col in enumerate(ntc_df.columns, 1):
        dtype = str(ntc_df[col].dtype)
        nulls = ntc_df[col].isnull().sum()
        if ntc_df[col].dtype in ['float64', 'int64']:
            mn = ntc_df[col].min()
            mx = ntc_df[col].max()
            mean = ntc_df[col].mean()
            std = ntc_df[col].std()
            p(f"        {i:2d}. {col:40s} | {dtype:8s} | nulls:{nulls:4d} | [{mn:10.4f}, {mx:10.4f}] | mean:{mean:8.4f} | std:{std:8.4f}")
        else:
            p(f"        {i:2d}. {col:40s} | {dtype:8s} | nulls:{nulls:4d}")
    
    # TARGET distribution
    if 'TARGET' in ntc_df.columns:
        tgt = ntc_df['TARGET']
        p(f"\n      TARGET distribution:")
        p(f"        0 (non-default): {(tgt == 0).sum():6d} ({(tgt == 0).mean() * 100:.1f}%)")
        p(f"        1 (default):     {(tgt == 1).sum():6d} ({(tgt == 1).mean() * 100:.1f}%)")
else:
    p(f"      NOT FOUND")

# ============================================================================
# STEP 3: Load Trained Model & Extract Features
# ============================================================================
p(f"\n{'=' * 80}")
p("STEP 3: TRAINED MODEL INSPECTION")
p(f"{'=' * 80}")

model_path = REPO_PATH / "ntc_model" / "models" / "ntc_credit_model.pkl"
prep_path = REPO_PATH / "ntc_model" / "models" / "ntc_preprocessor.pkl"

p(f"\n[3.1] NTC v3 Model")
p(f"      Path: {model_path}")
p(f"      Exists: {model_path.exists()}")

model = None
model_features = []
if model_path.exists():
    model = joblib.load(model_path)
    p(f"      Type: {type(model).__name__}")
    
    if hasattr(model, 'estimators_'):
        p(f"      Wrapper: CalibratedClassifierCV (Platt scaling)")
        p(f"      Num estimators: {len(model.estimators_)}")
        base = model.estimators_[0].estimator
        p(f"      Base model type: {type(base).__name__}")
        
        if hasattr(base, 'get_booster'):
            booster = base.get_booster()
            model_features = booster.feature_names
            p(f"      Features from booster ({len(model_features)}):")
            for i, fn in enumerate(model_features, 1):
                p(f"        {i:2d}. {fn}")
        else:
            p(f"      Cannot extract features from base model")
    elif hasattr(model, 'get_booster'):
        booster = model.get_booster()
        model_features = booster.feature_names
        p(f"      Features ({len(model_features)}): {model_features[:5]}...")
    else:
        p(f"      Cannot extract feature names")

p(f"\n[3.2] Preprocessor")
p(f"      Path: {prep_path}")
p(f"      Exists: {prep_path.exists()}")

if prep_path.exists():
    prep = joblib.load(prep_path)
    p(f"      Type: {type(prep).__name__}")
    if hasattr(prep, 'n_features_in_'):
        p(f"      n_features_in_: {prep.n_features_in_}")
    if hasattr(prep, 'feature_names_in_'):
        p(f"      feature_names_in_ ({len(prep.feature_names_in_)}):")
        for i, fn in enumerate(prep.feature_names_in_, 1):
            p(f"        {i:2d}. {fn}")

# Also check production models
p(f"\n[3.3] Production Models (what scorer.py loads)")
for mname in ['pdr_ntc_model.pkl', 'pdr_msme_model.pkl']:
    mpath = REPO_PATH / mname
    p(f"\n      {mname}")
    p(f"      Path: {mpath}")
    p(f"      Exists: {mpath.exists()}")
    if mpath.exists():
        pm = joblib.load(mpath)
        p(f"      Type: {type(pm).__name__}")
        if hasattr(pm, 'get_booster'):
            pf = pm.get_booster().feature_names
            p(f"      Features: {len(pf)}")

# ============================================================================
# STEP 4: Feature Mapping — Source → Training → Model
# ============================================================================
p(f"\n{'=' * 80}")
p("STEP 4: FEATURE MAPPING (SOURCE → TRAINING → MODEL)")
p(f"{'=' * 80}")

# Define how cs-training.csv columns map to our features
FEATURE_MAP = {
    # feature_name → (source_dataset, source_column, derivation)
    'utility_payment_consistency': ('cs-training', 'NumberOfTime30-59DaysPastDueNotWorse', 'sigmoid(1 - total_DPD/max)'),
    'avg_utility_dpd': ('cs-training', 'NumberOfTime30-59DaysPastDueNotWorse + NumberOfTimes90DaysLate', 'weighted average of DPD'),
    'rent_wallet_share': ('cs-training', 'DebtRatio', 'clip(DebtRatio * 0.22, 0, 0.70)'),
    'subscription_commitment_ratio': ('cs-training', 'DebtRatio', 'clip(DebtRatio * 0.03, 0, 0.20)'),
    'emergency_buffer_months': ('cs-training', 'MonthlyIncome + DebtRatio', 'income * (1-DebtRatio) / expenses'),
    'eod_balance_volatility': ('cs-training', 'RevolvingUtilizationOfUnsecuredLines', 'clip(utilization, 0, 1)'),
    'essential_vs_lifestyle_ratio': ('cs-training', 'RevolvingUtilizationOfUnsecuredLines', '3.0 - 2.5 * utilization'),
    'cash_withdrawal_dependency': ('cs-training', 'RevolvingUtilizationOfUnsecuredLines + DPD', 'combined formula'),
    'bounced_transaction_count': ('cs-training', 'NumberOfTime30-59DaysPastDueNotWorse', 'direct map'),
    'min_balance_violation_count': ('cs-training', 'NumberOfTimes90DaysLate', 'np.clip(late90, 0, 8)'),
    'telecom_number_vintage_days': ('cs-training', 'age', 'age * 30 + noise (was demographic, now behavioral)'),
    'telecom_recharge_drop_ratio': ('cs-training', 'NumberOfTime60-89DaysPastDueNotWorse', 'sigmoid transform'),
    'gst_filing_consistency_score': ('cs-training', 'total_DPD', 'clip(10 - total_DPD, 0, 10)'),
    'gst_to_bank_variance': ('cs-training', 'DebtRatio', 'clip(abs(DebtRatio - 0.3) * 0.5, 0, 1)'),
    'p2p_circular_loop_flag': ('cs-training', 'DPD signals', 'int(total_DPD > 10 and utilization > 0.9)'),
    'turnover_inflation_spike': ('cs-training', 'DPD + DebtRatio', 'rule-based detection'),
    'identity_device_mismatch': ('cs-training', 'utilization + DPD', 'rule-based detection'),
    'income_stability_score': ('cs-training', 'MonthlyIncome + NumberOfDependents', 'income-based formula'),
    'income_seasonality_flag': ('cs-training', 'DPD signals', 'pattern detection'),
    'business_vintage_months': ('cs-training', 'NumberOfOpenCreditLinesAndLoans', 'clip(open_lines * 4, 0, 180)'),
    'revenue_seasonality_index': ('cs-training', 'NumberOfTimes90DaysLate', 'sigmoid formula'),
    'revenue_growth_trend': ('cs-training', 'NumberOfTimes90DaysLate', 'linear transform'),
    'cashflow_volatility': ('cs-training', 'RevolvingUtilizationOfUnsecuredLines', 'utilization-based'),
    'night_transaction_ratio': ('cs-training', 'DPD signals', 'UPI-calibrated baseline + DPD risk'),
    'weekend_spending_ratio': ('cs-training', 'DPD signals', 'UPI-calibrated baseline + DPD risk'),
    'payment_diversity_score': ('cs-training', 'DPD signals', 'UPI-calibrated baseline + DPD risk'),
    'device_consistency_score': ('cs-training', 'DPD signals', 'UPI-calibrated baseline + DPD risk'),
    'applicant_age_years': ('Home Credit', 'DAYS_BIRTH', '-DAYS_BIRTH / 365.25'),
    'employment_vintage_days': ('Home Credit', 'DAYS_EMPLOYED', 'abs(DAYS_EMPLOYED)'),
    'academic_background_tier': ('Home Credit', 'NAME_EDUCATION_TYPE', 'ordinal encoding'),
    'owns_property': ('Home Credit', 'FLAG_OWN_REALTY', 'binary mapping'),
    'owns_car': ('Home Credit', 'FLAG_OWN_CAR', 'binary mapping'),
    'region_risk_tier': ('Home Credit', 'REGION_RATING_CLIENT', 'direct'),
    'address_stability_years': ('Home Credit', 'DAYS_REGISTRATION', 'abs(DAYS_REGISTRATION) / 365.25'),
    'id_document_age_years': ('Home Credit', 'DAYS_ID_PUBLISH', 'abs(DAYS_ID_PUBLISH) / 365.25'),
    'family_burden_ratio': ('cs-training + Home Credit', 'NumberOfDependents + AMT_INCOME_TOTAL', 'dependents / income proxy'),
    'income_type_risk_score': ('Home Credit', 'NAME_INCOME_TYPE', 'ordinal encoding'),
    'family_status_stability_score': ('Home Credit', 'NAME_FAMILY_STATUS', 'ordinal encoding'),
    'contactability_score': ('Home Credit', 'various FLAG_ columns', 'sum of contact flags'),
    'purpose_of_loan_encoded': ('Home Credit', 'various', 'loan purpose mapping'),
    'car_age_years': ('Home Credit', 'OWN_CAR_AGE', 'direct or 99 if no car'),
    'region_city_risk_score': ('Home Credit', 'REGION_RATING_CLIENT_W_CITY', 'direct'),
    'address_work_mismatch': ('Home Credit', 'REG_CITY_NOT_WORK_CITY', 'binary'),
    'has_email_flag': ('Home Credit', 'FLAG_EMAIL', 'binary'),
    'neighbourhood_default_rate_30': ('Home Credit', 'DEF_30_CNT_SOCIAL_CIRCLE', 'normalized'),
    'neighbourhood_default_rate_60': ('Home Credit', 'DEF_60_CNT_SOCIAL_CIRCLE', 'normalized'),
    'employment_to_age_ratio': ('derived', 'DAYS_EMPLOYED / DAYS_BIRTH', 'ratio'),
    'geographic_risk_score': ('Home Credit', 'REGION_POPULATION_RELATIVE', 'population-based risk'),
}

train_cols = set(ntc_df.columns) if ntc_df is not None else set()
model_feats = set(model_features)

p(f"\n{'Feature':<45s} {'Source':<15s} {'InTraining':<12s} {'InModel':<12s} {'Status'}")
p("-" * 100)

all_ok = 0
issues = []
for feat, (source, col, deriv) in FEATURE_MAP.items():
    in_train = "YES" if feat in train_cols else "NO"
    in_model = "YES" if feat in model_feats else "NO"
    
    if feat in train_cols and feat in model_feats:
        status = "OK"
        all_ok += 1
    elif feat in train_cols and feat not in model_feats:
        status = "WARN: in training but not model"
        issues.append(f"  {feat}: in training data but NOT in model features")
    elif feat not in train_cols and feat in model_feats:
        status = "ERROR: in model but not training"
        issues.append(f"  {feat}: in model features but NOT in training data")
    else:
        status = "ERROR: missing from both"
        issues.append(f"  {feat}: MISSING from both training and model")
    
    p(f"  {feat:<43s} {source:<15s} {in_train:<12s} {in_model:<12s} {status}")

p(f"\n  Total features mapped: {len(FEATURE_MAP)}")
p(f"  OK: {all_ok}")
p(f"  Issues: {len(issues)}")
if issues:
    p(f"\n  ISSUES:")
    for iss in issues:
        p(iss)

# Check for features in model NOT in our map
unmapped = model_feats - set(FEATURE_MAP.keys())
if unmapped:
    p(f"\n  UNMAPPED features in model: {unmapped}")

# ============================================================================
# STEP 5: Feature Range Validation
# ============================================================================
p(f"\n{'=' * 80}")
p("STEP 5: FEATURE RANGE VALIDATION")
p(f"{'=' * 80}")

expected_ranges = {
    'utility_payment_consistency': (0.0, 1.0),
    'avg_utility_dpd': (0.0, 120.0),
    'rent_wallet_share': (0.0, 1.0),
    'subscription_commitment_ratio': (0.0, 0.30),
    'emergency_buffer_months': (0.0, 50.0),
    'eod_balance_volatility': (0.0, 1.0),
    'essential_vs_lifestyle_ratio': (0.0, 5.0),
    'cash_withdrawal_dependency': (0.0, 1.0),
    'bounced_transaction_count': (0.0, 20.0),
    'min_balance_violation_count': (0.0, 8.0),
    'telecom_number_vintage_days': (30.0, 7000.0),
    'telecom_recharge_drop_ratio': (0.0, 1.5),
    'gst_filing_consistency_score': (0.0, 10.0),
    'gst_to_bank_variance': (0.0, 1.0),
    'p2p_circular_loop_flag': (0.0, 1.0),
    'turnover_inflation_spike': (0.0, 1.0),
    'identity_device_mismatch': (0.0, 1.0),
    'income_stability_score': (0.0, 1.0),
    'income_seasonality_flag': (0.0, 1.0),
    'business_vintage_months': (0.0, 200.0),
    'revenue_seasonality_index': (0.0, 1.0),
    'applicant_age_years': (20.0, 75.0),
    'employment_vintage_days': (0.0, 20000.0),
    'owns_property': (0.0, 1.0),
    'owns_car': (0.0, 1.0),
    'family_burden_ratio': (0.0, 1.0),
}

if ntc_df is not None:
    p(f"\n{'Feature':<43s} {'Expected':>16s} {'Actual':>20s} {'Mean':>10s} {'Status'}")
    p("-" * 105)
    
    range_ok = 0
    range_warn = 0
    for feat, (exp_min, exp_max) in expected_ranges.items():
        if feat in ntc_df.columns:
            act_min = ntc_df[feat].min()
            act_max = ntc_df[feat].max()
            act_mean = ntc_df[feat].mean()
            
            ok = act_min >= exp_min - 0.01 and act_max <= exp_max + 0.01
            status = "OK" if ok else "OUT OF RANGE"
            if ok:
                range_ok += 1
            else:
                range_warn += 1
            
            p(f"  {feat:<41s} [{exp_min:6.1f},{exp_max:6.1f}] [{act_min:8.4f},{act_max:8.4f}] {act_mean:9.4f}  {status}")
        else:
            p(f"  {feat:<41s} {'MISSING':>16s}")
            range_warn += 1
    
    p(f"\n  Range checks passed: {range_ok}/{range_ok + range_warn}")

# ============================================================================
# STEP 6: Build Script Verification
# ============================================================================
p(f"\n{'=' * 80}")
p("STEP 6: BUILD SCRIPT VERIFICATION")
p(f"{'=' * 80}")

build_path = REPO_PATH / "ntc_model" / "build_ntc_training_v3.py"
p(f"\n[6.1] build_ntc_training_v3.py")
p(f"      Exists: {build_path.exists()}")

if build_path.exists():
    with open(build_path, 'r', encoding='utf-8') as bf:
        build_src = bf.read()
    
    checks = {
        'Loads cs-training.csv': 'cs-training' in build_src or 'cs_training' in build_src,
        'Loads application_train.csv': 'application_train' in build_src,
        'Uses SeriousDlqin2yrs as TARGET': 'SeriousDlqin2yrs' in build_src,
        'Random pairing (independence)': 'shuffle' in build_src or 'sample' in build_src or 'permutation' in build_src,
        'Saves output CSV': '.to_csv' in build_src,
        'Uses sigmoid/clip transforms': 'sigmoid' in build_src or 'np.clip' in build_src,
        'Handles nulls': 'fillna' in build_src or 'dropna' in build_src,
        'Feature count ~49': str(len(model_features)) in build_src or '49' in build_src or '50' in build_src,
    }
    
    p(f"\n      Build script checks:")
    for check_name, passed in checks.items():
        status = "PASS" if passed else "FAIL"
        p(f"        {check_name:<45s} {status}")
    
    # Count feature assignments
    feature_assignments = build_src.count("row['")
    p(f"\n      Feature assignments in build script: {feature_assignments}")

# ============================================================================
# STEP 7: Cross-System Feature Alignment
# ============================================================================
p(f"\n{'=' * 80}")
p("STEP 7: CROSS-SYSTEM FEATURE ALIGNMENT")
p(f"{'=' * 80}")

# Root feature_engine.py
import sys
sys.path.insert(0, str(REPO_PATH))
from feature_engine import compute_features
fe_features = list(compute_features([], {}, {}).keys())

p(f"\n[7.1] Feature counts across systems:")
p(f"      Root feature_engine.py:     {len(fe_features)} features")
p(f"      Training data (v2.csv):     {len(ntc_df.columns) - 1 if ntc_df is not None else '?'} features (excl TARGET)")
p(f"      v3 Model (booster):         {len(model_features)} features")

# Production model features
prod_feats = []
prod_path = REPO_PATH / "pdr_ntc_model.pkl"
if prod_path.exists():
    pm = joblib.load(prod_path)
    if hasattr(pm, 'get_booster'):
        prod_feats = pm.get_booster().feature_names
p(f"      Prod model (pdr_ntc):       {len(prod_feats)} features")

train_feats = set(ntc_df.columns) - {'TARGET'} if ntc_df is not None else set()
fe_set = set(fe_features)
model_set = set(model_features)
prod_set = set(prod_feats)

p(f"\n[7.2] Feature alignment matrix:")
p(f"      In ALL 4 systems:           {len(fe_set & train_feats & model_set & prod_set)}")
p(f"      In v3 model but NOT feature_engine: {len(model_set - fe_set)}")
p(f"      In feature_engine but NOT v3 model: {len(fe_set - model_set)}")
p(f"      In v3 model but NOT prod model:     {len(model_set - prod_set)}")
p(f"      In prod model but NOT v3 model:     {len(prod_set - model_set)}")

p(f"\n[7.3] Features MISSING from feature_engine (needed by v3 model):")
missing = sorted(model_set - fe_set)
for m in missing:
    source = FEATURE_MAP.get(m, ('?', '?', '?'))
    p(f"      {m:<45s} source: {source[0]}")

p(f"\n[7.4] Features EXTRA in feature_engine (NOT used by v3 model):")
extra = sorted(fe_set - model_set)
for e in extra:
    p(f"      {e}")

# ============================================================================
# SUMMARY
# ============================================================================
p(f"\n{'=' * 80}")
p("FINAL SUMMARY")
p(f"{'=' * 80}")
p()

checks_summary = [
    ("cs-training.csv loaded", cs_df is not None, f"{cs_df.shape}" if cs_df is not None else "NOT FOUND"),
    ("application_train.csv loaded", app_df is not None, f"cols={len(app_df.columns)}" if app_df is not None else "NOT FOUND"),
    ("Training data generated", ntc_df is not None, f"{ntc_df.shape}" if ntc_df is not None else "NOT FOUND"),
    ("v3 model loaded", model is not None, type(model).__name__ if model else "NOT FOUND"),
    ("Model has 49 features", len(model_features) == 49, f"actual={len(model_features)}"),
    ("Training data has 49+1 cols", ntc_df.shape[1] == 50 if ntc_df is not None else False, f"actual={ntc_df.shape[1]}" if ntc_df is not None else "?"),
    ("Feature engine aligned with model", len(model_set - fe_set) == 0, f"{len(model_set - fe_set)} missing"),
    ("v3 model deployed to API", False, "scorer.py loads pdr_ntc_model.pkl (OLD)"),
]

for name, passed, detail in checks_summary:
    status = "PASS" if passed else "FAIL"
    p(f"  [{status:4s}] {name:<45s} | {detail}")

p(f"\n  CRITICAL ACTION ITEMS:")
p(f"  1. Wire ntc_credit_model.pkl + ntc_preprocessor.pkl into scorer.py")
p(f"  2. Update feature_engine.py to output all {len(model_features)} features")
p(f"  3. Handle CalibratedClassifierCV wrapper for SHAP")
p(f"  4. Delete pdr_ntc_model.pkl (old circular model)")
p()

f.close()
print(f"\nAudit complete. Report saved to: {REPO_PATH / 'audit_report.txt'}")
