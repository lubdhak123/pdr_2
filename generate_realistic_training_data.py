import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ================== DIVERSE BORROWER ARCHETYPES ==================

def generate_good_borrower(user_id):
    archetype = random.choice([
        'it_professional', 'seasonal_farmer', 'retired_pension',
        'nri_remittance', 'doctor_practice', 'export_importer',
        'clean_sme', 'housewife_business', 'real_estate_agent', 'influencer'
    ])

    base_profile = {
        "business_vintage_months": random.randint(24, 120),
        "academic_background_tier": random.choice([1, 2, 3]),
        "purpose_of_loan_encoded": random.choice([1, 2, 3]),
        "telecom_number_vintage_days": random.randint(400, 3000),
        "gst_filing_consistency_score": random.randint(4, 12),
        "city": random.choice(["Mumbai", "Bengaluru", "Chennai", "Hyderabad", "Pune"]),
    }

    transactions = []
    base_date = datetime(2023, 6, 1)
    balance = random.randint(50000, 300000)

    if archetype == 'it_professional':
        base_profile["name"] = f"GoodIT_{user_id}"
        for month in range(6):
            date = base_date + timedelta(days=month*30 + random.randint(1, 5))
            amt = random.randint(80000, 150000)
            balance += amt
            transactions.append({"date": date.strftime("%Y-%m-%d"), "amount": amt, "type": "CREDIT", "narration": "NEFT FROM CLIENT INVOICE", "balance": balance})
            balance -= random.randint(1500, 3000)
            transactions.append({"date": (date + timedelta(days=3)).strftime("%Y-%m-%d"), "amount": -random.randint(1500, 3000), "type": "DEBIT", "narration": "ELECTRICITY BILL PAYMENT", "balance": balance})
            balance -= random.randint(15000, 25000)
            transactions.append({"date": (date + timedelta(days=5)).strftime("%Y-%m-%d"), "amount": -random.randint(15000, 25000), "type": "DEBIT", "narration": "OFFICE RENT HDFC", "balance": balance})

    elif archetype == 'seasonal_farmer':
        base_profile["name"] = f"GoodFarmer_{user_id}"
        base_profile["gst_filing_consistency_score"] = random.randint(3, 6)
        harvest_months = random.sample(range(6), 2)
        for month in range(6):
            date = base_date + timedelta(days=month*30 + random.randint(1, 10))
            if month in harvest_months:
                amt = random.randint(150000, 400000)
                balance += amt
                transactions.append({"date": date.strftime("%Y-%m-%d"), "amount": amt, "type": "CREDIT", "narration": "MANDI PAYMENT CROP SALE", "balance": balance})
            small_exp = random.randint(2000, 8000)
            balance -= small_exp
            transactions.append({"date": (date + timedelta(days=5)).strftime("%Y-%m-%d"), "amount": -small_exp, "type": "DEBIT", "narration": "GROCERY KIRANA STORE", "balance": balance})

    elif archetype == 'retired_pension':
        base_profile["name"] = f"GoodRetired_{user_id}"
        base_profile["business_vintage_months"] = random.randint(0, 12)
        base_profile["gst_filing_consistency_score"] = random.randint(0, 2)
        for month in range(6):
            date = base_date + timedelta(days=month*30 + random.randint(1, 3))
            amt = random.randint(25000, 60000)
            balance += amt
            transactions.append({"date": date.strftime("%Y-%m-%d"), "amount": amt, "type": "CREDIT", "narration": "PENSION CREDIT GOVT", "balance": balance})
            balance -= random.randint(5000, 15000)
            transactions.append({"date": (date + timedelta(days=5)).strftime("%Y-%m-%d"), "amount": -random.randint(5000, 15000), "type": "DEBIT", "narration": "MEDICAL PHARMACY APOLLO", "balance": balance})
            balance -= random.randint(2000, 5000)
            transactions.append({"date": (date + timedelta(days=10)).strftime("%Y-%m-%d"), "amount": -random.randint(2000, 5000), "type": "DEBIT", "narration": "GROCERY BIGBASKET", "balance": balance})

    elif archetype == 'nri_remittance':
        base_profile["name"] = f"GoodNRI_{user_id}"
        base_profile["gst_filing_consistency_score"] = random.randint(0, 3)
        for month in range(6):
            date = base_date + timedelta(days=month*30 + random.randint(1, 8))
            amt = random.randint(80000, 200000)
            balance += amt
            transactions.append({"date": date.strftime("%Y-%m-%d"), "amount": amt, "type": "CREDIT", "narration": "INWARD REMITTANCE SWIFT USD", "balance": balance})
            balance -= random.randint(10000, 30000)
            transactions.append({"date": (date + timedelta(days=3)).strftime("%Y-%m-%d"), "amount": -random.randint(10000, 30000), "type": "DEBIT", "narration": "FAMILY TRANSFER NEFT", "balance": balance})

    elif archetype == 'doctor_practice':
        base_profile["name"] = f"GoodDoctor_{user_id}"
        for month in range(6):
            date = base_date + timedelta(days=month*30 + random.randint(1, 5))
            for _ in range(random.randint(8, 15)):
                amt = random.randint(500, 3000)
                balance += amt
                transactions.append({"date": date.strftime("%Y-%m-%d"), "amount": amt, "type": "CREDIT", "narration": "UPI PATIENT CONSULTATION", "balance": balance})
                date += timedelta(days=1)
            balance -= random.randint(20000, 50000)
            transactions.append({"date": date.strftime("%Y-%m-%d"), "amount": -random.randint(20000, 50000), "type": "DEBIT", "narration": "CLINIC RENT PAYMENT", "balance": balance})

    elif archetype == 'export_importer':
        base_profile["name"] = f"GoodExport_{user_id}"
        for month in range(6):
            date = base_date + timedelta(days=month*30 + random.randint(5, 20))
            amt = random.randint(200000, 800000)
            balance += amt
            transactions.append({"date": date.strftime("%Y-%m-%d"), "amount": amt, "type": "CREDIT", "narration": "EXPORT PROCEEDS FOREX HDFC", "balance": balance})
            balance -= random.randint(150000, 600000)
            transactions.append({"date": (date + timedelta(days=3)).strftime("%Y-%m-%d"), "amount": -random.randint(150000, 600000), "type": "DEBIT", "narration": "SUPPLIER PAYMENT TT", "balance": balance})

    elif archetype == 'clean_sme':
        base_profile["name"] = f"GoodSME_{user_id}"
        for month in range(6):
            date = base_date + timedelta(days=month*30 + random.randint(1, 5))
            amt = random.randint(100000, 300000)
            balance += amt
            transactions.append({"date": date.strftime("%Y-%m-%d"), "amount": amt, "type": "CREDIT", "narration": "NEFT FROM DISTRIBUTOR", "balance": balance})
            balance -= random.randint(1500, 3000)
            transactions.append({"date": (date + timedelta(days=2)).strftime("%Y-%m-%d"), "amount": -random.randint(1500, 3000), "type": "DEBIT", "narration": "ELECTRICITY BILL PAYMENT", "balance": balance})
            balance -= random.randint(30000, 80000)
            transactions.append({"date": (date + timedelta(days=5)).strftime("%Y-%m-%d"), "amount": -random.randint(30000, 80000), "type": "DEBIT", "narration": "VENDOR PAYMENT RTGS", "balance": balance})

    elif archetype == 'housewife_business':
        base_profile["name"] = f"GoodHW_{user_id}"
        base_profile["business_vintage_months"] = random.randint(6, 36)
        base_profile["gst_filing_consistency_score"] = random.randint(2, 6)
        for month in range(6):
            date = base_date + timedelta(days=month*30 + random.randint(1, 10))
            for _ in range(random.randint(5, 12)):
                amt = random.randint(1000, 8000)
                balance += amt
                transactions.append({"date": date.strftime("%Y-%m-%d"), "amount": amt, "type": "CREDIT", "narration": "UPI CUSTOMER PAYMENT", "balance": balance})
                date += timedelta(days=2)
            balance -= random.randint(5000, 15000)
            transactions.append({"date": date.strftime("%Y-%m-%d"), "amount": -random.randint(5000, 15000), "type": "DEBIT", "narration": "RAW MATERIAL PURCHASE", "balance": balance})

    elif archetype == 'real_estate_agent':
        base_profile["name"] = f"GoodREA_{user_id}"
        for month in range(6):
            date = base_date + timedelta(days=month*30 + random.randint(1, 15))
            if random.random() > 0.5:
                amt = random.randint(100000, 500000)
                balance += amt
                transactions.append({"date": date.strftime("%Y-%m-%d"), "amount": amt, "type": "CREDIT", "narration": "COMMISSION RECEIPT PROPERTY", "balance": balance})
            balance -= random.randint(5000, 20000)
            transactions.append({"date": (date + timedelta(days=5)).strftime("%Y-%m-%d"), "amount": -random.randint(5000, 20000), "type": "DEBIT", "narration": "FUEL VEHICLE MAINTENANCE", "balance": balance})

    elif archetype == 'influencer':
        base_profile["name"] = f"GoodInfluencer_{user_id}"
        base_profile["gst_filing_consistency_score"] = random.randint(3, 7)
        for month in range(6):
            date = base_date + timedelta(days=month*30 + random.randint(1, 10))
            for _ in range(random.randint(2, 5)):
                amt = random.randint(10000, 80000)
                balance += amt
                transactions.append({"date": date.strftime("%Y-%m-%d"), "amount": amt, "type": "CREDIT", "narration": "BRAND DEAL PAYMENT NEFT", "balance": balance})
                date += timedelta(days=3)
            balance -= random.randint(5000, 20000)
            transactions.append({"date": date.strftime("%Y-%m-%d"), "amount": -random.randint(5000, 20000), "type": "DEBIT", "narration": "AMAZON EQUIPMENT PURCHASE", "balance": balance})

    if random.random() < 0.15:
        bounce_date = date + timedelta(days=random.randint(6, 12))
        balance -= 500
        transactions.append({
            "date": bounce_date.strftime("%Y-%m-%d"),
            "amount": -500,
            "type": "DEBIT",
            "narration": "CHEQUE BOUNCE CHG",
            "balance": balance
        })

    gst_turnover = sum(t['amount'] for t in transactions if t['type'] == 'CREDIT')
    return {
        "id": user_id, "true_label": 0, "archetype": archetype,
        "profile": {
            "user_profile": base_profile,
            "transactions": transactions,
            "gst_data": {"available": random.random() > 0.2, "declared_turnover": gst_turnover * random.uniform(0.9, 1.1)}
        }
    }


