import json
import os
import joblib
import pandas as pd
from manual_score import engineer_features, FEATURE_COLS

def get_true_label(profile_type):
    """Fallback mapping for LLM-generated profile types to binary truth"""
    profile_type = str(profile_type).lower()
    
    # Obvious Fraud / Defaulter / High Risk
    bad_keywords = ['wash', 'bounce', 'struggling', 'ghost', 'inflator', 'stacking', 'hoarder']
    for kw in bad_keywords:
        if kw in profile_type:
            return 1
            
    # Obvious Good Borrowers
    good_keywords = ['clean', 'doctor', 'retired', 'export', 'nri']
    for kw in good_keywords:
        if kw in profile_type:
            return 0
            
    # Ambiguous ones (gig workers, freelancers, etc.) 
    # For testing, we'll mark them as 1 (expecting them to be High Risk) 
    # unless they are clearly stable.
    return 1 if 'inconsistent' in profile_type or 'lumpy' in profile_type else 0

def analyze_batch(batch_file="test_batch.json"):
    print("=================================================================")
    print("  BLIND BATCH EVALUATION - LLM GENERATED EDGE CASES")
    print("=================================================================\n")

    # Load test batch
    with open(batch_file, "r") as f:
        data = json.load(f)

    # Handle both old array format AND new object format
    if isinstance(data, dict) and "users" in data:
        users = data["users"]
    else:
        users = data

    # Load Model
    model_path = os.path.join(os.path.dirname(__file__), "..", "pdr_model_realistic.pkl")
    model = joblib.load(model_path)

    total = len(users)
    correct = 0
    false_positives = 0
    false_negatives = 0
    
    print("Running generated edge cases through XGBoost pipeline...\n")
    print(f"{'User/Type':<25} | {'True status':<15} | {'Model Pred':<15} | {'Match?'}")
    print("-" * 65)

    for i, u in enumerate(users):
        # Extract ID and handle new format
        uid = u.get("user_id", u.get("id", f"USER_{i}"))
        profile_type = u.get("profile_type", "synthetic_test")
        
        # Determine Ground Truth
        if "true_label" in u:
            true_label = u["true_label"]
        else:
            true_label = get_true_label(profile_type)
            
        true_status_str = "Default/Risk" if true_label == 1 else "Good"

        # Construct flat profile mapping handling old & new schemas
        profile_payload = u["profile"] if "profile" in u else u
        
        # 1. Feature Engineering
        features_dict = engineer_features(profile_payload)
        input_df = pd.DataFrame([features_dict])[FEATURE_COLS]
        
        # 2. Predict Probability of Default
        pd_score = float(model.predict_proba(input_df)[0][1])
        
        # 3. Categorize Risk (>= 0.22 = D/E High Risk)
        pred_label = 1 if pd_score >= 0.22 else 0 
        pred_status_str = "Default/Risk" if pred_label == 1 else "Good"
        
        # Accuracy check
        is_match = (true_label == pred_label)
        match_str = "[+] YES" if is_match else "[-] NO"
        
        if is_match:
            correct += 1
        elif true_label == 0 and pred_label == 1:
            false_positives += 1
        elif true_label == 1 and pred_label == 0:
            false_negatives += 1

        # Truncate profile_type string to fit display
        display_id = profile_type[:23] if profile_type != "synthetic_test" else str(uid)
        
        # Print a sample of logs (print more frequently for these fun LLM types!)
        if total <= 20 or i % max(1, total // 15) == 0 or not is_match:
            print(f"{display_id:<25} | {true_status_str:<15} | {pred_status_str:<15} | {match_str}")

    accuracy = (correct / total) * 100
    
    print("\n=================================================================")
    print("  FINAL ACCURACY REPORT ON LLM EDGE CASES")
    print("=================================================================")
    print(f"Total Users Tested    : {total}")
    print(f"Accuracy              : {accuracy:.2f}%\n")
    print(f"False Positives       : {false_positives} (Good users wrongly flagged)")
    print(f"False Negatives       : {false_negatives} (Risky users completely missed)")
    print("=================================================================")

if __name__ == "__main__":
    # If run from root, point exactly to where standard file resides
    target = "test_batch.json" if os.path.exists("test_batch.json") else "../test_batch.json"
    analyze_batch(target)
