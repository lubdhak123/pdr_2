# -*- coding: utf-8 -*-
"""
PDR Manual Scoring Demo - PDR (Paisa Do Re) by Barclays Hack-O-Fire 2026
==========================================================================
This script takes a RAW user profile + transaction history (JSON),
runs it through ALL 4 layers of the Trust-Gated Pipeline, and prints
a full audit-ready credit score report.

Usage:
    py manual_score.py
    py manual_score.py --profile custom_profile.json

Layer flow:
  JSON Input  ->  Layer 2 (Trust)  ->  Layer 3 (Feature Eng + XGBoost)  ->  Layer 4 (SHAP)
"""

import json
import sys
import os
import math
import warnings
import numpy as np
import pandas as pd
import joblib
import shap
from collections import defaultdict, Counter

warnings.filterwarnings("ignore")

# -------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------
MODEL_PATH   = os.path.join(os.path.dirname(__file__), "..", "pdr_model.pkl")
PROFILE_PATH = os.path.join(os.path.dirname(__file__), "defaulter_profile.json")

if len(sys.argv) > 1:
    PROFILE_PATH = sys.argv[1]

# -------------------------------------------------------------
# EXACT 30 FEATURE COLUMNS - must match training schema exactly
# -------------------------------------------------------------
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

# -------------------------------------------------------------
# LAYER 2 - TRUST INTELLIGENCE FILTERS
# -------------------------------------------------------------

def detect_circular_loops(txns: list) -> int:
    """
    Graph-based circular loop detection.
    Flags if money flows OUT to a party and then flows BACK IN from
    the SAME party (typical P2P wash/circular transaction pattern).
    """
    # Build a graph: party -> [amounts sent]
    credits_from = defaultdict(list)
    debits_to    = defaultdict(list)

    for t in txns:
        narr  = t['narration'].upper()
        amt   = abs(t['amount'])
        ttype = t['type'].upper()

        # Extract counter-party name (simple heuristic: last 2 words of narration)
        words = narr.replace("/", " ").split()
        party = " ".join(words[-2:]) if len(words) >= 2 else narr

        if ttype == "DEBIT":
            debits_to[party].append(amt)
        elif ttype == "CREDIT":
            credits_from[party].append(amt)

    # Check overlap: same party both sent to and received from
    loop_parties = set(debits_to.keys()) & set(credits_from.keys())
    loop_detected = 0
    for party in loop_parties:
        # Check for approximate amount matching (within 5%)
        for d_amt in debits_to[party]:
            for c_amt in credits_from[party]:
                if abs(d_amt - c_amt) / max(d_amt, c_amt, 1) < 0.05:
                    loop_detected = 1
                    break
    return loop_detected


def benford_anomaly_score(amounts: list) -> float:
    """
    Benford's Law: the first digit of natural financial amounts
    should follow a log distribution. High deviation = suspicious.
    Returns a score 0.0-1.0 (higher = more anomalous).
    """
    expected = {d: math.log10(1 + 1/d) for d in range(1, 10)}
    first_digits = []
    for a in amounts:
        s = str(int(abs(a))).lstrip("0")
        if s and s[0].isdigit() and s[0] != '0':
            first_digits.append(int(s[0]))

    if len(first_digits) < 10:
        return 0.0  # Not enough data

    observed_counts = Counter(first_digits)
    total = len(first_digits)
    observed_freq = {d: observed_counts.get(d, 0) / total for d in range(1, 10)}

    # Mean Absolute Deviation from Benford expectation
    mad = sum(abs(observed_freq.get(d, 0) - expected[d]) for d in range(1, 10)) / 9
    # Normalise to 0-1 range (typical MAD rarely exceeds 0.15 even in fraud)
    return min(mad / 0.15, 1.0)


def round_number_spike_ratio(amounts: list) -> float:
    """
    % of transaction amounts ending in 000 or 500 - common in cash stuffing.
    Natural spending rarely produces so many perfectly round numbers.
    """
    if not amounts:
        return 0.0
    round_count = sum(1 for a in amounts if abs(a) % 1000 == 0 or abs(a) % 500 == 0)
    return round_count / len(amounts)


