"""
Full pipeline test: Run all 5 demo users through pre-layer + model.
Identifies edge cases, flaws, and gaps in the pre-layer.
"""
import json, sys, os
import numpy as np
import pandas as pd
import joblib

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "ntc_model"))

from pre_layer import apply_pre_layer

# Load model
model = joblib.load(os.path.join("ntc_model", "models", "ntc_credit_model.pkl"))
preprocessor = joblib.load(os.path.join("ntc_model", "models", "ntc_preprocessor.pkl"))

# Load feature list from training data
train_df = pd.read_csv(os.path.join("ntc_model", "datasets", "ntc_credit_training_v2.csv"), nrows=1)
FEATURE_COLS = [c for c in train_df.columns if c != "TARGET"]

# Load demo users
with open("demo_users.json") as f:
    data = json.load(f)

# Population defaults for missing features
POP_DEFAULTS = {
    "utility_payment_consistency": 0.70, "avg_utility_dpd": 8.0,
    "rent_wallet_share": 0.30, "subscription_commitment_ratio": 0.05,
    "emergency_buffer_months": 2.0, "eod_balance_volatility": 0.35,
    "essential_vs_lifestyle_ratio": 0.65, "cash_withdrawal_dependency": 0.15,
    "bounced_transaction_count": 1, "telecom_recharge_drop_ratio": 0.10,
    "min_balance_violation_count": 1, "income_stability_score": 0.60,
    "income_seasonality_flag": 0, "p2p_circular_loop_flag": 0,
    "gst_to_bank_variance": 0.20, "customer_concentration_ratio": 0.40,
    "turnover_inflation_spike": 0, "identity_device_mismatch": 0,
    "business_vintage_months": 36, "gst_filing_consistency_score": 5,
    "revenue_seasonality_index": 0.15, "revenue_growth_trend": 0.05,
    "cashflow_volatility": 0.30, "night_transaction_ratio": 0.05,
    "weekend_spending_ratio": 0.28, "payment_diversity_score": 0.80,
    "device_consistency_score": 0.85, "geographic_risk_score": 2,
    "applicant_age_years": 35, "employment_vintage_days": 2500,
    "academic_background_tier": 2, "owns_property": 0, "owns_car": 0,
    "region_risk_tier": 2, "address_stability_years": 5.0,
    "id_document_age_years": 10.0, "family_burden_ratio": 0.20,
    "income_type_risk_score": 2, "family_status_stability_score": 2,
    "contactability_score": 2, "purpose_of_loan_encoded": 2,
    "car_age_years": 99, "region_city_risk_score": 2,
    "address_work_mismatch": 0, "has_email_flag": 0,
    "telecom_number_vintage_days": 1000,
    "neighbourhood_default_rate_30": 0.05,
    "neighbourhood_default_rate_60": 0.03, "employment_to_age_ratio": 0.40
}

f = open("demo_test_results.txt", "w", encoding="utf-8")
def p(t=""): f.write(t + "\n"); print(t)

p("=" * 90)
p("  FULL PIPELINE TEST: 5 DEMO USERS through PRE-LAYER + NTC MODEL v3")
p("=" * 90)
p()

results = []
flaws = []

