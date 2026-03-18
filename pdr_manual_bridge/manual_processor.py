import pandas as pd
import numpy as np
import joblib
import json
import shap

# 1. Load your trained model [cite: 301, 463]
model = joblib.load('../pdr_model_clean.pkl')
explainer = shap.TreeExplainer(model)

# The exact 30 features your model expects [cite: 462]
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

def engineer_features(raw_data):
    """Parses raw transactions into the 30 ML features [cite: 284, 286]"""
    txns = raw_data['transactions']
    balances = [t['balance'] for t in txns]
    narrations = " ".join([t['narration'].upper() for t in txns])
    
    # Example Feature Calculations [cite: 258, 284]
    features = {f: 0.1 for f in FEATURE_COLS} # Start with defaults
    
    # I. Liquidity & Stress [cite: 73]
    features['eod_balance_volatility'] = np.std(balances) / np.mean(balances) if balances else 0.5
    features['bounced_transaction_count'] = narrations.count("BOUNCE") + narrations.count("RTN")
    features['min_balance_violation_count'] = sum(1 for b in balances if b < 500)
    
    # II. Profile Data [cite: 74, 168]
    features['business_vintage_months'] = raw_data['user_profile']['business_vintage_months']
    features['academic_background_tier'] = raw_data['user_profile']['academic_background_tier']
    
    return features

# --- RUN THE BRIDGE ---
with open('raw_setu_sample.json', 'r') as f:
    raw_input = json.load(f)

# Step 1: Feature Engineering [cite: 282, 284]
processed_features = engineer_features(raw_input)
input_df = pd.DataFrame([processed_features])[FEATURE_COLS]

# Step 2: Prediction (Inference) [cite: 307, 313]
pd_score = model.predict_proba(input_df)[0][1]
grade = "A" if pd_score < 0.05 else "B" if pd_score < 0.12 else \
        "C" if pd_score < 0.20 else "D" if pd_score < 0.40 else "E"

# Step 3: SHAP Explanations (Layer 4) [cite: 41, 315]
shap_values = explainer.shap_values(input_df)
top_idx = np.argsort(abs(shap_values[0]))[::-1][:3]

print(f"--- PDR MANUAL SCORE ---")
print(f"Probability of Default: {pd_score*100:.2f}%")
print(f"Risk Grade: {grade}")
print(f"Primary Risk Drivers: {[FEATURE_COLS[i] for i in top_idx]}")