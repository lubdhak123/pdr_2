import pandas as pd
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE
import shap
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
import joblib
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# === LOAD THE REALISTIC CSV (this is the only one we use now) ===
df = pd.read_csv('pdr_training_data_realistic.csv')

feature_cols = [
    'utility_payment_consistency', 'avg_utility_dpd', 'rent_wallet_share', 'subscription_commitment_ratio',
    'emergency_buffer_months', 'min_balance_violation_count', 'eod_balance_volatility',
    'essential_vs_lifestyle_ratio', 'cash_withdrawal_dependency', 'bounced_transaction_count',
    'telecom_number_vintage_days', 'telecom_recharge_drop_ratio', 'academic_background_tier',
    'purpose_of_loan_encoded', 'business_vintage_months', 'revenue_growth_trend',
    'revenue_seasonality_index', 'operating_cashflow_ratio', 'cashflow_volatility',
    'avg_invoice_payment_delay', 'customer_concentration_ratio', 'repeat_customer_revenue_pct',
    'vendor_payment_discipline', 'gst_filing_consistency_score', 'gst_to_bank_variance',
    'p2p_circular_loop_flag', 'benford_anomaly_score', 'round_number_spike_ratio',
    'turnover_inflation_spike', 'identity_device_mismatch'
]

X = df[feature_cols]
y = df['default_label']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Apply SMOTE only on training data
sm = SMOTE(random_state=42)
X_train_res, y_train_res = sm.fit_resample(X_train, y_train)
print(f"After SMOTE — train size: {len(X_train_res)}, class balance: {y_train_res.value_counts().to_dict()}")

# Tell XGBoost about the imbalance as a backup
scale = (y_train == 0).sum() / (y_train == 1).sum()

model = XGBClassifier(
    n_estimators=400,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.85,
    colsample_bytree=0.85,
    scale_pos_weight=scale,
    random_state=42,
    eval_metric='auc'
)
model.fit(
    X_train_res, y_train_res,
    eval_set=[(X_test, y_test)],
    verbose=50
)

joblib.dump(model, 'pdr_model_realistic.pkl')
print("\n[OK] Model saved as pdr_model_realistic.pkl")

# === EVALUATION ===
y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]

print(f"\nROC-AUC:  {roc_auc_score(y_test, y_prob):.4f}")
print(f"Accuracy: {model.score(X_test, y_test):.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=['Good (0)', 'Default (1)']))

# === SHAP demo (Layer 4 - exactly what judges want) ===
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test.iloc[:3])
print("\n📊 Top 5 SHAP reasons for first 3 test users:")
for i in range(3):
    print(f"\nUser {i+1}:")
    top_idx = np.argsort(abs(shap_values[i]))[::-1][:5]
    for idx in top_idx:
        print(f"   {feature_cols[idx]:<35} → {shap_values[i][idx]:+.4f}")