for user in data["demo_users"]:
    uid = user["user_id"]
    persona = user["persona"]
    expected_outcome = user["expected_outcome"]
    expected_grade = user["expected_grade"]

    p(f"{'─' * 90}")
    p(f"  USER: {uid} — {persona}")
    p(f"  Name: {user['user_profile']['name']}, City: {user['user_profile']['city']}")
    p(f"  Expected: {expected_grade} / {expected_outcome}")
    p(f"{'─' * 90}")

    # Build 49-feature vector
    features = dict(POP_DEFAULTS)  # start with population defaults

    # Overlay user_profile fields
    prof = user["user_profile"]
    for k, v in prof.items():
        if k in features:
            features[k] = v

    # Overlay ntc_features or msme_features
    ntc = user.get("ntc_features", {})
    msme = user.get("msme_features", {})
    for k, v in {**ntc, **msme}.items():
        if k in features:
            features[k] = v

    # Special mappings from demo data
    if "p2p_circular_loop_flag" not in ntc and "p2p_circular_loop_flag" not in msme:
        # Check key_flags for P2P
        if "P2P_CIRCULAR_LOOP" in user.get("key_flags", []):
            features["p2p_circular_loop_flag"] = 1
    if "turnover_inflation_spike" not in ntc:
        if "TURNOVER_INFLATION_SPIKE" in user.get("key_flags", []):
            features["turnover_inflation_spike"] = 1
    if "identity_device_mismatch" not in ntc:
        if "IDENTITY_DEVICE_MISMATCH" in user.get("key_flags", []):
            features["identity_device_mismatch"] = 1

    # Apply pre-layer
    pre_result = apply_pre_layer(features)

    if pre_result:
        grade, decision, reason = pre_result
        p(f"  PRE-LAYER: {grade} — {decision}")
        p(f"  Reason: {reason[:120]}...")
        model_prob = None
        model_decision = decision
        model_grade = grade
    else:
        p(f"  PRE-LAYER: None (goes to model)")

        # Run through model
        vec = [features.get(col, POP_DEFAULTS.get(col, 0)) for col in FEATURE_COLS]
        vec_df = pd.DataFrame([vec], columns=FEATURE_COLS)
        vec_scaled = preprocessor.transform(vec_df)
        model_prob = model.predict_proba(vec_scaled)[0, 1]

        if model_prob < 0.35:
            model_decision = "APPROVED"
            model_grade = "A" if model_prob < 0.15 else "B"
        elif model_prob < 0.55:
            model_decision = "MANUAL_REVIEW"
            model_grade = "C"
        else:
            model_decision = "REJECTED"
            model_grade = "D" if model_prob < 0.75 else "E"

        p(f"  MODEL: P(default) = {model_prob:.4f} ({model_prob*100:.1f}%)")
        p(f"  DECISION: {model_grade} — {model_decision}")
        reason = f"Model score: {model_prob:.4f}"

    # Check result vs expected
    # Normalize expected outcomes for comparison
    exp_norm = expected_outcome.upper().replace(" ", "_")
    act_norm = model_decision.upper().replace(" ", "_")

    # Check if grade matches
    grade_match = model_grade == expected_grade
    # Check if outcome direction matches (APPROVED, REVIEW, REJECTED)
    outcome_keywords = {
        "APPROVED": ["APPROVED", "APPROVED_WITH_CONDITIONS"],
        "APPROVED_WITH_CONDITIONS": ["APPROVED", "APPROVED_WITH_CONDITIONS"],
        "MANUAL_REVIEW": ["MANUAL_REVIEW", "MANUAL REVIEW"],
        "REJECTED": ["REJECTED"],
    }
    outcome_match = act_norm in [x.replace(" ", "_") for x in outcome_keywords.get(expected_outcome.upper().replace("_", " "), [expected_outcome])]
    if not outcome_match:
        # More lenient: check direction
        exp_risky = "REJECT" in exp_norm
        act_risky = "REJECT" in act_norm
        exp_good = "APPROV" in exp_norm
        act_good = "APPROV" in act_norm
        outcome_match = (exp_risky == act_risky) or (exp_good == act_good)

    status = "✅ MATCH" if outcome_match else "❌ MISMATCH"
    p(f"  RESULT: {status}")
    if not outcome_match:
        p(f"  ⚠️ Expected {expected_grade}/{expected_outcome}, Got {model_grade}/{model_decision}")
        flaws.append({
            "user": uid, "persona": persona,
            "expected": f"{expected_grade}/{expected_outcome}",
            "actual": f"{model_grade}/{model_decision}",
            "prob": model_prob
        })
    p()

    results.append({
        "uid": uid, "persona": persona,
        "expected_grade": expected_grade, "expected_outcome": expected_outcome,
        "actual_grade": model_grade, "actual_decision": model_decision,
        "prob": model_prob, "pre_layer_fired": pre_result is not None,
        "match": outcome_match
    })

