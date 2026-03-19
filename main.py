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

app = FastAPI(title='PDR Credit Scoring API', version='1.0.0')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*']
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

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)
