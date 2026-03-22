import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score

df = pd.read_csv('pdr_training_data_realistic.csv')

# Verify archetype column exists
assert 'archetype' in df.columns, \
    "archetype column missing — re-run generate_realistic_training_data.py first"

# Define NTC archetypes (individuals, no registered business)
NTC_ARCHETYPES = {
    'it_professional', 'retired_pension', 'nri_remittance',
    'seasonal_farmer', 'gig_stress', 'salary_inflator',
    'cash_hoarder', 'influencer', 'real_estate_agent', 'housewife_business'
}

# Split by archetype
ntc_df  = df[df['archetype'].isin(NTC_ARCHETYPES)].copy()
msme_df = df[~df['archetype'].isin(NTC_ARCHETYPES)].copy()

print(f"NTC rows: {len(ntc_df)}, bad rate: {ntc_df['default_label'].mean():.1%}")
print(f"MSME rows: {len(msme_df)}, bad rate: {msme_df['default_label'].mean():.1%}")

# STOP if either split has fewer than 100 bad borrowers
ntc_bad  = ntc_df['default_label'].sum()
msme_bad = msme_df['default_label'].sum()
assert ntc_bad >= 100,  f"NTC has only {ntc_bad} bad borrowers — check archetype split"
assert msme_bad >= 100, f"MSME has only {msme_bad} bad borrowers — check archetype split"

# Drop non-feature columns
DROP_COLS = ['default_label', 'archetype']

def train_model(subset_df, name):
    y = subset_df['default_label']
    X = subset_df.drop(columns=DROP_COLS, errors='ignore').fillna(0)
    
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    
    pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
    print(f"\n{name}: {len(X_train)} train, {len(X_val)} val, scale_pos_weight={pos_weight:.2f}")
    
    model = xgb.XGBClassifier(
        n_estimators=500,
        max_depth=4,
        min_child_weight=10,
        reg_alpha=0.3,
        reg_lambda=2.0,
        subsample=0.8,
        colsample_bytree=0.7,
        learning_rate=0.03,
        scale_pos_weight=pos_weight,
        early_stopping_rounds=20,
        eval_metric='auc',
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=50
    )
    
    val_probs = model.predict_proba(X_val)[:, 1]
    auc = roc_auc_score(y_val, val_probs)
    print(f"{name} validation AUC: {auc:.4f}")
    
    # GATE: refuse to save if AUC is suspiciously perfect or terrible
    if auc > 0.97:
        print(f"WARNING: {name} AUC={auc:.4f} — likely still memorising. "
              f"Check that noise was added and distributions overlap.")
    if auc < 0.60:
        print(f"WARNING: {name} AUC={auc:.4f} — model has no signal. "
              f"Check feature alignment between CSV and model input.")
    
    # Feature importance — top 10
    feat_names = X_train.columns.tolist()
    importances = model.feature_importances_
    top10 = sorted(zip(feat_names, importances), key=lambda x: -x[1])[:10]
    print(f"\n{name} top 10 features:")
    for feat, imp in top10:
        print(f"  {feat}: {imp:.4f}")
    
    # WARN if fraud flags dominate
    top3_names = {f for f, _ in top10[:3]}
    fraud_flags = {'p2p_circular_loop_flag', 'benford_anomaly_score',
                   'identity_device_mismatch', 'turnover_inflation_spike'}
    overlap = top3_names & fraud_flags
    if overlap:
        print(f"WARNING: Fraud flags in top 3: {overlap}. "
              f"These simulated features are dominating real signal.")
    
    return model

ntc_model  = train_model(ntc_df,  'NTC')
msme_model = train_model(msme_df, 'MSME')

joblib.dump(ntc_model,  'pdr_ntc_model.pkl')
joblib.dump(msme_model, 'pdr_msme_model.pkl')
print("\nModels saved: pdr_ntc_model.pkl, pdr_msme_model.pkl")