def generate_bad_borrower(user_id):
    archetype = random.choice([
        'wash_trader', 'ghost_gst', 'loan_stacker',
        'salary_inflator', 'cash_hoarder', 'kirana_bounce', 'gig_stress'
    ])

    base_profile = {
        "business_vintage_months": random.randint(2, 18),
        "academic_background_tier": random.choice([2, 3, 4]),
        "purpose_of_loan_encoded": random.choice([2, 3, 4]),
        "telecom_number_vintage_days": random.randint(30, 800),
        "gst_filing_consistency_score": random.randint(0, 6),
        "city": random.choice(["Delhi", "Kanpur", "Patna", "Agra"]),
    }

    transactions = []
    base_date = datetime(2023, 6, 1)
    balance = random.randint(500, 5000)

    if archetype == 'wash_trader':
        base_profile["name"] = f"BadWash_{user_id}"
        for month in range(6):
            date = base_date + timedelta(days=month*30 + random.randint(1, 5))
            amt = random.choice([50000, 100000, 200000])
            balance += amt
            transactions.append({"date": date.strftime("%Y-%m-%d"), "amount": amt, "type": "CREDIT", "narration": "UPI FROM SHYAM", "balance": balance})
            balance -= amt - random.randint(100, 500)
            transactions.append({"date": (date + timedelta(days=1)).strftime("%Y-%m-%d"), "amount": -(amt - random.randint(100, 500)), "type": "DEBIT", "narration": "UPI TO SHYAM", "balance": balance})
            if random.random() > 0.4:
                balance -= 500
                transactions.append({"date": (date + timedelta(days=2)).strftime("%Y-%m-%d"), "amount": -500, "type": "DEBIT", "narration": "CHEQUE BOUNCE CHG", "balance": balance})

    elif archetype == 'ghost_gst':
        base_profile["name"] = f"BadGST_{user_id}"
        for month in range(6):
            date = base_date + timedelta(days=month*30 + random.randint(1, 10))
            amt = random.randint(100000, 300000)
            balance += amt
            transactions.append({"date": date.strftime("%Y-%m-%d"), "amount": amt, "type": "CREDIT", "narration": "UPI TRANSFER UNKNOWN ROUND", "balance": balance})
            balance -= amt
            transactions.append({"date": (date + timedelta(days=1)).strftime("%Y-%m-%d"), "amount": -amt, "type": "DEBIT", "narration": "ATM CASH WITHDRAWAL", "balance": balance})

    elif archetype == 'loan_stacker':
        base_profile["name"] = f"BadStack_{user_id}"
        for month in range(6):
            date = base_date + timedelta(days=month*30 + random.randint(1, 5))
            amt = random.randint(50000, 150000)
            balance += amt
            transactions.append({"date": date.strftime("%Y-%m-%d"), "amount": amt, "type": "CREDIT", "narration": "LOAN DISBURSAL FINTECH", "balance": balance})
            balance -= random.randint(40000, 130000)
            transactions.append({"date": (date + timedelta(days=2)).strftime("%Y-%m-%d"), "amount": -random.randint(40000, 130000), "type": "DEBIT", "narration": "EMI REPAYMENT MULTIBANK", "balance": balance})
            if random.random() > 0.5:
                balance -= 500
                transactions.append({"date": (date + timedelta(days=5)).strftime("%Y-%m-%d"), "amount": -500, "type": "DEBIT", "narration": "CHEQUE BOUNCE CHG", "balance": balance})

    elif archetype == 'salary_inflator':
        base_profile["name"] = f"BadInflate_{user_id}"
        for month in range(6):
            date = base_date + timedelta(days=month*30 + random.randint(1, 3))
            amt = random.choice([100000, 200000, 300000])
            balance += amt
            transactions.append({"date": date.strftime("%Y-%m-%d"), "amount": amt, "type": "CREDIT", "narration": "NEFT SALARY CREDIT", "balance": balance})
            balance -= amt - random.randint(1000, 3000)
            transactions.append({"date": (date + timedelta(days=1)).strftime("%Y-%m-%d"), "amount": -(amt - random.randint(1000, 3000)), "type": "DEBIT", "narration": "ATM CASH WITHDRAWAL", "balance": balance})

    elif archetype == 'cash_hoarder':
        base_profile["name"] = f"BadCash_{user_id}"
        for month in range(6):
            date = base_date + timedelta(days=month*30 + random.randint(1, 10))
            amt = random.randint(50000, 200000)
            balance += amt
            transactions.append({"date": date.strftime("%Y-%m-%d"), "amount": amt, "type": "CREDIT", "narration": "CASH DEPOSIT BRANCH", "balance": balance})
            balance -= random.randint(40000, 180000)
            transactions.append({"date": (date + timedelta(days=2)).strftime("%Y-%m-%d"), "amount": -random.randint(40000, 180000), "type": "DEBIT", "narration": "ATM CASH WITHDRAWAL", "balance": balance})

    elif archetype == 'kirana_bounce':
        base_profile["name"] = f"BadKirana_{user_id}"
        for month in range(6):
            date = base_date + timedelta(days=month*30 + random.randint(1, 5))
            amt = random.randint(20000, 60000)
            balance += amt
            transactions.append({"date": date.strftime("%Y-%m-%d"), "amount": amt, "type": "CREDIT", "narration": "UPI CUSTOMER PAYMENT", "balance": balance})
            balance -= random.randint(15000, 55000)
            transactions.append({"date": (date + timedelta(days=3)).strftime("%Y-%m-%d"), "amount": -random.randint(15000, 55000), "type": "DEBIT", "narration": "SUPPLIER PAYMENT", "balance": balance})
            if random.random() > 0.3:
                balance -= 500
                transactions.append({"date": (date + timedelta(days=4)).strftime("%Y-%m-%d"), "amount": -500, "type": "DEBIT", "narration": "CHEQUE BOUNCE CHG", "balance": balance})
            if random.random() > 0.5:
                balance -= random.randint(5000, 20000)
                transactions.append({"date": (date + timedelta(days=6)).strftime("%Y-%m-%d"), "amount": -random.randint(5000, 20000), "type": "DEBIT", "narration": "ATM CASH WITHDRAWAL", "balance": balance})

    elif archetype == 'gig_stress':
        base_profile["name"] = f"BadGig_{user_id}"
        base_profile["telecom_number_vintage_days"] = random.randint(60, 300)
        for month in range(6):
            date = base_date + timedelta(days=month*30 + random.randint(1, 15))
            for _ in range(random.randint(3, 8)):
                amt = random.randint(500, 3000)
                balance += amt
                transactions.append({"date": date.strftime("%Y-%m-%d"), "amount": amt, "type": "CREDIT", "narration": "UPI GIGS PAYMENT", "balance": balance})
                date += timedelta(days=2)
            balance -= random.randint(10000, 30000)
            transactions.append({"date": date.strftime("%Y-%m-%d"), "amount": -random.randint(10000, 30000), "type": "DEBIT", "narration": "ATM CASH WITHDRAWAL", "balance": balance})
            if random.random() > 0.4:
                balance -= 500
                transactions.append({"date": (date + timedelta(days=1)).strftime("%Y-%m-%d"), "amount": -500, "type": "DEBIT", "narration": "CHEQUE BOUNCE CHG", "balance": balance})

    gst_turnover = sum(t['amount'] for t in transactions if t['type'] == 'CREDIT')
    return {
        "id": user_id, "true_label": 1, "archetype": archetype,
        "profile": {
            "user_profile": base_profile,
            "transactions": transactions,
            "gst_data": {"available": random.random() < 0.2, "declared_turnover": gst_turnover * random.uniform(1.5, 3.0)}
        }
    }


