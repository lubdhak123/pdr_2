import os
import json
import uuid
import random
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Strict deterministic constraints
random.seed(42)
rng = np.random.default_rng(42)

logger = logging.getLogger("synthetic_generator")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

PROFILES = {
    "good_salaried_ntc": {
        "monthly_income": 45000.0,
        "income_type": "salary",
        "loan_amount": 100000.0,
        "months_of_history": 6,
        "expected_features": {
            "utility_payment_consistency": 1.0, 
            "bounced_transaction_count": 0,
            "emergency_buffer_months": 2.25,
            "cash_withdrawal_dependency": 0.05
        },
        "desc": "Stable salaried employee with clean utility and zero bounces."
    },
    "stressed_gig_ntc": {
        "monthly_income": 22000.0,
        "income_type": "gig",
        "loan_amount": 50000.0,
        "months_of_history": 6,
        "expected_features": {
            "utility_payment_consistency": 0.6, 
            "bounced_transaction_count": 2,
            "emergency_buffer_months": 0.8,
            "cash_withdrawal_dependency": 0.3
        },
        "desc": "Gig worker with erratic income, occasional missed utility, low buffer."
    },
    "high_risk_ntc": {
        "monthly_income": 15000.0,
        "income_type": "irregular",
        "loan_amount": 75000.0,
        "months_of_history": 6,
        "expected_features": {
            "utility_payment_consistency": 0.3, 
            "bounced_transaction_count": 6,
            "emergency_buffer_months": 0.1,
            "cash_withdrawal_dependency": 0.8
        },
        "desc": "Highly irregular cashflow, frequent NSF bounces, massive cash dependency."
    },
    "good_msme_owner": {
        "monthly_income": 120000.0,
        "income_type": "business",
        "loan_amount": 300000.0,
        "months_of_history": 6,
        "expected_features": {
            "utility_payment_consistency": 1.0, 
            "bounced_transaction_count": 0,
            "emergency_buffer_months": 4.0,
            "cash_withdrawal_dependency": 0.1
        },
        "desc": "Solid MSME proprietor with high corporate inflows and stable operations."
    }
}

UTILITY_BANDS = ["BESCOM ELECTRICITY", "JIO PREPAID", "INDANE GAS", "TNEB WATER"]
LIFESTYLE_BANDS = ["SWIGGY", "ZOMATO", "AMAZON PAY", "FLIPKART", "NETFLIX", "STARBUCKS"]

def get_base_probability(profile_name):
    if "good" in profile_name: return {"bounce": 0.0, "miss_utility": 0.0, "cash": 0.05}
    if "stressed" in profile_name: return {"bounce": 0.1, "miss_utility": 0.4, "cash": 0.3}
    return {"bounce": 0.3, "miss_utility": 0.7, "cash": 0.8}

