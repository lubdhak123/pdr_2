"""Pipeline verification - runs all 5 demo users and asserts grades match."""

import json
import pathlib
import sys
from scorer import score_user

def run_verify():
    demo_path = pathlib.Path(__file__).parent / 'demo_users.json'
    try:
        data = json.loads(demo_path.read_text(encoding='utf-8'))
    except Exception as e:
        print(f"Error loading demo users: {e}")
        sys.exit(1)

    print("  --------------------------------------------------------------")
    print("  USER      PERSONA                EXPECTED  ACTUAL  SOURCE      PASS")
    print("  --------------------------------------------------------------")

    passes = 0
    total = len(data['demo_users'])
    results = []

    for user in data['demo_users']:
        user_id = user['user_id']
        persona = user['persona']
        expected_grade = user['expected_grade']
        
        try:
            result = score_user(user['transactions'], user['user_profile'], user['gst_data'])
        except Exception as e:
            print(f"Failed scoring {user_id}: {e}")
            sys.exit(1)
            
        actual_grade = result['grade']
        source = result['decision_source']
        is_pass = (actual_grade == expected_grade)
        
        if is_pass:
            passes += 1
        
        pass_str = "PASS" if is_pass else "FAIL"
        # Truncate persona to 22 chars
        p_str = (persona[:20] + '..') if len(persona) > 22 else persona.ljust(22)
        e_str = expected_grade.ljust(8)
        a_str = actual_grade.ljust(6)
        s_str = source.ljust(10)
        print(f"  {user_id}  {p_str}  {e_str}  {a_str}  {s_str}  {pass_str}")
        
        results.append((user_id, source, result))

    print("  --------------------------------------------------------------")
    print()
    
    for user_id, source, result in results:
        print(f"Reasons for {user_id}:")
        if source == 'pre_layer':
            print(f"  -> {result['primary_reason']}")
        else:
            shap_reasons = result.get('shap_reasons', [])
            for sr in shap_reasons[:3]:
                print(f"  -> {sr['reason']} ({sr['direction']}, {sr['impact']})")
        print()

    if passes == total:
        print(f"{passes}/{total} passed PASS")
        sys.exit(0)
    else:
        print(f"{passes}/{total} passed FAIL - fix pre_layer.py")
        sys.exit(1)

if __name__ == '__main__':
    run_verify()
