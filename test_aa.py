import requests
import json

base = 'http://localhost:8000'

print('Testing AA routes...')

# Test AA health
r = requests.get(f'{base}/aa/health')
assert r.status_code == 200
assert r.json()['aa_status'] == 'operational'
print('[OK] GET /aa/health')

# Test user list
r = requests.get(f'{base}/aa/users')
assert r.status_code == 200
assert r.json()['total'] == 5
print('[OK] GET /aa/users — 5 users returned')

# Test consent
r = requests.post(f'{base}/aa/users/DEMO_001/consent')
assert r.status_code == 200
assert r.json()['status'] == 'GRANTED'
consent_id = r.json()['consent_id']
print(f'[OK] POST /aa/users/DEMO_001/consent — {consent_id}')

# Test profile
r = requests.get(f'{base}/aa/users/DEMO_001/profile')
assert r.status_code == 200
assert r.json()['data_type'] == 'PROFILE'
print('[OK] GET /aa/users/DEMO_001/profile')

# Test statements
r = requests.get(f'{base}/aa/users/DEMO_001/statements')
assert r.status_code == 200
assert r.json()['data_type'] == 'BANK_STATEMENTS'
print(f'[OK] GET /aa/users/DEMO_001/statements — {r.json()["account_summary"]["total_transactions"]} transactions')

# Test full AA score for all 5 users
expected = {
    'DEMO_001': 'A',
    'DEMO_002': 'E',
    'DEMO_003': 'B',
    'DEMO_004': 'D',
    'DEMO_005': 'B',
}
print()
print('Testing AA scoring for all 5 users...')
all_pass = True
for user_id, expected_grade in expected.items():
    r = requests.post(f'{base}/aa/score', json={'user_id': user_id})
    assert r.status_code == 200
    actual = r.json()['scoring_result']['grade']
    match = '✅' if actual == expected_grade else '❌'
    print(f'  {user_id} → expected {expected_grade} actual {actual} {match}')
    if actual != expected_grade:
        all_pass = False

print()
if all_pass:
    print('All AA routes verified. 5/5 users scoring correctly.')
else:
    print('Some users failed. Check pre_layer.py rules.')