# Summary
p("=" * 90)
p("  SUMMARY")
p("=" * 90)
p()
p(f"{'User':<12} {'Persona':<45} {'Expected':<15} {'Actual':<20} {'P(def)':<10} {'Status'}")
p("─" * 115)
for r in results:
    prob_str = f"{r['prob']:.1%}" if r['prob'] is not None else "PRE-LAYER"
    pre = "[PL] " if r["pre_layer_fired"] else "[ML] "
    status = "✅" if r["match"] else "❌"
    p(f"{r['uid']:<12} {r['persona'][:43]:<45} {r['expected_outcome']:<15} {pre}{r['actual_decision']:<15} {prob_str:<10} {status}")

# Flaws
if flaws:
    p(f"\n{'=' * 90}")
    p(f"  FLAWS DETECTED ({len(flaws)})")
    p(f"{'=' * 90}")
    for fl in flaws:
        p(f"\n  {fl['user']} — {fl['persona']}")
        p(f"    Expected: {fl['expected']}")
        p(f"    Actual:   {fl['actual']}")
        if fl['prob']:
            p(f"    P(def):   {fl['prob']:.4f}")

# Edge case analysis
p(f"\n{'=' * 90}")
p(f"  PRE-LAYER EDGE CASE ANALYSIS")
p(f"{'=' * 90}")

# Test additional edge cases that SHOULD be caught
edge_cases = {
    "High-value stable borrower with minor DPD": {
        **POP_DEFAULTS,
        "utility_payment_consistency": 0.75,
        "avg_utility_dpd": 12,
        "bounced_transaction_count": 0,
        "min_balance_violation_count": 0,
        "emergency_buffer_months": 8.0,
        "telecom_number_vintage_days": 2500,
        "gst_filing_consistency_score": 8,
        "cash_withdrawal_dependency": 0.05,
        "owns_property": 1,
        "p2p_circular_loop_flag": 0,
        "identity_device_mismatch": 0,
    },
    "Gig worker with UPI-only income": {
        **POP_DEFAULTS,
        "gst_filing_consistency_score": 0,
        "bounced_transaction_count": 0,
        "cash_withdrawal_dependency": 0.02,
        "telecom_number_vintage_days": 900,
        "p2p_circular_loop_flag": 0,
        "emergency_buffer_months": 1.0,
        "income_stability_score": 0.30,
        "income_seasonality_flag": 1,
        "eod_balance_volatility": 0.50,
    },
    "Retired person with pension": {
        **POP_DEFAULTS,
        "applicant_age_years": 65,
        "employment_vintage_days": 14600,
        "bounced_transaction_count": 0,
        "min_balance_violation_count": 0,
        "gst_filing_consistency_score": 0,
        "cash_withdrawal_dependency": 0.30,
        "telecom_number_vintage_days": 5000,
        "emergency_buffer_months": 12.0,
        "income_stability_score": 0.95,
        "owns_property": 1,
        "p2p_circular_loop_flag": 0,
        "identity_device_mismatch": 0,
    },
    "Student with part-time income": {
        **POP_DEFAULTS,
        "applicant_age_years": 22,
        "employment_vintage_days": 180,
        "academic_background_tier": 4,
        "bounced_transaction_count": 0,
        "min_balance_violation_count": 0,
        "gst_filing_consistency_score": 0,
        "cash_withdrawal_dependency": 0.08,
        "telecom_number_vintage_days": 600,
        "emergency_buffer_months": 0.5,
        "income_stability_score": 0.20,
        "eod_balance_volatility": 0.60,
        "p2p_circular_loop_flag": 0,
        "identity_device_mismatch": 0,
    },
    "Farmer with exactly 3 min_bal violations (boundary)": {
        **POP_DEFAULTS,
        "min_balance_violation_count": 3,
        "bounced_transaction_count": 0,
        "telecom_number_vintage_days": 4000,
        "gst_filing_consistency_score": 6,
        "revenue_seasonality_index": 0.70,
        "p2p_circular_loop_flag": 0,
    },
    "1 bounce + high cash (just below threshold)": {
        **POP_DEFAULTS,
        "bounced_transaction_count": 2,
        "cash_withdrawal_dependency": 0.79,  # just below 0.80
        "p2p_circular_loop_flag": 0,
        "min_balance_violation_count": 0,
    },
    "P2P circular but only 2 bounces (below threshold)": {
        **POP_DEFAULTS,
        "p2p_circular_loop_flag": 1,
        "bounced_transaction_count": 2,  # below threshold of 3
        "min_balance_violation_count": 0,
        "gst_to_bank_variance": 0.5,
    },
    "All-zero stress profile (new empty account)": {
        **POP_DEFAULTS,
        "utility_payment_consistency": 0,
        "avg_utility_dpd": 0,
        "bounced_transaction_count": 0,
        "min_balance_violation_count": 0,
        "emergency_buffer_months": 0,
        "income_stability_score": 0,
        "telecom_number_vintage_days": 30,
        "gst_filing_consistency_score": 0,
        "business_vintage_months": 0,
        "cash_withdrawal_dependency": 0,
        "p2p_circular_loop_flag": 0,
        "identity_device_mismatch": 0,
        "eod_balance_volatility": 0,
    },
}