# ================== FEATURE ENGINE (label-blind) ==================


def compute_features(transactions, profile, gst_data):
    df = pd.DataFrame(transactions)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    credits = df[df['type'] == 'CREDIT']['amount']
    debits = df[df['type'] == 'DEBIT']['amount'].abs()

    features = {}

    # === I. PROXY PILLARS ===
    utility_tx = df[df['narration'].str.contains('ELECTRICITY|WATER|BROADBAND|BILL', case=False, na=False)]
    features['utility_payment_consistency'] = len(utility_tx)
    features['avg_utility_dpd'] = max(0.0, 30.0 - len(utility_tx) * 5.0)  # deterministic — matches feature_engine.py

    avg_income = credits.mean() if len(credits) > 0 else 1
    rent_payments = df[df['narration'].str.contains('RENT', case=False, na=False)]['amount'].abs()
    features['rent_wallet_share'] = (rent_payments.mean() / avg_income) if (len(rent_payments) > 0 and avg_income > 0) else 0.0

    sub_payments = df[df['narration'].str.contains('NETFLIX|SPOTIFY|SUBSCRIPTION|OTT|PRIME', case=False, na=False)]['amount'].abs()
    features['subscription_commitment_ratio'] = (sub_payments.sum() / (avg_income * 6)) if avg_income > 0 else 0.0

    # === II. LIQUIDITY & STRESS ===
    essential_out = df[df['narration'].str.contains('GROCERY|MEDICAL|ELECTRICITY|RENT|FUEL|PHARMACY|KIRANA', case=False, na=False)]['amount'].abs()
    lifestyle_out = df[df['narration'].str.contains('RESTAURANT|ZOMATO|SWIGGY|AMAZON|TRAVEL|HOTEL', case=False, na=False)]['amount'].abs()
    avg_essential = essential_out.mean() if len(essential_out) > 0 else 1
    features['emergency_buffer_months'] = (df['balance'].mean() / (avg_essential * 30)) if avg_essential > 0 else 0.5
    features['min_balance_violation_count'] = len(df[df['balance'] < 500])
    features['eod_balance_volatility'] = (df['balance'].std() / df['balance'].mean()) if df['balance'].mean() != 0 else 1.0
    features['essential_vs_lifestyle_ratio'] = (essential_out.sum() / lifestyle_out.sum()) if lifestyle_out.sum() > 0 else 3.0
    features['cash_withdrawal_dependency'] = (
        df[df['narration'].str.contains('ATM|CASH', case=False, na=False)]['amount'].abs().sum() / debits.sum()
    ) if debits.sum() > 0 else 0.0
    features['bounced_transaction_count'] = len(df[df['narration'].str.contains('BOUNCE|RETURN|CHG', case=False, na=False)])

    # === III. TELECOM & IDENTITY ===
    features['telecom_number_vintage_days'] = profile.get('telecom_number_vintage_days', 365)
    vintage = profile.get('telecom_number_vintage_days', 365)
    features['telecom_recharge_drop_ratio'] = max(0.4, 1.5 - (vintage / 3000))
    features['academic_background_tier'] = profile.get('academic_background_tier', 2)
    features['purpose_of_loan_encoded'] = profile.get('purpose_of_loan_encoded', 1)

    # === IV. MSME OPERATIONAL STABILITY ===
    features['business_vintage_months'] = profile.get('business_vintage_months', 24)

    df['month'] = df['date'].dt.to_period('M')
    monthly_in  = df[df['type'] == 'CREDIT'].groupby('month')['amount'].sum()
    monthly_out = df[df['type'] == 'DEBIT'].groupby('month')['amount'].sum().abs()
    monthly_net = monthly_in.subtract(monthly_out, fill_value=0)

    if len(monthly_in) >= 2:
        growth_vals = monthly_in.pct_change().dropna()
        features['revenue_growth_trend'] = float(growth_vals.mean())
        features['revenue_seasonality_index'] = float(monthly_in.std() / monthly_in.mean()) if monthly_in.mean() != 0 else 1.0
    else:
        features['revenue_growth_trend'] = 0.0
        features['revenue_seasonality_index'] = 0.5

    total_in  = monthly_in.sum()
    total_out = monthly_out.sum()
    features['operating_cashflow_ratio'] = (total_in / total_out) if total_out > 0 else 1.0
    features['cashflow_volatility'] = float(monthly_net.std()) if len(monthly_net) > 1 else 0.0
    n_credits = len(credits)
    features['avg_invoice_payment_delay'] = max(3.0, 15.0 - n_credits * 1.0) if n_credits >= 4 else (50.0 - n_credits * 10.0)  # deterministic

    # === V. NETWORK RISK & COMPLIANCE ===
    credit_df = df[df['type'] == 'CREDIT'].copy()
    if len(credit_df) > 0:
        top3 = credit_df.groupby('narration')['amount'].sum().nlargest(3).sum()
        features['customer_concentration_ratio'] = top3 / credit_df['amount'].sum() if credit_df['amount'].sum() > 0 else 1.0
        repeat = credit_df['narration'].value_counts()
        repeat_revenue = credit_df[credit_df['narration'].isin(repeat[repeat > 1].index)]['amount'].sum()
        features['repeat_customer_revenue_pct'] = repeat_revenue / credit_df['amount'].sum() if credit_df['amount'].sum() > 0 else 0.0
    else:
        features['customer_concentration_ratio'] = 1.0
        features['repeat_customer_revenue_pct'] = 0.0

    features['vendor_payment_discipline'] = 5.0 if features['bounced_transaction_count'] == 0 else (15.0 + features['bounced_transaction_count'] * 5.0)  # deterministic
    features['gst_filing_consistency_score'] = profile.get('gst_filing_consistency_score', 6)

    if gst_data.get('available') and gst_data.get('declared_turnover', 0) > 0:
        actual = credits.sum()
        features['gst_to_bank_variance'] = abs(actual - gst_data['declared_turnover']) / gst_data['declared_turnover']
    else:
        features['gst_to_bank_variance'] = 0.5

    # === VI. TRUST FLAGS ===
    def detect_circular_flow(df):
        credits_df = df[df['type'] == 'CREDIT'].copy()
        debits_df  = df[df['type'] == 'DEBIT'].copy()
        if len(credits_df) == 0 or len(debits_df) == 0:
            return 0
        loop_count = 0
        for _, cr in credits_df.iterrows():
            cr_root = cr['narration'].strip().split()[-1].upper()
            if len(cr_root) < 3:
                continue
            matching_debits = debits_df[
                (debits_df['narration'].str.upper().str.contains(cr_root, na=False)) &
                (abs((debits_df['date'] - cr['date']).dt.days) <= 3) &
                (debits_df['amount'].abs() >= cr['amount'] * 0.80)
            ]
            if len(matching_debits) > 0:
                loop_count += 1
        return int(loop_count >= 3)
        
    features['p2p_circular_loop_flag'] = detect_circular_flow(df)
    
    first_digits = [int(str(abs(int(a)))[0]) for a in df['amount'] if a != 0]
    benford_exp = np.log10(1 + 1 / np.arange(1, 10))
    benford_obs = np.array([first_digits.count(d) / len(first_digits) for d in range(1, 10)]) if len(first_digits) > 0 else np.zeros(9)
    features['benford_anomaly_score'] = float(np.sum(np.abs(benford_obs - benford_exp))) if len(first_digits) > 10 else 0.05
    features['round_number_spike_ratio'] = len(df[df['amount'].abs() % 1000 == 0]) / len(df) if len(df) > 0 else 0.0

    features['turnover_inflation_spike'] = int(features['round_number_spike_ratio'] > 0.6 and features['gst_to_bank_variance'] > 0.3)
    
    bounce_count = features.get('bounced_transaction_count', 0)
    mismatch_prob = 0.20 if bounce_count >= 3 else 0.03
    features['identity_device_mismatch'] = int(random.random() < mismatch_prob)

    NOISE_EXEMPT = {
        'p2p_circular_loop_flag', 'identity_device_mismatch',
        'turnover_inflation_spike', 'bounced_transaction_count',
        'min_balance_violation_count', 'utility_payment_consistency',
        'gst_filing_consistency_score', 'academic_background_tier',
        'purpose_of_loan_encoded', 'business_vintage_months',
        'telecom_number_vintage_days', 'employment_vintage_days'
    }
    for key in list(features.keys()):
        if key not in NOISE_EXEMPT and isinstance(features[key], float):
            if features[key] != 0.0:
                sigma = abs(features[key]) * 0.15
                features[key] = float(max(0.0, features[key] + random.gauss(0, sigma)))

    return features


