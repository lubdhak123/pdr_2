"""Main scoring orchestrator for PDR.
Loads XGBoost model once at module level.
Pipeline: feature engine -> pre-layer -> model -> SHAP -> output.
"""
import pathlib
import numpy as np
try:
    import shap
except ImportError:
    import os
    os.system('pip install shap')
    import shap
import joblib
from feature_engine import compute_features
from pre_layer import apply_pre_layer

FEATURE_COLS = [
    'utility_payment_consistency', 'avg_utility_dpd', 'rent_wallet_share',
    'subscription_commitment_ratio', 'emergency_buffer_months',
    'min_balance_violation_count', 'eod_balance_volatility',
    'essential_vs_lifestyle_ratio', 'cash_withdrawal_dependency',
    'bounced_transaction_count', 'telecom_number_vintage_days',
    'telecom_recharge_drop_ratio', 'academic_background_tier',
    'purpose_of_loan_encoded', 'business_vintage_months',
    'revenue_growth_trend', 'revenue_seasonality_index',
    'operating_cashflow_ratio', 'cashflow_volatility',
    'avg_invoice_payment_delay', 'customer_concentration_ratio',
    'repeat_customer_revenue_pct', 'vendor_payment_discipline',
    'gst_filing_consistency_score', 'gst_to_bank_variance',
    'p2p_circular_loop_flag', 'benford_anomaly_score',
    'round_number_spike_ratio', 'turnover_inflation_spike',
    'identity_device_mismatch'
]

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
    'business_vintage_months':       'Business operating history',
    'revenue_growth_trend':          'Revenue growth trajectory',
    'revenue_seasonality_index':     'Revenue seasonality pattern',
    'operating_cashflow_ratio':      'Operating cashflow health',
    'cashflow_volatility':           'Monthly cashflow volatility',
    'avg_invoice_payment_delay':     'Invoice payment delay',
    'customer_concentration_ratio':  'Customer concentration risk',
    'repeat_customer_revenue_pct':   'Repeat customer revenue share',
    'vendor_payment_discipline':     'Vendor payment reliability',
    'gst_filing_consistency_score':  'GST filing regularity',
    'gst_to_bank_variance':          'GST declared vs actual turnover',
    'p2p_circular_loop_flag':        'Circular fund flow detected',
    'benford_anomaly_score':         'Transaction amount anomaly',
    'round_number_spike_ratio':      'Round number transaction spike',
    'turnover_inflation_spike':      'Turnover inflation indicator',
    'identity_device_mismatch':      'Identity verification signal'
}

GRADE_THRESHOLDS = [
    (0.20, 'A', 'APPROVED'),
    (0.40, 'B', 'APPROVED WITH CONDITIONS'),
    (0.60, 'C', 'MANUAL REVIEW'),
    (0.80, 'D', 'REJECTED'),
    (1.01, 'E', 'REJECTED'),
]

path = pathlib.Path(__file__).parent / 'pdr_model_realistic.pkl'
try:
    model = joblib.load(path)
    print(f"[OK] Model loaded from {path}")
except Exception as e:
    print(f"[ERROR] Model load failed: {e}")
    model = None

def score_user(
    transactions: list[dict],
    profile: dict,
    gst_data: dict
) -> dict:
    """Score a user through the PDR pipeline."""
    features = compute_features(transactions, profile, gst_data)
    pre_result = apply_pre_layer(features)

    if pre_result is not None:
        grade, outcome, reason = pre_result
        model_score = None
        decision_source = 'pre_layer'
        shap_reasons = []
        primary_reason = reason
    else:
        if model is None:
            raise RuntimeError('Model not loaded')
        X = np.array([[features[col] for col in FEATURE_COLS]])
        model_score = float(model.predict_proba(X)[0][1])
        
        grade, outcome = 'E', 'REJECTED'
        for threshold, g, o in GRADE_THRESHOLDS:
            if model_score < threshold:
                grade, outcome = g, o
                break
        
        decision_source = 'model'
        explainer = shap.TreeExplainer(model)
        shap_vals = explainer.shap_values(X)[0]
        top5 = np.argsort(np.abs(shap_vals))[::-1][:5]
        
        shap_reasons = []
        for idx in top5:
            val = float(shap_vals[idx])
            abs_val = abs(val)
            shap_reasons.append({
                'feature': FEATURE_COLS[idx],
                'reason': SHAP_REASON_MAP[FEATURE_COLS[idx]],
                'shap_value': round(val, 4),
                'direction': 'risk' if val > 0 else 'strength',
                'impact': 'Very High' if abs_val > 0.3 else 'High' if abs_val > 0.15 else 'Medium'
            })
            
        primary_reason = shap_reasons[0]['reason'] if shap_reasons else 'Model assessed profile'

    return {
        'grade': grade,
        'outcome': outcome,
        'default_probability': round(model_score, 4) if model_score is not None else None,
        'decision_source': decision_source,
        'primary_reason': primary_reason,
        'shap_reasons': shap_reasons,
        'features': features
    }