def detect_turnover_inflation_spike(txns: list) -> int:
    """
    Detects if total credit volume spikes significantly in the 30-90 days
    before the most recent date (simulating pre-application inflation).
    Returns 1 if spike ratio > 3x compared to earlier months.
    """
    df = pd.DataFrame(txns)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    credits = df[df['type'] == 'CREDIT'].copy()
    if len(credits) < 5:
        return 0

    max_date  = credits['date'].max()
    cutoff    = max_date - pd.Timedelta(days=90)
    cutoff2   = max_date - pd.Timedelta(days=180)

    recent_vol = credits[credits['date'] >= cutoff]['amount'].sum()
    older_vol  = credits[(credits['date'] >= cutoff2) & (credits['date'] < cutoff)]['amount'].sum()

    if older_vol == 0:
        return 0

    ratio = recent_vol / older_vol
    return 1 if ratio > 2.5 else 0  # 2.5x spike threshold


# -------------------------------------------------------------
# LAYER 3 - FEATURE ENGINEERING FROM RAW TRANSACTIONS
# -------------------------------------------------------------

def engineer_features(profile: dict) -> dict:
    """
    Transforms raw user profile + transactions into all 30 ML features.
    Uses heuristics based on narration keywords + balance/amount series.
    """
    profile_info = profile.get("user_profile", {})
    txns         = profile.get("transactions", [])
    gst_data     = profile.get("gst_data", {})

    # -- Convert to DataFrame for easier analysis ---------------
    df = pd.DataFrame(txns)
    df['date']   = pd.to_datetime(df['date'])
    df['amount'] = df['amount'].astype(float)
    df = df.sort_values('date').reset_index(drop=True)

    credits = df[df['type'] == 'CREDIT']
    debits  = df[df['type'] == 'DEBIT']
    balances = df['balance'].tolist()
    amounts  = df['amount'].tolist()
    all_narr = " ".join(df['narration'].str.upper().tolist())

    total_credit  = credits['amount'].sum()
    total_debit   = abs(debits['amount'].sum())
    n_months      = max((df['date'].max() - df['date'].min()).days / 30, 1)

    # --- UTILITY / RECURRING PAYMENTS ------------------------
    UTILITY_KW = ['ELECTRICITY', 'WATER', 'BROADBAND', 'GAS', 'BSES', 'BESCOM', 'TPDDL',
                  'MSEDCL', 'TANGEDCO', 'MAHADISCOM', 'BOARD BILL', 'BILL PAID']

    utility_txns = df[df['narration'].str.upper().apply(
        lambda n: any(kw in n for kw in UTILITY_KW)
    )]

    # How many months had a utility payment
    utility_months = (utility_txns['date'].dt.to_period('M')
                      .nunique() if len(utility_txns) > 0 else 0)
    utility_payment_consistency = int(utility_months)  # 0-12+ months

    # Average days past due - proxy: if utility was paid after 15th of month = delay
    if len(utility_txns) > 0:
        avg_utility_dpd = float(utility_txns['date'].dt.day.clip(1, 60).mean()) - 5
        avg_utility_dpd = max(avg_utility_dpd, 0.0)
    else:
        avg_utility_dpd = 30.0  # penalty for no utility payments found

    # --- RENT SHARE -------------------------------------------
    RENT_KW = ['RENT', 'HOUSE RENT', 'RENTAL', 'LEASE PAYMENT', 'LANDLORD']
    rent_txns    = debits[debits['narration'].str.upper().apply(
        lambda n: any(kw in n for kw in RENT_KW)
    )]
    rent_total   = abs(rent_txns['amount'].sum())
    rent_wallet_share = float(rent_total / total_credit) if total_credit > 0 else 0.0
    rent_wallet_share = np.clip(rent_wallet_share, 0.0, 0.95)

    # --- SUBSCRIPTION & TELECOM ------------------------------
    SUB_KW   = ['NETFLIX', 'SPOTIFY', 'PRIME', 'HOTSTAR', 'RECHARGE', 'AIRTEL',
                'JIO', 'VODAFONE', 'BSNL', 'BROADBAND', 'ANNUAL SUBSCRIPTION']
    sub_txns = debits[debits['narration'].str.upper().apply(
        lambda n: any(kw in n for kw in SUB_KW)
    )]
    subscription_commitment_ratio = float(abs(sub_txns['amount'].sum()) / total_credit) \
        if total_credit > 0 else 0.0

    # Telecom recharge drop ratio: if recharge amounts drop month-over-month
    recharge_txns = df[df['narration'].str.upper().apply(
        lambda n: any(kw in n for kw in ['RECHARGE', 'AIRTEL', 'JIO', 'VODAFONE'])
    )]
    if len(recharge_txns) >= 2:
        monthly_recharge = recharge_txns.groupby(recharge_txns['date'].dt.to_period('M'))['amount'].sum().abs()
        if len(monthly_recharge) >= 2:
            first_half = monthly_recharge.iloc[:len(monthly_recharge)//2].mean()
            second_half= monthly_recharge.iloc[len(monthly_recharge)//2:].mean()
            telecom_recharge_drop_ratio = float(second_half / first_half) if first_half > 0 else 1.0
        else:
            telecom_recharge_drop_ratio = 1.0
    else:
        telecom_recharge_drop_ratio = 0.8  # no recharge data = slight negative

    # --- LIQUIDITY --------------------------------------------
    avg_balance            = np.mean(balances) if balances else 0
    std_balance            = np.std(balances)  if balances else 0
    eod_balance_volatility = float(std_balance / max(abs(avg_balance), 1))

    # Emergency buffer: avg balance / monthly expenses
    monthly_expenses = total_debit / n_months if n_months > 0 else 1
    emergency_buffer_months = float(avg_balance / monthly_expenses) if monthly_expenses > 0 else 0.1
    emergency_buffer_months = np.clip(emergency_buffer_months, 0.0, 12.0)

    # Min balance violations: balance dropped below Rs.500 (common threshold)
    min_balance_violation_count = int(sum(1 for b in balances if b < 500))

    # --- CASH & SPENDING BEHAVIOUR ---------------------------
    CASH_KW = ['CASH WITHDRAWAL', 'ATM', 'ATW']
    cash_txns = debits[debits['narration'].str.upper().apply(
        lambda n: any(kw in n for kw in CASH_KW)
    )]
    cash_withdrawal_dependency = float(abs(cash_txns['amount'].sum()) / total_debit) \
        if total_debit > 0 else 0.0

    ESSENTIAL_KW = ['ELECTRICITY', 'WATER', 'RENT', 'GROCERY', 'MEDICAL', 'FUEL',
                    'BILL', 'BROADBAND', 'GAS', 'INSURANCE']
    LIFESTYLE_KW = ['RESTAURANT', 'HOTEL', 'TRAVEL', 'ZOMATO', 'SWIGGY', 'MYNTRA',
                    'AMAZON', 'FLIPKART', 'ENTERTAINMENT', 'MALL']
    essential_spend = abs(debits[debits['narration'].str.upper().apply(
        lambda n: any(kw in n for kw in ESSENTIAL_KW))]['amount'].sum())
    lifestyle_spend = abs(debits[debits['narration'].str.upper().apply(
        lambda n: any(kw in n for kw in LIFESTYLE_KW))]['amount'].sum())
    essential_vs_lifestyle_ratio = float(essential_spend / max(lifestyle_spend, 1))
    essential_vs_lifestyle_ratio = np.clip(essential_vs_lifestyle_ratio, 0.1, 10.0)

    BOUNCE_KW = ['BOUNCE', 'BOUNCED', 'RTN', 'RETURN', 'DISHONOUR', 'DISHOR',
                 'CHEQUE RETURN', 'BOUNCE CHG']
    bounced_transaction_count = int(sum(
        1 for n in df['narration'].str.upper() if any(kw in n for kw in BOUNCE_KW)
    ))

    # --- CASHFLOW (Revenue Proxy) -----------------------------
    monthly_credits = credits.groupby(credits['date'].dt.to_period('M'))['amount'].sum()
    if len(monthly_credits) >= 2:
        growth_rates = monthly_credits.pct_change().dropna()
        revenue_growth_trend      = float(growth_rates.mean())
        revenue_seasonality_index = float(growth_rates.std())
    else:
        revenue_growth_trend      = 0.0
        revenue_seasonality_index = 0.5

    operating_cashflow_ratio = float(total_credit / max(total_debit, 1))
    cashflow_volatility      = float(monthly_credits.std() / max(monthly_credits.mean(), 1)) \
        if len(monthly_credits) > 1 else 0.5

    # --- INVOICE / VENDOR -------------------------------------
    INV_KW = ['INVOICE', 'VENDOR', 'SUPPLIER', 'PAYMENT TO', 'PARTY PAYMENT']
    invoice_txns = debits[debits['narration'].str.upper().apply(
        lambda n: any(kw in n for kw in INV_KW)
    )]
    # Average delay: proxy by day-of-month of invoice payments
    avg_invoice_payment_delay = float(invoice_txns['date'].dt.day.mean()) \
        if len(invoice_txns) > 0 else 20.0

    vendor_payment_discipline = float(abs(invoice_txns['amount'].sum()) / total_debit) * 100 \
        if total_debit > 0 else 10.0

    # --- CUSTOMER CONCENTRATION -------------------------------
    # How concentrated are credits? High = few large customers
    credit_amounts = credits['amount'].values
    if len(credit_amounts) > 0:
        credit_shares = credit_amounts / credit_amounts.sum()
        # Herfindahl-Hirschman Index normalized to 0-1
        customer_concentration_ratio = float(np.sum(credit_shares ** 2))
    else:
        customer_concentration_ratio = 0.5

    # Repeat customer revenue % - proxy: narrations with "INVOICE" mentioning same parties
    CUST_KW = ['CUSTOMER', 'INVOICE', 'CLIENT', 'NEFT FROM', 'PAYMENT FROM']
    repeat_txns = credits[credits['narration'].str.upper().apply(
        lambda n: any(kw in n for kw in CUST_KW)
    )]
    repeat_customer_revenue_pct = float(repeat_txns['amount'].sum() / max(total_credit, 1))
    repeat_customer_revenue_pct = np.clip(repeat_customer_revenue_pct, 0.0, 1.0)

    # --- GST VARIANCE ----------------------------------------
    if gst_data.get("available") and gst_data.get("declared_turnover", 0) > 0:
        gst_declared = gst_data["declared_turnover"]
        gst_to_bank_variance = float(abs(total_credit - gst_declared) / max(total_credit, 1))
    else:
        gst_to_bank_variance = 0.0  # Unknown, set neutral

    # --- PROFILE-LEVEL DIRECT FEATURES -----------------------
    telecom_number_vintage_days = int(profile_info.get("telecom_number_vintage_days", 365))
    academic_background_tier    = int(profile_info.get("academic_background_tier", 2))
    purpose_of_loan_encoded     = int(profile_info.get("purpose_of_loan_encoded", 0))
    business_vintage_months     = int(profile_info.get("business_vintage_months", 24))
    gst_filing_consistency_score= int(profile_info.get("gst_filing_consistency_score", 6))

    # --- LAYER 2 FRAUD FLAGS ----------------------------------
    # (These OVERRIDE good financial signals if triggered)
    amt_list = [abs(a) for a in amounts if a != 0]

    p2p_circular_loop_flag    = detect_circular_loops(txns)
    benford_score             = benford_anomaly_score(amt_list)
    round_spike               = round_number_spike_ratio(amt_list)
    turnover_spike            = detect_turnover_inflation_spike(txns)
    # identity_device_mismatch: not detectable from bank data alone, default 0
    identity_device_mismatch  = 0

    # --- ASSEMBLE FINAL 30-FEATURE DICT ----------------------
    features = {
        'utility_payment_consistency':    utility_payment_consistency,
        'avg_utility_dpd':                avg_utility_dpd,
        'rent_wallet_share':              rent_wallet_share,
        'subscription_commitment_ratio':  np.clip(subscription_commitment_ratio, 0.0, 0.5),
        'emergency_buffer_months':        emergency_buffer_months,
        'min_balance_violation_count':    min_balance_violation_count,
        'eod_balance_volatility':         np.clip(eod_balance_volatility, 0.0, 5.0),
        'essential_vs_lifestyle_ratio':   essential_vs_lifestyle_ratio,
        'cash_withdrawal_dependency':     np.clip(cash_withdrawal_dependency, 0.0, 1.0),
        'bounced_transaction_count':      bounced_transaction_count,
        'telecom_number_vintage_days':    telecom_number_vintage_days,
        'telecom_recharge_drop_ratio':    np.clip(telecom_recharge_drop_ratio, 0.1, 3.0),
        'academic_background_tier':       academic_background_tier,
        'purpose_of_loan_encoded':        purpose_of_loan_encoded,
        'business_vintage_months':        business_vintage_months,
        'revenue_growth_trend':           np.clip(revenue_growth_trend, -1.0, 2.0),
        'revenue_seasonality_index':      np.clip(revenue_seasonality_index, 0.0, 2.0),
        'operating_cashflow_ratio':       np.clip(operating_cashflow_ratio, 0.0, 10.0),
        'cashflow_volatility':            np.clip(cashflow_volatility, 0.0, 3.0),
        'avg_invoice_payment_delay':      avg_invoice_payment_delay,
        'customer_concentration_ratio':   customer_concentration_ratio,
        'repeat_customer_revenue_pct':    repeat_customer_revenue_pct,
        'vendor_payment_discipline':      vendor_payment_discipline,
        'gst_filing_consistency_score':   gst_filing_consistency_score,
        'gst_to_bank_variance':           np.clip(gst_to_bank_variance, 0.0, 1.0),
        'p2p_circular_loop_flag':         p2p_circular_loop_flag,
        'benford_anomaly_score':          benford_score,
        'round_number_spike_ratio':       round_spike,
        'turnover_inflation_spike':       turnover_spike,
        'identity_device_mismatch':       identity_device_mismatch,
    }
    return features


# -------------------------------------------------------------
# LAYER 4 - EXPLAINABLE AI (SHAP Reason Codes)
# -------------------------------------------------------------

FEATURE_DESCRIPTIONS = {
    'utility_payment_consistency':   "Utility bill payment streak (months)",
    'avg_utility_dpd':               "Average days past due on utility bills",
    'rent_wallet_share':             "Rent as % of total income",
    'subscription_commitment_ratio': "Subscription payments as % of income",
    'emergency_buffer_months':       "Emergency buffer (months of expenses saved)",
    'min_balance_violation_count':   "Times balance dropped below Rs.500",
    'eod_balance_volatility':        "Day-end balance volatility (std/mean)",
    'essential_vs_lifestyle_ratio':  "Essential vs lifestyle spending ratio",
    'cash_withdrawal_dependency':    "Cash withdrawals as % of total debits",
    'bounced_transaction_count':     "Number of bounced/returned transactions",
    'telecom_number_vintage_days':   "Mobile number age (days)",
    'telecom_recharge_drop_ratio':   "Telecom recharge trend (drop = risk)",
    'academic_background_tier':      "Academic background tier (1=highest)",
    'purpose_of_loan_encoded':       "Purpose of loan category",
    'business_vintage_months':       "Business age (months)",
    'revenue_growth_trend':          "Month-over-month revenue growth trend",
    'revenue_seasonality_index':     "Revenue seasonality / inconsistency",
    'operating_cashflow_ratio':      "Operating cashflow ratio (credit/debit)",
    'cashflow_volatility':           "Cashflow volatility across months",
    'avg_invoice_payment_delay':     "Average invoice payment delay (days)",
    'customer_concentration_ratio':  "Customer concentration index (HHI)",
    'repeat_customer_revenue_pct':   "% revenue from repeat customers",
    'vendor_payment_discipline':     "Vendor payment discipline score",
    'gst_filing_consistency_score':  "GST filing consistency (months filed)",
    'gst_to_bank_variance':          "GST declared vs bank turnover variance",
    'p2p_circular_loop_flag':        "[!]  P2P CIRCULAR LOOP DETECTED",
    'benford_anomaly_score':         "[!]  Benford's Law anomaly score",
    'round_number_spike_ratio':      "[!]  Round-number transaction spike ratio",
    'turnover_inflation_spike':      "[!]  Turnover inflation spike (pre-application)",
    'identity_device_mismatch':      "[!]  Identity/device mismatch flag",
}

RISK_THRESHOLDS = [
    (0.05,  "A", "[A] VERY LOW RISK",   "Eligible for prime rates. High creditworthiness."),
    (0.12,  "B", "[B] LOW RISK",        "Eligible for standard lending. Minor monitoring."),
    (0.22,  "C", "[C] MODERATE RISK",   "Eligible with enhanced due diligence. Higher rate."),
    (0.40,  "D", "[D] HIGH RISK",       "Requires collateral or guarantor. High risk category."),
    (1.01,  "E", "[E] VERY HIGH RISK",  "DECLINE recommended. Fraud signals or deep distress."),
]


def classify_pd(pd_score: float):
    for threshold, grade, label, description in RISK_THRESHOLDS:
        if pd_score < threshold:
            return grade, label, description
    return "E", "[E] VERY HIGH RISK", "DECLINE recommended."


def run_scoring_pipeline(profile_path: str):
    print("\n" + "="*65)
    print("  PDR - Paisa Do Re  |  Barclays Hack-O-Fire 2026")
    print("  Alternate Credit Scoring - Manual Evaluation Report")
    print("="*65)

    # -- Load profile -----------------------------------------
    with open(profile_path, 'r') as f:
        profile = json.load(f)

    user = profile.get("user_profile", {})
    txns = profile.get("transactions", [])
    print(f"\n  Applicant    : {user.get('name', 'Unknown')}")
    print(f"  Phone        : {user.get('phone', 'N/A')}")
    print(f"  Business     : {user.get('business_type', 'N/A')} | {user.get('city', 'N/A')}")
    print(f"  Vintage      : {user.get('business_vintage_months')} months")
    print(f"  Transactions : {len(txns)} records provided")

    # -- Layer 2: Trust Intelligence ---------------------------
    print("\n" + "-"*65)
    print("  LAYER 2 - TRUST INTELLIGENCE FILTERS")
    print("-"*65)

    features = engineer_features(profile)

    trust_results = {
        "P2P Circular Loop"          : ("[FLAGGED]" if features['p2p_circular_loop_flag'] else "[CLEAR]", features['p2p_circular_loop_flag']),
        "Benford Anomaly Score"       : (f"{features['benford_anomaly_score']:.3f}", features['benford_anomaly_score'] > 0.25),
        "Round Number Spike"          : (f"{features['round_number_spike_ratio']:.1%}", features['round_number_spike_ratio'] > 0.3),
        "Turnover Inflation Spike"    : ("[FLAGGED]" if features['turnover_inflation_spike'] else "[CLEAR]", features['turnover_inflation_spike']),
        "Identity/Device Mismatch"    : ("[FLAGGED]" if features['identity_device_mismatch'] else "[CLEAR]", features['identity_device_mismatch']),
    }

    fraud_flags_count = sum(1 for _, (_, flagged) in trust_results.items() if flagged)
    for check_name, (status, flagged) in trust_results.items():
        indicator = "[!!] " if flagged else "[OK] "
        print(f"  {indicator}{check_name:<30} : {status}")

    if fraud_flags_count > 0:
        print(f"\n  *** {fraud_flags_count} FRAUD SIGNAL(S) DETECTED - these override positive financials ***")
    else:
        print("\n  [PASS] All trust filters passed.")

    # -- Layer 3: Feature Engineering Summary ------------------
    print("\n" + "-"*65)
    print("  LAYER 3 - ENGINEERED FEATURES SNAPSHOT (key signals)")
    print("-"*65)
    key_features = [
        ('utility_payment_consistency', features['utility_payment_consistency'], "months"),
        ('avg_utility_dpd',             features['avg_utility_dpd'],             "days"),
        ('bounced_transaction_count',   features['bounced_transaction_count'],   "events"),
        ('min_balance_violation_count', features['min_balance_violation_count'], "events"),
        ('cash_withdrawal_dependency',  features['cash_withdrawal_dependency'],  "(ratio)"),
        ('eod_balance_volatility',      features['eod_balance_volatility'],      "(std/avg)"),
        ('operating_cashflow_ratio',    features['operating_cashflow_ratio'],    "(credit/debit)"),
        ('emergency_buffer_months',     features['emergency_buffer_months'],     "months"),
        ('round_number_spike_ratio',    features['round_number_spike_ratio'],    "(ratio)"),
        ('benford_anomaly_score',       features['benford_anomaly_score'],       "(score)"),
    ]
    for fname, fval, unit in key_features:
        if isinstance(fval, float):
            print(f"  {fname:<35} = {fval:>8.3f}  {unit}")
        else:
            print(f"  {fname:<35} = {fval:>8}  {unit}")

    # -- Load model & predict ----------------------------------
    print("\n" + "-"*65)
    print("  LAYER 3 - XGBOOST PROBABILITY OF DEFAULT (PD)")
    print("-"*65)

    model = joblib.load(MODEL_PATH)
    explainer = shap.TreeExplainer(model)

    input_df = pd.DataFrame([features])[FEATURE_COLS]
    pd_score = float(model.predict_proba(input_df)[0][1])
    grade, risk_label, risk_description = classify_pd(pd_score)

    print(f"\n  Probability of Default (PD) : {pd_score*100:>6.2f}%")
    print(f"  Risk Grade                  :    {grade}")
    print(f"  Risk Category               : {risk_label}")
    print(f"  Decision Guidance           : {risk_description}")

    # -- Layer 4: SHAP Explanations ----------------------------
    print("\n" + "-"*65)
    print("  LAYER 4 - EXPLAINABILITY (Top 10 SHAP Reason Codes)")
    print("-"*65)

    shap_values = explainer.shap_values(input_df)
    sv = shap_values[0]  # single-row, shape (30,)
    sorted_idx = np.argsort(np.abs(sv))[::-1][:10]

    print(f"\n  {'#':<3} {'Feature':<35} {'Value':>10}  {'SHAP':>9}  Direction")
    print(f"  {'-'*3} {'-'*35} {'-'*10}  {'-'*9}  {'-'*20}")

    reason_codes = []
    for rank, idx in enumerate(sorted_idx, 1):
        feat_name  = FEATURE_COLS[idx]
        feat_desc  = FEATURE_DESCRIPTIONS.get(feat_name, feat_name)
        feat_val   = features[feat_name]
        shap_val   = sv[idx]
        direction  = "^ INCREASES RISK" if shap_val > 0 else "v REDUCES  RISK"
        severity   = "[!!]" if shap_val > 0.1 else ("[OK]" if shap_val < -0.05 else "    ")

        if isinstance(feat_val, float):
            val_str = f"{feat_val:>10.3f}"
        else:
            val_str = f"{feat_val:>10}"

        print(f"  {rank:<3} {feat_name:<35} {val_str}  {shap_val:>+9.4f}  {severity} {direction}")
        reason_codes.append({
            "rank"      : rank,
            "feature"   : feat_name,
            "description": feat_desc,
            "value"     : round(float(feat_val), 4),
            "shap"      : round(float(shap_val), 4),
            "direction" : direction
        })

    # -- Final Summary -----------------------------------------
    print("\n" + "="*65)
    print("  FINAL AUDIT-READY SUMMARY")
    print("="*65)
    print(f"  Applicant      : {user.get('name', 'Unknown')}")
    print(f"  PD Score       : {pd_score*100:.2f}%")
    print(f"  Risk Grade     : {grade}")
    print(f"  Decision       : {risk_label}")
    print(f"  Fraud Flags    : {fraud_flags_count}/5 triggered")
    print(f"\n  Top 3 Risk Drivers:")
    for r in reason_codes[:3]:
        arrow = "[^]" if r['shap'] > 0 else "[v]"
        print(f"  {arrow} [{r['rank']}] {r['description']}")
        print(f"      Value: {r['value']}  |  SHAP contribution: {r['shap']:+.4f}")
    print("\n" + "="*65)
    print("  Report generated by PDR - Paisa Do Re  |  2026-03-18")
    print("="*65 + "\n")

    return {
        "pd"          : round(pd_score, 4),
        "grade"       : grade,
        "risk_label"  : risk_label,
        "fraud_flags" : fraud_flags_count,
        "reason_codes": reason_codes[:5],
        "features"    : features,
    }


if __name__ == "__main__":
    result = run_scoring_pipeline(PROFILE_PATH)