# ================== MAIN ==================
random.seed(42)
n_good = 17000
n_bad  = 3000
users  = []

print("Generating 20,000 realistic users with diverse archetypes...")

for i in range(1, n_good + 1):
    good = generate_good_borrower(i)
    feats = compute_features(good['profile']['transactions'], good['profile']['user_profile'], good['profile']['gst_data'])
    feats['default_label'] = 0
    feats['archetype'] = good['archetype']
    users.append(feats)

for i in range(1, n_bad + 1):
    bad = generate_bad_borrower(i + n_good)
    feats = compute_features(bad['profile']['transactions'], bad['profile']['user_profile'], bad['profile']['gst_data'])
    feats['default_label'] = 1
    feats['archetype'] = bad['archetype']
    users.append(feats)

df = pd.DataFrame(users)
df.to_csv('pdr_training_data_realistic.csv', index=False)

print(f"[OK] Created pdr_training_data_realistic.csv")
print(f"Default rate: {df['default_label'].mean():.1%}")
print(f"Columns ({len(df.columns)}): {df.columns.tolist()}")
print("\nFeature means by class:")
print(df.groupby('default_label')[['utility_payment_consistency', 'bounced_transaction_count',
                                    'cash_withdrawal_dependency', 'p2p_circular_loop_flag']].mean().round(3))