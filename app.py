from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
import numpy as np
import shap
import requests # Needed for Setu API calls [cite: 338]

app = Flask(__name__)
CORS(app) 

# --- CONFIGURATION ---
SETU_CLIENT_ID = "d84dc7af-a453-4e47-9720-965efd4b1b60"
SETU_CLIENT_SECRET = "XEEhMfzWa3F5TTP1K8ZgX0HXDyI3R6ug"
SETU_PRODUCT_ID = "95366be4-65b9-4e52-a4df-a9f2fd2a66c4"
SETU_BASE_URL = "https://fiu-sandbox.setu.co" # Sandbox environment [cite: 335]

# --- LOAD ML MODEL ---
# Loading your clean model and SHAP explainer [cite: 301, 463]
model = joblib.load('pdr_model.pkl')
explainer = shap.TreeExplainer(model)

# The exact 30 features from your finalized schema [cite: 415, 462]
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

# --- SETU HELPERS ---
def get_setu_headers():
    return {
        "x-client-id": SETU_CLIENT_ID,
        "x-client-secret": SETU_CLIENT_SECRET,
        "x-product-instance-id": SETU_PRODUCT_ID,
        "Content-Type": "application/json"
    }

# --- ENDPOINTS ---

@app.route('/initiate-consent', methods=['POST'])
def initiate_consent():
    """Step 1: Request user consent via Setu [cite: 336, 338]"""
    phone = request.json.get('phone')
    url = f"{SETU_BASE_URL}/consents"
    
    # Payload follows standard Setu AA sandbox requirements 
    payload = {
        "Detail": {
            "consentStart": "2023-01-01T00:00:00Z",
            "consentExpiry": "2026-12-31T00:00:00Z",
            "Customer": {"id": f"{phone}@onemoney"}, # Sandbox VPA 
            "FIDataRange": {"from": "2023-01-01T00:00:00Z", "to": "2024-01-01T00:00:00Z"},
            "consentMode": "STORE",
            "consentTypes": ["TRANSACTIONS", "PROFILE", "SUMMARY"],
            "fiTypes": ["DEPOSIT"]
        },
        "redirectUrl": "http://localhost:3000/callback" # Update with your ngrok URL if needed [cite: 343, 344]
    }
    
    response = requests.post(url, json=payload, headers=get_setu_headers())
    return jsonify(response.json())

@app.route('/fetch-and-score/<consent_id>', methods=['GET'])
def fetch_and_score(consent_id):
    """Step 2: Fetch raw FI data, engineer features, and score user [cite: 13, 338]"""
    # 1. Fetch raw data from Setu 
    fi_url = f"{SETU_BASE_URL}/fi/fetch/{consent_id}"
    fi_response = requests.get(fi_url, headers=get_setu_headers())
    raw_data = fi_response.json()
    
    # 2. Transform raw Setu JSON into the 30-feature vector [cite: 284, 286]
    # In a hackathon demo, you often map the presence of patterns to feature values
    processed_features = transform_data_to_features(raw_data)
    
    # 3. Predict Score [cite: 37, 313]
    input_df = pd.DataFrame([processed_features])[FEATURE_COLS]
    pd_score = model.predict_proba(input_df)[0][1]
    
    # 4. Determine Grade [cite: 40, 313]
    grade = "A" if pd_score < 0.05 else "B" if pd_score < 0.12 else \
            "C" if pd_score < 0.20 else "D" if pd_score < 0.40 else "E"
    
    # 5. SHAP Reason Codes [cite: 41, 315]
    shap_values = explainer.shap_values(input_df)
    top_indices = np.argsort(abs(shap_values[0]))[::-1][:5]
    reasons = [{"feature": FEATURE_COLS[i], "impact": float(shap_values[0][i])} for i in top_indices]

    return jsonify({
        "pd": round(pd_score * 100, 2),
        "grade": grade,
        "reasons": reasons,
        "raw_data_summary": "Successfully fetched from Setu AA"
    })

def transform_data_to_features(raw_json):
    """
    Placeholder: Maps raw Setu JSON transactions to your 30 ML features. [cite: 284]
    In reality, you'd calculate things like 'eod_balance_volatility' here. [cite: 220, 229]
    """
    # For simulation, returning a sample row from your training schema
    return {f: 0.1 for f in FEATURE_COLS} 

if __name__ == '__main__':
    app.run(port=5000, debug=True)