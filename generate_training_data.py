import pandas as pd
import numpy as np

np.random.seed(42)
n_rows = 25000  # slightly larger → better imbalance handling later

print("🔄 Loading stats from your 3 real Kaggle datasets...")

# === EXACT FILENAMES FROM YOUR FOLDER ===
home_credit_file   = "application_train.csv"
indian_file        = "train.csv"
lending_club_file  = "accepted_2007_to_2018Q4.csv.gz"

# 1. Home Credit
hc = pd.read_csv(home_credit_file, nrows=60000)
hc_default_rate = hc['TARGET'].mean()
hc_income_mean  = hc['AMT_INCOME_TOTAL'].mean()
hc_income_std   = hc['AMT_INCOME_TOTAL'].std()

# 2. Indian Loan
ind = pd.read_csv(indian_file, nrows=60000)
if 'default' in ind.columns:
    ind_default_rate = ind['default'].mean()
elif 'Loan_Status' in ind.columns:
    ind_default_rate = (ind['Loan_Status'].isin(['N', 0, 'Default'])).mean()
else:
    ind_default_rate = 0.08

# 3. Lending Club
lc = pd.read_csv(lending_club_file, nrows=60000, low_memory=False, compression='gzip')
lc_default_rate = (lc['loan_status'].str.contains('Charged Off|Default', case=False, na=False)).mean()

print(f"Default rates → HomeCredit: {hc_default_rate:.1%} | Indian: {ind_default_rate:.1%} | LendingClub: {lc_default_rate:.1%}")

# Use median instead of mean to avoid Lending Club skew
base_default = np.median([hc_default_rate, ind_default_rate, lc_default_rate])
print(f"Using base default rate (median): {base_default:.1%}")

# ──────────────────────────────────────────────────────────────
# Generate features with more realistic / varied distributions
# ──────────────────────────────────────────────────────────────

data = {
    'utility_payment_consistency':   np.random.randint(0, 36, n_rows),                     # more chance of low streaks
    'avg_utility_dpd':               np.random.exponential(scale=8, size=n_rows),         # exponential → many low, few high
    'rent_wallet_share':             np.clip(np.random.normal(0.28, 0.12, n_rows), 0.05, 0.80),
    'subscription_commitment_ratio': np.clip(np.random.normal(0.14, 0.08, n_rows), 0.0, 0.45),

    'emergency_buffer_months':       np.random.exponential(scale=2.5, size=n_rows),
    'min_balance_violation_count':   np.random.poisson(lam=1.2, size=n_rows),
    'eod_balance_volatility':        np.random.beta(2, 5, n_rows) * 1.5,                  # skewed low
    'essential_vs_lifestyle_ratio':  np.random.uniform(0.5, 3.5, n_rows),
    'cash_withdrawal_dependency':    np.random.beta(1.5, 4, n_rows) * 0.8,
    'bounced_transaction_count':     np.random.poisson(lam=0.8, size=n_rows),

    'telecom_number_vintage_days':   np.random.randint(60, 365*5, n_rows),
    'telecom_recharge_drop_ratio':   1 + np.random.normal(0, 0.25, n_rows),               # centered around 1
    'academic_background_tier':      np.random.choice([1,2,3,4], n_rows, p=[0.12, 0.38, 0.35, 0.15]),
    'purpose_of_loan_encoded':       np.random.randint(0, 6, n_rows),

    'business_vintage_months':       np.random.randint(3, 180, n_rows),
    'revenue_growth_trend':          np.random.normal(0.03, 0.18, n_rows),
    'revenue_seasonality_index':     np.random.uniform(0.05, 0.9, n_rows),
    'operating_cashflow_ratio':      np.random.lognormal(mean=0, sigma=0.4, size=n_rows), # >1 more common
    'cashflow_volatility':           np.random.beta(3, 6, n_rows) * 1.2,
    'avg_invoice_payment_delay':     np.random.exponential(scale=12, size=n_rows),

    'customer_concentration_ratio':  np.random.beta(2, 5, n_rows),
    'repeat_customer_revenue_pct':   np.random.beta(4, 2, n_rows),
    'vendor_payment_discipline':     np.random.exponential(scale=10, size=n_rows),
    'gst_filing_consistency_score':  np.random.randint(0, 12, n_rows),
    'gst_to_bank_variance':          np.random.beta(1.5, 5, n_rows) * 0.4,

    # Fraud flags — low base rate, but very impactful
    'p2p_circular_loop_flag':        np.random.choice([0,1], n_rows, p=[0.96, 0.04]),
    'benford_anomaly_score':         np.random.beta(0.8, 5, n_rows) * 0.5,                # rare high values
    'round_number_spike_ratio':      np.random.beta(1, 6, n_rows) * 0.6,
    'turnover_inflation_spike':      np.random.choice([0,1], n_rows, p=[0.97, 0.03]),
    'identity_device_mismatch':      np.random.choice([0,1], n_rows, p=[0.98, 0.02])
}

df = pd.DataFrame(data)

# ──────────────────────────────────────────────────────────────
# Much better default probability logic
# ──────────────────────────────────────────────────────────────

# Use a slightly lower base to hit the sweet spot
base_default = 0.085   # ← changed from median to fixed realistic India NTC base

# ──────────────────────────────────────────────────────────────
# Much better default probability logic
# ──────────────────────────────────────────────────────────────
# Good signals (reduce risk) — slightly stronger
good_score = (
    0.25 * (df['utility_payment_consistency'] > 12) +
    0.22 * (df['operating_cashflow_ratio'] > 1.3) +
    0.18 * (df['emergency_buffer_months'] > 3) +
    0.15 * (df['gst_filing_consistency_score'] > 8)
)

# Bad signals — slightly reduced weight
bad_score = (
    0.28 * (df['avg_utility_dpd'] > 12) +
    0.22 * (df['eod_balance_volatility'] > 0.8) +
    0.18 * (df['bounced_transaction_count'] > 2) +
    0.16 * (df['cashflow_volatility'] > 0.7) +
    0.13 * (df['min_balance_violation_count'] > 3)
)

# Fraud overrides — keep strong but not extreme
fraud_boost = 3.0 * (
    df['p2p_circular_loop_flag'] +
    (df['benford_anomaly_score'] > 0.25) +
    df['identity_device_mismatch'] +
    df['turnover_inflation_spike']
)
# Combine → logistic function for smooth 0–1 probability
logit = np.log(base_default / (1 - base_default)) + good_score - bad_score + fraud_boost
default_prob = 1 / (1 + np.exp(-logit))  # sigmoid

df['default_prob'] = default_prob
df['default_label']  = (np.random.rand(n_rows) < default_prob).astype(int)

df.to_csv('pdr_training_data_v2.csv', index=False)

print(f"\n🎯 FINAL RESULTS")
print(f"Generated {n_rows:,} samples")
print(f"Target base rate (median): {base_default:.1%}")
print(f"Actual default rate:       {df['default_label'].mean():.1%}")
print(f"Default prob mean / median / 90th percentile: "
      f"{df['default_prob'].mean():.1%} / {df['default_prob'].median():.1%} / {df['default_prob'].quantile(0.90):.1%}")
print("\nFraud flag impact:")
print(df.groupby('p2p_circular_loop_flag')['default_label'].mean().round(3))
print("\nFile saved: pdr_training_data_v2.csv")
print("Next: update your training script to read 'pdr_training_data_v2.csv'")