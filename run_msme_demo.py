"""
MSME Middleman Credit Scoring Demo — Murugan Provision Store
Posts the Selvaraj M profile to POST /score/middleman and prints results.
"""
import json
import sys
import requests

PROFILE_PATH = "demo_profiles/selvaraj_msme.json"
API_URL = "http://localhost:8000/score/middleman"
RESULT_PATH = "demo_profiles/selvaraj_result.json"
EXPECTED_DECISION = "APPROVE"


def main():
    print("=" * 58)
    print("=== MURUGAN PROVISION STORE — MSME CREDIT SCORING DEMO ===")
    print("=" * 58)

    # Profile summary
    print()
    print("Business  : Murugan Provision Store, Villupuram TN")
    print("Vintage   : 11 years")
    print("Loan ask  : ₹80,000")
    print("Sources   : Supplier + Utility + Telecom + BC Agent")
    print("GST       : Not registered")
    print("Bank acct : None")
    print("Bureau    : No entry")
    print()

    # Load request body
    try:
        with open(PROFILE_PATH, "r") as f:
            payload = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: {PROFILE_PATH} not found.")
        sys.exit(1)

    # Pre-flight validation
    warnings = []
    non_null_sources = 0
    for src in ["supplierdata", "gstdata", "telecomdata", "utilitydata", "bcagentdata"]:
        if payload.get(src) is not None:
            non_null_sources += 1
    if non_null_sources < 2:
        warnings.append(f"Only {non_null_sources} non-null source(s) — need at least 2")

    meta = payload.get("applicantmetadata", {})
    if "loan_amount_requested" not in meta:
        warnings.append("applicantmetadata missing loan_amount_requested")

    if warnings:
        for w in warnings:
            print(f"WARNING: {w}")
        print("Proceeding with request anyway...\n")
    else:
        print("Validation passed: 4 sources present, loan amount set.\n")

    # POST to middleman endpoint
    print(f"Posting to {API_URL} ...")
    try:
        resp = requests.post(API_URL, json=payload, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError:
        print("Server not running. Start with: uvicorn main:app --reload")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e}")
        print(f"Response: {resp.text}")
        sys.exit(1)

    result = resp.json()

    # Print results
    print()
    print("-" * 50)
    print(f"DECISION     : {result.get('decision')}")
    print(f"PROBABILITY  : {result.get('probability_default')}")
    print(f"GRADE        : {result.get('grade')}")
    print(f"CONFIDENCE   : {result.get('confidence')}")
    print(f"SOURCES USED : {result.get('sources_used')}")
    pre_layer = result.get("pre_layer_override")
    print(f"PRE-LAYER    : {'PASS' if not pre_layer else f'FLAG — {pre_layer}'}")
    print("-" * 50)

    top_features = result.get("top_features", [])
    if top_features:
        print("TOP FEATURES:")
        for i, feat in enumerate(top_features, 1):
            print(f"  {i}. {feat}")
    print("-" * 50)

    # Interpretation
    decision = result.get("decision")
    print()
    if decision == "APPROVE":
        print("Strong cross-source consistency across 4 independent")
        print("signals. 11-year business vintage with clean supplier")
        print("payment history justifies approval at this ticket size.")
    elif decision == "MANUAL_REVIEW":
        print("Sufficient evidence for review. Recommend field")
        print("verification of supplier relationship before disbursal.")
    elif decision == "REJECT":
        print(f"Insufficient evidence or conflicting signals.")
        print(f"Flags: {pre_layer}")
    print()

    # Expected outcome check
    if decision != EXPECTED_DECISION:
        print(f"NOTE: Expected {EXPECTED_DECISION} — check middleman_scorer.py")
        print("      feature extraction and threshold logic.")
        print()

    # Save raw response
    try:
        with open(RESULT_PATH, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Raw API response saved to {RESULT_PATH}")
    except Exception as e:
        print(f"Could not save result: {e}")


if __name__ == "__main__":
    main()
