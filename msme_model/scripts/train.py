"""
MSME Model — XGBoost Training (KS-optimized)
Run: python scripts/train.py
"""
import os, pickle, warnings
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import roc_auc_score, roc_curve, classification_report, confusion_matrix, make_scorer
warnings.filterwarnings("ignore")

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR  = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

X_train = pd.read_csv(os.path.join(DATA_DIR, "X_train.csv"))
X_val   = pd.read_csv(os.path.join(DATA_DIR, "X_val.csv"))
y_train = pd.read_csv(os.path.join(DATA_DIR, "y_train.csv")).squeeze()
y_val   = pd.read_csv(os.path.join(DATA_DIR, "y_val.csv")).squeeze()
print(f"Train: {X_train.shape} | Val: {X_val.shape}")

neg, pos = (y_train == 0).sum(), (y_train == 1).sum()
spw = neg / pos
print(f"Class balance — Non-default: {neg} | Default: {pos} | scale_pos_weight: {spw:.2f}")

def ks_score(y_true, y_proba, **kwargs):
    if len(np.unique(y_true)) < 2:
        return 0.0      # fold has only one class — skip gracefully
    fpr, tpr, _ = roc_curve(y_true, y_proba)
    return float(max(tpr - fpr))

ks_scorer = make_scorer(ks_score, needs_proba=True)

param_dist = {
    "n_estimators":     [300, 500, 800],
    "max_depth":        [2, 3, 4],
    "learning_rate":    [0.01, 0.02, 0.05],
    "subsample":        [0.6, 0.7, 0.8],
    "colsample_bytree": [0.6, 0.7, 0.8],
    "min_child_weight": [5, 7, 10, 15],
    "gamma":            [0, 0.1, 0.2, 0.3],
    "reg_alpha":        [0.1, 0.5, 1.0],
    "reg_lambda":       [3.0, 5.0, 8.0],
}

base = xgb.XGBClassifier(
    objective="binary:logistic", eval_metric="auc",
    scale_pos_weight=spw, use_label_encoder=False,
    random_state=42, tree_method="hist", n_jobs=1
)
print("\nRunning RandomizedSearchCV (80 iterations, optimizing KS)...")
search = RandomizedSearchCV(
    base, param_distributions=param_dist,
    n_iter=80, scoring=ks_scorer,
    cv=5, verbose=1, random_state=42, n_jobs=1
)
search.fit(X_train, y_train)
print(f"CV results sample: {search.cv_results_['mean_test_score'][:5]}")
print(f"\nBest CV KS : {search.best_score_:.4f}")
print(f"Best params: {search.best_params_}")

best = search.best_params_
model = xgb.XGBClassifier(
    **best, objective="binary:logistic", eval_metric="auc",
    scale_pos_weight=spw, use_label_encoder=False,
    random_state=42, tree_method="hist", n_jobs=1,
    early_stopping_rounds=50
)
model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
print(f"Best iteration: {model.best_iteration}")

y_proba = model.predict_proba(X_val)[:, 1]
y_pred  = (y_proba >= 0.50).astype(int)
auc     = roc_auc_score(y_val, y_proba)
fpr, tpr, _ = roc_curve(y_val, y_proba)
ks   = float(max(tpr - fpr))
gini = 2 * auc - 1

print(f"\n{'='*45}\n  VALIDATION METRICS\n{'='*45}")
print(f"  AUC-ROC  : {auc:.4f}")
print(f"  KS Stat  : {ks:.4f}")
print(f"  Gini     : {gini:.4f}")
print(f"\n{classification_report(y_val, y_pred, target_names=['Non-Default','Default'])}")
cm = confusion_matrix(y_val, y_pred)
print(f"Confusion Matrix:\n  TN={cm[0,0]}  FP={cm[0,1]}\n  FN={cm[1,0]}  TP={cm[1,1]}")

fi = pd.DataFrame({
    "feature":    X_train.columns,
    "importance": model.feature_importances_
}).sort_values("importance", ascending=False)
print(f"\nTop 15 Features:\n{fi.head(15).to_string(index=False)}")

with open(os.path.join(MODEL_DIR, "xgb_msme.pkl"), "wb") as f: pickle.dump(model, f)
with open(os.path.join(MODEL_DIR, "best_params.pkl"), "wb") as f: pickle.dump(best, f)
fi.to_csv(os.path.join(MODEL_DIR, "feature_importance.csv"), index=False)
print(f"\n✅ Model saved → {MODEL_DIR}/xgb_msme.pkl")
