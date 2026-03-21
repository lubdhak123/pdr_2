"""Main scoring orchestrator for PDR.
Loads NTC (XGBoost) and MSME (CatBoost) models at module level.
Pipeline: feature_engine -> pre_layer -> model (routed on is_msme) -> SHAP -> output.
"""
import pathlib
import numpy as np
import pandas as pd
try:
    import shap
except ImportError:
    import os
    os.system('pip install shap')
    import shap
import joblib
from feature_engine import compute_features
from pre_layer import apply_pre_layer

# ─────────────────────────────────────────────
# FEATURE SETS — must match train.py exactly
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
# HUMAN-READABLE REASON MAP
# ─────────────────────────────────────────────

SHAP_REASON_MAP = {
    'utility_payment_consistency':   'Utility bill payment discipline',
    'avg_utility_dpd':               'Utility payment timeliness',
    'rent_wallet_share':             'Rent as share of income',
    'subscription_commitment_ratio': 'Subscription payment commitment',
    'emergency_buffer_months':       'Emergency savings buffer',
    'min_balance_violation_count':   'Minimum balance violations',
    'eod_balance_volatility':        'Account balance stability',
    'essential_vs_lifestyle_ratio':  'Essential vs lifestyle spending',
    'cash_withdrawal_dependency':    'Cash withdrawal dependency',
    'bounced_transaction_count':     'Bounce charges on account',
    'telecom_number_vintage_days':   'SIM card age - identity stability',
    'telecom_recharge_drop_ratio':   'Telecom recharge consistency',
    'academic_background_tier':      'Educational background tier',
    'purpose_of_loan_encoded':       'Stated loan purpose',
    'employment_vintage_days':       'Employment tenure',
    'business_vintage_months':       'Business operating history',
    'revenue_growth_trend':          'Revenue growth trajectory',
    'operating_cashflow_ratio':      'Operating cashflow health',
    'cashflow_volatility':           'Monthly cashflow volatility',
    'customer_concentration_ratio':  'Customer concentration risk',
    'gst_filing_consistency_score':  'GST filing regularity',
    'monthly_income':                'Monthly income level',
    'avg_invoice_payment_delay':     'Invoice payment delay',
    'repeat_customer_revenue_pct':   'Repeat customer revenue share',
    'vendor_payment_discipline':     'Vendor payment reliability',
    'gst_to_bank_variance':          'GST declared vs actual turnover',
    'p2p_circular_loop_flag':        'Circular fund flow detected',
    'benford_anomaly_score':         'Transaction amount anomaly',
    'round_number_spike_ratio':      'Round number transaction spike',
    'turnover_inflation_spike':      'Turnover inflation indicator',
    'identity_device_mismatch':      'Identity verification signal',
    'is_msme':                       'Applicant segment (MSME/NTC)',
}

GRADE_THRESHOLDS = [
    (0.05, 'A', 'APPROVED'),
    (0.15, 'B', 'APPROVED WITH CONDITIONS'),
    (0.30, 'C', 'MANUAL REVIEW'),
    (0.50, 'D', 'REJECTED'),
    (1.01, 'E', 'REJECTED'),
]

# ─────────────────────────────────────────────
# MODEL LOADING
# ─────────────────────────────────────────────

_base = pathlib.Path(__file__).parent

def _load(filename):
    p = _base / filename
    try:
        obj = joblib.load(p)
        print(f"[OK] Loaded {filename}")
        return obj
    except Exception as e:
        print(f"[ERROR] Failed to load {filename}: {e}")
        return None

ntc_model  = _load('pdr_ntc_model.pkl')
msme_model = _load('pdr_msme_model.pkl')

# Build SHAP explainers once at load time — expensive, don't rebuild per request
ntc_explainer  = shap.TreeExplainer(ntc_model)  if ntc_model  else None
msme_explainer = shap.TreeExplainer(msme_model) if msme_model else None

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _to_row(features: dict, feature_list: list) -> pd.DataFrame:
    """Single-row DataFrame for model input, NaN-filling missing cols."""
    return pd.DataFrame([{f: features.get(f, np.nan) for f in feature_list}])


