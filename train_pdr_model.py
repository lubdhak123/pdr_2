import pandas as pd
import numpy as np
from xgboost import XGBClassifier
import shap
from sklearn.model_selection import train_test_split
import joblib
import warnings
warnings.filterwarnings('ignore')

# === CHANGE TO YOUR NEW FILE ===
df = pd.read_csv('pdr_training_data_v2_clean.csv')

feature_cols = [col for col in df.columns if col != 'default_label']
X = df[feature_cols]
y = df['default_label']

print(f"Training on {len(df):,} users with {len(feature_cols)} features")

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

model = XGBClassifier(
    n_estimators=400,
    max_depth=7,
    learning_rate=0.05,
    subsample=0.85,
    colsample_bytree=0.85,
    random_state=42,
    eval_metric='auc'
)

model.fit(X_train, y_train)

joblib.dump(model, 'pdr_model.pkl')
print("✅ Model saved as pdr_model.pkl")

print(f"\nTraining AUC: {model.score(X_train, y_train):.4f}")
print(f"Test AUC:      {model.score(X_test, y_test):.4f}")

# Quick SHAP demo (Layer 4)
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test.iloc[:3])

print("\n📊 Top 5 SHAP reasons for first 3 test users:")
for i in range(3):
    print(f"\nUser {i+1}:")
    top_idx = np.argsort(abs(shap_values[i]))[::-1][:5]
    for idx in top_idx:
        print(f"   {feature_cols[idx]:<30} → {shap_values[i][idx]:+.4f}")