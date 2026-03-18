import json
import os
import joblib
import pandas as pd
from manual_score import engineer_features, FEATURE_COLS

def analyze_batch(batch_file="test_batch.json"):
    print("=================================================================")
    print("  BLIND BATCH EVALUATION - PDR MANUAL MODEL ACCURACY TEST")
    print("=================================================================\n")

    # Load test batch
    with open(batch_file, "r") as f:
        users = json.load(f)

    # Load Model
    model_path = os.path.join(os.path.dirname(__file__), "..", "pdr_model.pkl")
    model = joblib.load(model_path)

    total = len(users)
    correct = 0
    false_positives = 0  # Good user flagged as bad
    false_negatives = 0  # Bad user missed
    
    predictions = []

    print("Running hidden users through model pipeline...\n")
    print(f"{'User ID':<10} | {'True status':<15} | {'Model Pred':<15} | {'Match?'}")
    print("-" * 65)

    for u in users:
        uid = u["id"]
        true_label = u["true_label"] # 1=Default, 0=Good
        true_status_str = "Default" if true_label == 1 else "Good"
        
        # 1. Engineer exact 30 features (Model does NOT see true_label!)
        profile = u["profile"]
        features_dict = engineer_features(profile)
        input_df = pd.DataFrame([features_dict])[FEATURE_COLS]
        
        # 2. Predict Probability of Default
        pd_score = float(model.predict_proba(input_df)[0][1])
        
        # Determine prediction category
        # Using 0.22 as our boundary between "Acceptable" (A,B,C) and "High Risk" (D,E)
        pred_label = 1 if pd_score >= 0.22 else 0 
        pred_status_str = "Default (Risk D/E)" if pred_label == 1 else "Good (Risk A/B/C)"
        
        # Accuracy check
        is_match = (true_label == pred_label)
        match_str = "[+] YES" if is_match else "[-] NO"
        
        if is_match:
            correct += 1
        elif true_label == 0 and pred_label == 1:
            false_positives += 1
        elif true_label == 1 and pred_label == 0:
            false_negatives += 1

        if total <= 10 or uid % 10 == 0:  # Print sample logs
            print(f"{uid:<10} | {true_status_str:<15} | {pred_status_str:<15} | {match_str}")

    accuracy = (correct / total) * 100
    
    print("\n=================================================================")
    print("  FINAL ACCURACY REPORT")
    print("=================================================================")
    print(f"Total Users Tested    : {total}")
    print(f"Correct Predictions   : {correct}")
    print(f"Accuracy              : {accuracy:.2f}%\n")
    print(f"False Positives       : {false_positives} (Good users wrongly flagged)")
    print(f"False Negatives       : {false_negatives} (Defaulters missed by model)")
    print("=================================================================")

if __name__ == "__main__":
    analyze_batch()