def _grade(pd_score: float):
    for threshold, g, o in GRADE_THRESHOLDS:
        if pd_score < threshold:
            return g, o
    return 'E', 'REJECTED'


def _shap_reasons(shap_vals, feature_list: list, top_n: int = 5) -> list[dict]:
    pairs = sorted(zip(shap_vals, feature_list), key=lambda x: abs(x[0]), reverse=True)
    reasons = []
    for val, feat in pairs[:top_n]:
        abs_val = abs(val)
        reasons.append({
            'feature': feat,
            'reason': SHAP_REASON_MAP.get(feat, feat),
            'shap_value': round(float(val), 4),
            'direction': 'risk' if val > 0 else 'strength',
            'impact': (
                'Very High' if abs_val > 0.3 else
                'High'      if abs_val > 0.15 else
                'Medium'
            ),
        })
    return reasons


# ─────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────

def score_user(
    transactions: list[dict],
    profile: dict,
    gst_data: dict
) -> dict:
    """Score a user through the PDR pipeline.

    Routes on profile['is_msme']:
      - NTC  (is_msme=0): 100% XGBoost NTC model
      - MSME (is_msme=1): 60% CatBoost MSME + 40% XGBoost NTC ensemble
    """
    # ── 1. Feature computation ────────────────────────────────────────────
    features = compute_features(transactions, profile, gst_data)

    # Inject is_msme from profile so models see it as a feature
    is_msme = int(profile.get('is_msme', 0))
    features['is_msme'] = is_msme

    # ── 2. Pre-layer (hard rules) ─────────────────────────────────────────
    pre_result = apply_pre_layer(features)

    if pre_result is not None:
        grade, outcome, reason = pre_result
        return {
            'grade': grade,
            'outcome': outcome,
            'default_probability': None,
            'decision_source': 'pre_layer',
            'primary_reason': reason,
            'shap_reasons': [],
            'features': features,
        }

    # ── 3. Model scoring ──────────────────────────────────────────────────
    if ntc_model is None:
        raise RuntimeError('NTC model not loaded — run train.py first')

    row_ntc = _to_row(features, NTC_FEATURES)
    pd_ntc  = float(ntc_model.predict_proba(row_ntc)[0][1])

    if is_msme:
        if msme_model is None:
            raise RuntimeError('MSME model not loaded — run train.py first')
        row_msme = _to_row(features, MSME_FEATURES)
        pd_msme  = float(msme_model.predict_proba(row_msme)[0][1])
        pd_score = 0.6 * pd_msme + 0.4 * pd_ntc

        # SHAP from MSME model (primary driver for MSME applicants)
        shap_vals  = msme_explainer.shap_values(row_msme)[0]
        shap_feats = MSME_FEATURES
    else:
        pd_score   = pd_ntc
        shap_vals  = ntc_explainer.shap_values(row_ntc)[0]
        shap_feats = NTC_FEATURES

    # ── 4. Fraud hard-override ────────────────────────────────────────────
    fraud_flags = ['p2p_circular_loop_flag', 'identity_device_mismatch']
    if any(features.get(f, 0) == 1 for f in fraud_flags):
        pd_score = max(pd_score, 0.85)

    # ── 5. Grade + reason codes ───────────────────────────────────────────
    grade, outcome    = _grade(pd_score)
    shap_reasons      = _shap_reasons(shap_vals, shap_feats)
    primary_reason    = shap_reasons[0]['reason'] if shap_reasons else 'Model assessed profile'

    return {
        'grade': grade,
        'outcome': outcome,
        'default_probability': round(pd_score, 4),
        'decision_source': 'model',
        'primary_reason': primary_reason,
        'shap_reasons': shap_reasons,
        'features': features,
        # Extra debug info — strip before prod if needed
        'pd_ntc':  round(pd_ntc, 4),
        'pd_msme': round(pd_msme, 4) if is_msme else None,
    }