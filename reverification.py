import joblib, pandas as pd, numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report

df = pd.read_csv('pdr_training_data_realistic.csv')

NTC_ARCHETYPES = {
    'it_professional', 'retired_pension', 'nri_remittance',
    'seasonal_farmer', 'gig_stress', 'salary_inflator',
    'cash_hoarder', 'influencer', 'real_estate_agent', 'housewife_business'
}

ntc_df  = df[df['archetype'].isin(NTC_ARCHETYPES)].copy()
msme_df = df[~df['archetype'].isin(NTC_ARCHETYPES)].copy()

ntc_model  = joblib.load('pdr_ntc_model.pkl')
msme_model = joblib.load('pdr_msme_model.pkl')

DROP_COLS = ['default_label', 'archetype']

print("=" * 55)
print("DISTRIBUTION CHECK (should NOT be 0.000 vs 2.000)")
print("=" * 55)
print(df.groupby('default_label')[
    ['bounced_transaction_count', 'telecom_number_vintage_days',
     'p2p_circular_loop_flag', 'gst_filing_consistency_score',
     'cash_withdrawal_dependency', 'identity_device_mismatch']
].mean().round(3).T.to_string())

print("\n" + "=" * 55)
print("MODEL PERFORMANCE (evaluated on held-out val split)")
print("=" * 55)

for name, subset, model in [('NTC', ntc_df, ntc_model), ('MSME', msme_df, msme_model)]:
    feats = model.get_booster().feature_names
    y = subset['default_label']
    X = subset[feats].fillna(0)
    
    _, X_val, _, y_val = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    
    probs = model.predict_proba(X_val)[:, 1]
    
    if y_val.nunique() < 2:
        print(f"\n{name}: FAIL — only one class in val split ({len(X_val)} rows, "
              f"{y_val.sum()} bad). Split is broken.")
        continue
    
    auc = roc_auc_score(y_val, probs)
    print(f"\n{name} — val rows: {len(X_val)}, bad: {y_val.sum()}, AUC: {auc:.4f}")
    
    if auc > 0.97:
        print("  STATUS: MEMORISED — distributions still too clean")
    elif auc > 0.75:
        print("  STATUS: GOOD — model has real generalisation")
    elif auc > 0.60:
        print("  STATUS: WEAK — acceptable for hackathon, needs work")
    else:
        print("  STATUS: BROKEN — no better than random")
    
    print(classification_report(y_val, (probs > 0.5).astype(int), digits=3))

print("=" * 55)
print("Running verify.py...")
import subprocess
result = subprocess.run(['python', 'verify.py'], capture_output=True, text=True)
print(result.stdout)
if result.returncode != 0:
    print("FAIL:", result.stderr)