def generate_statement(profile_name: str, user_id: str, months: int) -> dict:
    profile = PROFILES[profile_name]
    probs = get_base_probability(profile_name)
    
    start_date = datetime.now() - timedelta(days=30*months)
    transactions = []
    
    # Starting logical balance
    running_balance = rng.uniform(5000, 20000) if "good" in profile_name else rng.uniform(100, 1500)
    
    for month_idx in range(months):
        base_date = start_date + timedelta(days=30*month_idx)
        
        # 1. Income Generation
        if profile["income_type"] == "salary":
            amt = profile["monthly_income"] + rng.uniform(-1000, 1000)
            running_balance += amt
            transactions.append({
                "date": f"{base_date.year:04d}-{base_date.month:02d}-01",
                "type": "CR",
                "amount": round(amt, 2),
                "description": "NEFT-SALARY-WIPRO LTD",
                "category": "INCOME",
                "balance": round(running_balance, 2),
                "txn_id": str(uuid.uuid4())
            })
        elif profile["income_type"] == "gig":
            for _ in range(3): # Spread gig payments
                amt = profile["monthly_income"]/3 + rng.uniform(-2000, 2000)
                d = base_date + timedelta(days=int(rng.integers(1, 28)))
                running_balance += amt
                transactions.append({
                    "date": d.strftime("%Y-%m-%d"),
                    "type": "CR",
                    "amount": round(amt, 2),
                    "description": "UPI/ZOMATO/PAYOUT",
                    "category": "INCOME",
                    "balance": round(running_balance, 2),
                    "txn_id": str(uuid.uuid4())
                })
        else: # irregular / business
            count = 5 if profile["income_type"] == "business" else 2
            for _ in range(count):
                amt = (profile["monthly_income"]/count) + rng.uniform(-5000, 10000)
                d = base_date + timedelta(days=int(rng.integers(1, 28)))
                running_balance += amt
                transactions.append({
                    "date": d.strftime("%Y-%m-%d"),
                    "type": "CR",
                    "amount": round(amt, 2),
                    "description": "IMPS/B2B/VENDOR",
                    "category": "INCOME",
                    "balance": round(running_balance, 2),
                    "txn_id": str(uuid.uuid4())
                })
                
        # 2. Add structural predictable utility outflows
        if rng.random() >= probs["miss_utility"]:
            amt = rng.uniform(600, 2500)
            running_balance -= amt
            util_date = base_date + timedelta(days=10)
            transactions.append({
                "date": util_date.strftime("%Y-%m-%d"),
                "type": "DR",
                "amount": round(amt, 2),
                "description": f"UPI/BILLPAY/{rng.choice(UTILITY_BANDS)}",
                "category": "UTILITY",
                "balance": round(running_balance, 2),
                "txn_id": str(uuid.uuid4())
            })
            
        # 3. Rent & EMI (simulated based on wallet share logic)
        rent_amt = profile["monthly_income"] * 0.25 # standard mapping proxy
        running_balance -= rent_amt
        transactions.append({
            "date": (base_date + timedelta(days=5)).strftime("%Y-%m-%d"),
            "type": "DR",
            "amount": round(rent_amt, 2),
            "description": "UPI/RENT/LANDLORD",
            "category": "RENT",
            "balance": round(running_balance, 2),
            "txn_id": str(uuid.uuid4())
        })
        
        # 4. Cash withdrawals
        if rng.random() < probs["cash"]:
            amt = profile["monthly_income"] * probs["cash"] * 0.5
            running_balance -= amt
            transactions.append({
                "date": (base_date + timedelta(days=12)).strftime("%Y-%m-%d"),
                "type": "DR",
                "amount": round(amt, 2),
                "description": "ATM CASH WITHDRAWAL/SBI",
                "category": "CASH_WITHDRAWAL",
                "balance": round(running_balance, 2),
                "txn_id": str(uuid.uuid4())
            })
            
        # 5. Lifestyle overhead
        for _ in range(2):
            amt = rng.uniform(200, 1500)
            running_balance -= amt
            transactions.append({
                "date": (base_date + timedelta(days=int(rng.integers(1, 28)))).strftime("%Y-%m-%d"),
                "type": "DR",
                "amount": round(amt, 2),
                "description": f"UPI/{rng.choice(LIFESTYLE_BANDS)}",
                "category": "LIFESTYLE",
                "balance": round(running_balance, 2),
                "txn_id": str(uuid.uuid4())
            })
            
        # 6. Bounces / NSF fees
        if "bounce" in profile_name and rng.random() < probs["bounce"]:
            for _ in range(profile.get("expected_features", {}).get("bounced_transaction_count", 1) // months + 1):
                transactions.append({
                    "date": (base_date + timedelta(days=int(rng.integers(15, 25)))).strftime("%Y-%m-%d"),
                    "type": "DR",
                    "amount": 590.00,
                    "description": "CHQ RETURN/INSUFFICIENT FUNDS/NSF",
                    "category": "BOUNCE",
                    "balance": round(running_balance, 2),
                    "txn_id": str(uuid.uuid4())
                })
    
    # Sort by date
    transactions.sort(key=lambda x: x["date"])
    
    total_cr = sum(t["amount"] for t in transactions if t["type"] == "CR")
    total_dr = sum(t["amount"] for t in transactions if t["type"] == "DR")
    
    return {
        "user_id": user_id,
        "account_number": f"{rng.integers(1000000000, 9999999999)}",
        "bank": "HDFC BANK" if "good" in profile_name else "SBI",
        "ifsc": "HDFC0000123" if "good" in profile_name else "SBIN0000123",
        "currency": "INR",
        "statement_start": transactions[0]["date"],
        "statement_end": transactions[-1]["date"],
        "total_credits": round(total_cr, 2),
        "total_debits": round(total_dr, 2),
        "transaction_count": len(transactions),
        "transactions": transactions,
        "_test_expected_features": profile.get("expected_features", {}),
        "_profile_description": profile.get("desc", "")
    }

def generate_all_demo_profiles(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    results = {}
    
    logger.info(f"Generating synthetic statement JSONs into {output_dir}")
    for p_name in PROFILES.keys():
        uid = f"USR_{p_name.upper()}_{rng.integers(100, 999)}"
        doc = generate_statement(p_name, uid, 6)
        
        path = os.path.join(output_dir, f"{p_name}_statement.json")
        with open(path, "w") as f:
            json.dump(doc, f, indent=4)
        
        results[p_name] = doc
        logger.info(f" ✓ Saved {p_name} ({len(doc['transactions'])} txns) -> {path}")
        
    return results

def run_feature_engine_test(statements: dict, feature_engine_fn) -> pd.DataFrame:
    """
    Validates that the external core system (feature_engine.py) extracts features 
    correctly from our demo statements using a 15% tolerance window.
    """
    logger.info("\nSimulation verification logic initialized. Assuming feature_engine_fn takes JSON statement.")
    # Implementation placeholder for user's own CI/CD verification script logic
    pass

if __name__ == "__main__":
    statements = generate_all_demo_profiles("demo_data")
    print("\nGeneration Complete. Synthetic data primed for React Frontend.")
