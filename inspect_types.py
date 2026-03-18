import json

with open('test_batch.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

users = data.get('users', data) if isinstance(data, dict) else data

types = set()
for u in users:
    types.add(u.get('profile_type', str(u.get('true_label', 'unknown'))))

print("Unique profile types in test_batch.json:", types)
