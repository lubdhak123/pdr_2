import json
import random
from datetime import datetime, timedelta

def generate_good_borrower(user_id):
    """Generates a profile + transactions for a consistent, low-risk borrower (True Label = 0)"""
    profile = {
        "name": f"GoodUser_{user_id}",
        "phone": f"980000{user_id:04d}",
        "business_vintage_months": random.randint(36, 120),
        "academic_background_tier": random.choice([1, 2]),
        "purpose_of_loan_encoded": 1,
        "telecom_number_vintage_days": random.randint(1000, 3000),
        "gst_filing_consistency_score": random.randint(9, 12),
        "city": "Mumbai",
        "business_type": "IT Services"
    }

    transactions = []
    base_date = datetime(2023, 6, 1)
    balance = random.randint(100000, 200000)
    
    for month in range(6):
        # Salary / Client Payment (Consistent)
        date = base_date + timedelta(days=month*30 + random.randint(1, 5))
        amount = random.randint(80000, 120000)
        balance += amount
        transactions.append({
            "date": date.strftime("%Y-%m-%d"),
            "amount": amount,
            "type": "CREDIT",
            "narration": "NEFT FROM CLIENT INVOICE",
            "balance": balance
        })
        
        # Utility Payment (Consistent, No delay)
        date = date + timedelta(days=random.randint(2, 5))
        amount = -random.randint(1500, 3000)
        balance += amount
        transactions.append({
            "date": date.strftime("%Y-%m-%d"),
            "amount": amount,
            "type": "DEBIT",
            "narration": "ELECTRICITY BILL PAYMENT",
            "balance": balance
        })
        
        # Office Rent (Consistent)
        date = date + timedelta(days=1)
        amount = -random.randint(15000, 25000)
        balance += amount
        transactions.append({
            "date": date.strftime("%Y-%m-%d"),
            "amount": amount,
            "type": "DEBIT",
            "narration": "OFFICE RENT HDFC",
            "balance": balance
        })
        
        # Lifestyle spend
        date = date + timedelta(days=random.randint(5, 10))
        amount = -random.randint(5000, 15000)
        balance += amount
        transactions.append({
            "date": date.strftime("%Y-%m-%d"),
            "amount": amount,
            "type": "DEBIT",
            "narration": "RESTAURANT AMAZON ZOMATO",
            "balance": balance
        })

    return {"id": user_id, "true_label": 0, "profile": {"user_profile": profile, "transactions": transactions, "gst_data": {"available": True, "declared_turnover": 600000}}}

def generate_bad_borrower(user_id):
    """Generates a profile + transactions for a high-risk/fraud borrower (True Label = 1)"""
    profile = {
        "name": f"BadUser_{user_id}",
        "phone": f"990000{user_id:04d}",
        "business_vintage_months": random.randint(2, 10),
        "academic_background_tier": random.choice([3, 4]),
        "purpose_of_loan_encoded": 4,
        "telecom_number_vintage_days": random.randint(30, 150),
        "gst_filing_consistency_score": random.randint(0, 3),
        "city": "Delhi",
        "business_type": "Trading"
    }

    transactions = []
    base_date = datetime(2023, 6, 1)
    balance = random.randint(1000, 5000)
    
    for month in range(6):
        # Erratic credits
        date = base_date + timedelta(days=month*30 + random.randint(1, 15))
        amount = random.choice([50000, 100000, 200000]) # Round number spikes
        balance += amount
        transactions.append({
            "date": date.strftime("%Y-%m-%d"),
            "amount": amount,
            "type": "CREDIT",
            "narration": "UPI TRANSFER UNKNOWN ROUND",
            "balance": balance
        })
        
        # Immediate cash withdrawal
        date = date + timedelta(days=1)
        amount = -amount + random.randint(100, 500) # Withdraw almost everything
        balance += amount
        transactions.append({
            "date": date.strftime("%Y-%m-%d"),
            "amount": amount,
            "type": "DEBIT",
            "narration": "ATM CASH WITHDRAWAL",
            "balance": balance
        })
        
        # Bounced transaction
        if random.random() > 0.3:
            date = date + timedelta(days=random.randint(2, 5))
            amount = -500
            balance += amount
            transactions.append({
                "date": date.strftime("%Y-%m-%d"),
                "amount": amount,
                "type": "DEBIT",
                "narration": "CHEQUE BOUNCE CHG",
                "balance": balance
            })
            
        # Circular Loop Injection (Fraud Signal)
        if random.random() > 0.5:
            loop_date = date + timedelta(days=2)
            loop_amt = random.randint(20000, 50000)
            balance -= loop_amt
            transactions.append({
                "date": loop_date.strftime("%Y-%m-%d"),
                "amount": -loop_amt,
                "type": "DEBIT",
                "narration": "UPI TO SHYAM",
                "balance": balance
            })
            balance += loop_amt
            transactions.append({
                "date": (loop_date + timedelta(days=1)).strftime("%Y-%m-%d"),
                "amount": loop_amt,
                "type": "CREDIT",
                "narration": "UPI FROM SHYAM",
                "balance": balance
            })

    return {"id": user_id, "true_label": 1, "profile": {"user_profile": profile, "transactions": transactions, "gst_data": {"available": False, "declared_turnover": 0}}}


if __name__ == "__main__":
    random.seed(42)
    users = []
    
    # Generate 50 good and 50 bad users
    for i in range(1, 51):
        users.append(generate_good_borrower(i))
    for i in range(51, 101):
        users.append(generate_bad_borrower(i))
        
    # Shuffle so order is random
    random.shuffle(users)
    
    with open('test_batch.json', 'w') as f:
        json.dump(users, f, indent=2)
        
    print(f"Generated 100 manual test users (50 Good, 50 Default) into test_batch.json")
    print("True labels are hidden inside the JSON under 'true_label'.")