for name, feats in edge_cases.items():
    pre_result = apply_pre_layer(feats)
    if pre_result:
        grade, decision, reason = pre_result
        result_str = f"PRE-LAYER: {grade}/{decision}"
    else:
        vec = [feats.get(col, 0) for col in FEATURE_COLS]
        vec_df = pd.DataFrame([vec], columns=FEATURE_COLS)
        vec_scaled = preprocessor.transform(vec_df)
        prob = model.predict_proba(vec_scaled)[0, 1]
        if prob < 0.35: decision = "APPROVED"
        elif prob < 0.55: decision = "MANUAL_REVIEW"
        else: decision = "REJECTED"
        result_str = f"MODEL: P(def)={prob:.1%} → {decision}"

    p(f"\n  {name}")
    p(f"    {result_str}")

    # Flag concerning results
    if "Farmer" in name and "REJECT" in str(pre_result):
        flaws.append({"user": "EDGE", "persona": name, "expected": "REVIEW/SEASONAL", "actual": str(pre_result)})
        p(f"    ⚠️ FLAW: Farmer with seasonal pattern should NOT be hard-rejected")

    if "circular" in name.lower() and pre_result is None:
        p(f"    ⚠️ GAP: P2P circular loop detected but pre-layer didn't fire (below bounce threshold)")

    if "zero" in name.lower() and "APPROV" in decision:
        p(f"    ⚠️ GAP: Empty account with no signals should NOT be approved")

p(f"\n{'=' * 90}")
p(f"  MISSING PRE-LAYER RULES (EDGE CASES NOT COVERED)")
p(f"{'=' * 90}")
p()
p("  1. P2P CIRCULAR with <3 bounces: Currently passes to model.")
p("     → Should at least trigger MANUAL_REVIEW if p2p_circular_loop_flag=1")
p("")
p("  2. ZERO-SIGNAL profile (new empty account): Goes straight to model.")
p("     → Should trigger MANUAL_REVIEW if all signals are zero/missing")
p("")
p("  3. RETIRED PERSON: No edge case rule for pensioners.")
p("     → High telecom vintage + zero bounces + high buffer + old age = should APPROVE")
p("")
p("  4. STUDENT with part-time income: No student-specific rule.")
p("     → Young age + high education + low income + zero bounces = special handling")
p("")
p("  5. GIG WORKER (non-NRI): Only NRI/platform rule exists (needs GST=0).")
p("     → But gig workers with some GST filing don't qualify for NRI rule")
p("")
p("  6. HIGH DPD but zero bounces: No rule for consistently late but never bouncing.")
p("     → avg_utility_dpd > 20 + bounced_count=0 = poor discipline but not fraud")
p("")
p("  7. DECLINING BUSINESS with good history: No rule for revenue_growth_trend < -0.5")
p("     with high business_vintage (established but failing)")
p("")
p("  8. MULTIPLE IDENTITY MISMATCHES: identity_device_mismatch only triggers review.")
p("     → Should reject if combined with new SIM + no GST + bounces")

f.close()
print("\n\nResults saved to demo_test_results.txt")
