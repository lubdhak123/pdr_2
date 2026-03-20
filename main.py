"""FastAPI application for PDR scoring pipeline.
Endpoints: POST /score, GET /health, GET /demo/{user_id}
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import json
import datetime
import pathlib
from scorer import score_user, model

class ScoreRequest(BaseModel):
    user_profile: dict
    transactions: list
    gst_data: dict

class AAScoreRequest(BaseModel):
    user_id: str
    consent_id: str | None = None

app = FastAPI(title='PDR Credit Scoring API', version='1.0.0')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*']
)

def load_demo_users() -> list:
    """Load all demo users from demo_users.json."""
    path = pathlib.Path(__file__).parent / 'demo_users.json'
    try:
        return json.loads(path.read_text(encoding='utf-8'))['demo_users']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read demo_users.json: {e}")

def find_user(user_id: str) -> dict | None:
    """Find a single user by user_id. Returns None if not found."""
    return next(
        (u for u in load_demo_users() if u['user_id'] == user_id),
        None
    )

@app.post('/score')
def score_endpoint(req: ScoreRequest):
    try:
        result = score_user(req.transactions, req.user_profile, req.gst_data)
        print(f"[SCORE] {req.user_profile.get('name','unknown')} -> {result['grade']}")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/health')
def health_endpoint():
    return {
        'status': 'ok',
        'model_loaded': model is not None,
        'timestamp': datetime.datetime.now().isoformat()
    }

@app.get('/demo/{user_id}')
def demo_endpoint(user_id: str):
    demo_path = pathlib.Path(__file__).parent / 'demo_users.json'
    try:
        data = json.loads(demo_path.read_text(encoding='utf-8'))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading demo users: {e}")
        
    user = next((u for u in data['demo_users'] if u['user_id'] == user_id), None)
    if not user:
        raise HTTPException(404, f'{user_id} not found')
        
    result = score_user(user['transactions'], user['user_profile'], user['gst_data'])
    result['persona'] = user['persona']
    result['expected_grade'] = user['expected_grade']
    result['user_id'] = user_id
    
    print(f"[DEMO] {user_id} ({user['persona']}) -> {result['grade']} expected {user['expected_grade']}")
    return result

# ═══════════════════════════════════════════════════
# SIMULATED ACCOUNT AGGREGATOR (AA) LAYER
# Mimics the RBI Account Aggregator framework.
# In production, replace this with a real Sahamati FIP.
# FIP ID: PDR-DEMO-FIP
# ═══════════════════════════════════════════════════

@app.get('/aa/health')
def aa_health_endpoint():
    """AA server health check."""
    return {
      "aa_status": "operational",
      "fip_id": "PDR-DEMO-FIP",
      "fip_name": "PDR Demo Financial Information Provider",
      "aa_version": "1.0",
      "users_available": len(load_demo_users()),
      "endpoints": [
        "GET  /aa/users",
        "POST /aa/users/{user_id}/consent",
        "GET  /aa/users/{user_id}/profile",
        "GET  /aa/users/{user_id}/statements",
        "POST /aa/score"
      ],
      "timestamp": datetime.datetime.now().isoformat()
    }

@app.get('/aa/users')
def aa_users_endpoint():
    """Returns the list of all available users for consent discovery."""
    users = load_demo_users()
    summaries = []
    for u in users:
        profile = u.get('user_profile', {})
        b_type = profile.get('business_type', '')
        persona_type = "NTC" if b_type == "Individual / NTC" else "MSME"
        summaries.append({
            "user_id": u.get("user_id"),
            "name": profile.get("name", "Unknown"),
            "persona": u.get("persona", "Unknown"),
            "city": profile.get("city", "Unknown"),
            "business_type": b_type,
            "persona_type": persona_type
        })
    print(f"[AA] /aa/users — returned {len(summaries)} user summaries")
    return {
        "aa_version": "1.0",
        "fip_id": "PDR-DEMO-FIP",
        "users": summaries,
        "total": len(summaries)
    }

@app.post('/aa/users/{user_id}/consent')
def aa_consent_endpoint(user_id: str, body: dict = None):
    """Simulates the consent grant step."""
    user = find_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found in FIP")
    
    timestamp = int(datetime.datetime.now().timestamp())
    consent_id = f"CONSENT-{user_id}-{timestamp}"
    granted_at = datetime.datetime.now()
    expires_at = granted_at + datetime.timedelta(hours=24)
    print(f"[AA] Consent granted for {user_id}")
    return {
        "consent_id": consent_id,
        "user_id": user_id,
        "status": "GRANTED",
        "granted_at": granted_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "data_access": ["TRANSACTIONS", "PROFILE", "GST"],
        "fip_id": "PDR-DEMO-FIP",
        "message": "Consent granted. Financial data access authorised for 24 hours."
    }

@app.get('/aa/users/{user_id}/profile')
def aa_profile_endpoint(user_id: str):
    """Returns identity and profile data for the user."""
    user = find_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found in FIP")
    
    print(f"[AA] Profile data fetched for {user_id}")
    profile = user.get("user_profile", {})
    return {
        "aa_version": "1.0",
        "user_id": user_id,
        "fip_id": "PDR-DEMO-FIP",
        "data_type": "PROFILE",
        "profile": {
            "name": profile.get("name"),
            "city": profile.get("city"),
            "business_type": profile.get("business_type"),
            "business_vintage_months": profile.get("business_vintage_months"),
            "academic_background_tier": profile.get("academic_background_tier"),
            "purpose_of_loan_encoded": profile.get("purpose_of_loan_encoded"),
            "telecom_number_vintage_days": profile.get("telecom_number_vintage_days"),
            "gst_filing_consistency_score": profile.get("gst_filing_consistency_score")
        },
        "gst_data": user.get("gst_data", {}),
        "fetched_at": datetime.datetime.now().isoformat()
    }

@app.get('/aa/users/{user_id}/statements')
def aa_statements_endpoint(user_id: str):
    """Returns the transaction history for the user."""
    user = find_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found in FIP")
    
    transactions = user.get("transactions", [])
    if not transactions:
        total_tx = 0
        date_from = None
        date_to = None
        total_credits = 0.0
        total_debits = 0.0
        closing_balance = 0.0
    else:
        total_tx = len(transactions)
        date_from = min(t['date'] for t in transactions if 'date' in t)
        date_to = max(t['date'] for t in transactions if 'date' in t)
        total_credits = round(sum(float(t['amount']) for t in transactions if t.get('type') == 'CREDIT'), 2)
        total_debits = round(sum(abs(float(t['amount'])) for t in transactions if t.get('type') == 'DEBIT'), 2)
        sorted_tx = sorted(transactions, key=lambda x: x.get('date', ''))
        closing_balance = round(float(sorted_tx[-1].get('balance', 0)), 2)

    print(f"[AA] Statement data fetched for {user_id} — {len(transactions)} transactions")
    
    return {
        "aa_version": "1.0",
        "user_id": user_id,
        "fip_id": "PDR-DEMO-FIP",
        "data_type": "BANK_STATEMENTS",
        "account_summary": {
            "total_transactions": total_tx,
            "date_range_from": date_from,
            "date_range_to": date_to,
            "total_credits": total_credits,
            "total_debits": total_debits,
            "closing_balance": closing_balance
        },
        "transactions": transactions,
        "fetched_at": datetime.datetime.now().isoformat()
    }

@app.post('/aa/score')
def aa_score_endpoint(req: AAScoreRequest):
    """This is the full AA-integrated scoring flow in one call."""
    user = find_user(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {req.user_id} not found in FIP")
    
    transactions = user.get("transactions", [])
    user_profile = user.get("user_profile", {})
    gst_data = user.get("gst_data", {})
    
    result = score_user(transactions, user_profile, gst_data)
    
    consent_id = req.consent_id if req.consent_id else "DEMO-NO-CONSENT"
    grade = result.get('grade')
    
    if not transactions:
        total_tx = 0
        date_from = None
        date_to = None
        total_credits = 0.0
        total_debits = 0.0
        closing_balance = 0.0
    else:
        total_tx = len(transactions)
        date_from = min(t['date'] for t in transactions if 'date' in t)
        date_to = max(t['date'] for t in transactions if 'date' in t)
        total_credits = round(sum(float(t['amount']) for t in transactions if t.get('type') == 'CREDIT'), 2)
        total_debits = round(sum(abs(float(t['amount'])) for t in transactions if t.get('type') == 'DEBIT'), 2)
        sorted_tx = sorted(transactions, key=lambda x: x.get('date', ''))
        closing_balance = round(float(sorted_tx[-1].get('balance', 0)), 2)
        
    print(f"[AA] Full AA score for {req.user_id} ({user_profile.get('name')}) -> {grade}")
    
    return {
        "aa_version": "1.0",
        "fip_id": "PDR-DEMO-FIP",
        "user_id": req.user_id,
        "persona": user.get("persona"),
        "consent_id": consent_id,
        "account_summary": {
            "total_transactions": total_tx,
            "date_range_from": date_from,
            "date_range_to": date_to,
            "total_credits": total_credits,
            "total_debits": total_debits,
            "closing_balance": closing_balance
        },
        "scoring_result": result,
        "scored_at": datetime.datetime.now().isoformat(),
        "message": f"PDR scoring complete for {user_profile.get('name')}. Grade: {grade}."
    }

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)
