"""
chatbot_context.py — PDR Chatbot Context Fetcher + Prompt Builder
=================================================================
Steps 3 & 4 of the AI Credit Analyst Chatbot pipeline.

Step 3 — Fetch:
  fetch_applicant_context(db_path, applicant_id) → dict
    Retrieves a frozen, LLM-ready applicant card from SQLite.

Step 4 — Build:
  build_prompt(routed_query, db_path) → (system_prompt, user_prompt)
    Assembles the full prompt pair for any of the 7 query types.

Query types handled:
  LOOKUP | EXPLANATION | COMPARISON | SCENARIO |
  DECISION_LETTER | RISK_ASSESSMENT | AGGREGATE

Usage:
    from chatbot_router import route_query
    from chatbot_context import build_prompt

    routed = route_query("Why was msme_003 rejected?")
    system_p, user_p = build_prompt(routed, db_path="applicant_cards.db")
    # → pass both to Ollama / Claude
"""

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from chatbot_router import QueryType, RoutedQuery
from context_layer import fetch_applicant_card, search_applicants, get_grade_distribution

# ─────────────────────────────────────────────────────────────────────────────
# FEATURE NAME → PLAIN ENGLISH MAP
# ─────────────────────────────────────────────────────────────────────────────

FEATURE_LABELS: dict[str, str] = {
    "utility_payment_consistency":      "On-time utility bill payment rate",
    "avg_utility_dpd":                  "Average days late on utility bills",
    "rent_wallet_share":                "Rent/EMI share of income",
    "subscription_commitment_ratio":    "Fixed subscription share of income",
    "emergency_buffer_months":          "Financial safety buffer (months of expenses saved)",
    "eod_balance_volatility":           "Daily account balance stability",
    "essential_vs_lifestyle_ratio":     "Essentials vs lifestyle spending ratio",
    "cash_withdrawal_dependency":       "Reliance on cash withdrawals",
    "bounced_transaction_count":        "Number of bounced/failed transactions",
    "telecom_recharge_drop_ratio":      "Recent mobile recharge decline ratio",
    "min_balance_violation_count":      "Months below minimum balance (₹1,000)",
    "income_stability_score":           "Income regularity score",
    "income_seasonality_flag":          "Seasonal income pattern detected",
    "telecom_number_vintage_days":      "SIM card age (days)",
    "academic_background_tier":         "Education level (1=low, 4=postgrad)",
    "purpose_of_loan_encoded":          "Loan purpose category",
    "employment_vintage_days":          "Days in current employment",
    "applicant_age_years":              "Applicant age (years)",
    "owns_property":                    "Property ownership",
    "owns_car":                         "Vehicle ownership",
    "region_risk_tier":                 "Geographic risk tier (1=low, 3=high)",
    "address_stability_years":          "Years at current address",
    "id_document_age_years":            "Years since ID was issued",
    "family_burden_ratio":              "Financial dependants burden ratio",
    "has_email_flag":                   "Has registered email address",
    "income_type_risk_score":           "Employment type risk (1=salaried, 5=unemployed)",
    "family_status_stability_score":    "Marital/family stability score",
    "contactability_score":             "Reachability score (phone + email)",
    "car_age_years":                    "Vehicle age (years)",
    "region_city_risk_score":           "City-level risk score",
    "address_work_mismatch":            "Lives far from workplace",
    "employment_to_age_ratio":          "Employment years relative to working age",
    "neighbourhood_default_rate_30":    "30-day cluster default rate (local area)",
    "neighbourhood_default_rate_60":    "60-day cluster default rate (local area)",
    "p2p_circular_loop_flag":           "Circular money flow detected (A→B→A)",
    "gst_to_bank_variance":             "GST-declared vs actual bank credits gap",
    "customer_concentration_ratio":     "Revenue dependence on single customer",
    "turnover_inflation_spike":         "Unnatural revenue spike before application",
    "identity_device_mismatch":         "Multiple accounts from same device",
    "business_vintage_months":          "Months since business was established",
    "gst_filing_consistency_score":     "GST filing regularity (0–12 months)",
    "revenue_seasonality_index":        "Revenue concentration across months",
    "revenue_growth_trend":             "Recent income growth trend",
    "cashflow_volatility":              "Daily net cashflow variability",
}

_RISK_THRESHOLDS = {
    "utility_payment_consistency":   (">=", 0.80, "above 80% is healthy"),
    "avg_utility_dpd":               ("<=", 15,   "below 15 days is acceptable"),
    "emergency_buffer_months":       (">=", 2.0,  "2+ months buffer is recommended"),
    "eod_balance_volatility":        ("<=", 0.40, "below 0.40 is stable"),
    "bounced_transaction_count":     ("<=", 1,    "0–1 bounces is acceptable"),
    "cash_withdrawal_dependency":    ("<=", 0.50, "below 50% is preferred"),
    "income_stability_score":        (">=", 0.70, "above 0.70 is stable"),
    "gst_filing_consistency_score":  (">=", 8,    "8+ months of filing is healthy"),
    "min_balance_violation_count":   ("<=", 1,    "0–1 violations is acceptable"),
    "gst_to_bank_variance":          ("<=", 0.30, "below 30% variance is acceptable"),
}


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — CONTEXT FETCHER
# ─────────────────────────────────────────────────────────────────────────────

def fetch_applicant_context(db_path: str, applicant_id: str) -> dict | None:
    """
    Retrieve a frozen, LLM-ready applicant card from SQLite.

    Augments the raw DB record with:
    - Human-readable feature labels
    - Threshold context for top SHAP factors
    - Formatted loan offer string
    - Highlighted red flags

    Args:
        db_path:      Path to applicant_cards.db
        applicant_id: e.g. "ntc_001"

    Returns:
        Enriched dict ready for prompt injection, or None if not found.
    """
    card = fetch_applicant_card(db_path, applicant_id)
    if card is None:
        return None

    # ── Enrich SHAP factors with human-readable labels + threshold context ───
    enriched_shap = []
    for factor in card.get("top_shap_factors", []):
        feat = factor.get("feature", "")
        val  = factor.get("shap_value", 0.0)
        raw_feat_val = card.get("all_features", {}).get(feat)

        threshold_note = ""
        if feat in _RISK_THRESHOLDS:
            op, limit, note = _RISK_THRESHOLDS[feat]
            threshold_note = f"(threshold: {note})"

        enriched_shap.append({
            **factor,
            "label":          FEATURE_LABELS.get(feat, feat),
            "raw_value":      raw_feat_val,
            "threshold_note": threshold_note,
            "tag":            "⚠ RISK" if factor.get("direction") == "risk" else "✓ STRENGTH",
        })

    # ── Flag red flags from features ─────────────────────────────────────────
    all_features = card.get("all_features", {})
    red_flags: list[str] = []

    if all_features.get("bounced_transaction_count", 0) >= 3:
        red_flags.append(f"⚠ {int(all_features['bounced_transaction_count'])} bounced transactions")
    if all_features.get("p2p_circular_loop_flag", 0) == 1:
        red_flags.append("⚠ P2P circular money flow detected")
    if all_features.get("gst_to_bank_variance", 0) > 1.5:
        red_flags.append(f"⚠ GST vs bank variance: {all_features['gst_to_bank_variance']:.1%}")
    if all_features.get("cash_withdrawal_dependency", 0) > 0.80:
        red_flags.append(f"⚠ Very high cash dependency: {all_features['cash_withdrawal_dependency']:.0%}")
    if all_features.get("turnover_inflation_spike", 0) == 1:
        red_flags.append("⚠ Unusual revenue spike before application")
    if all_features.get("identity_device_mismatch", 0) == 1:
        red_flags.append("⚠ Multiple accounts from same device")

    # ── Format loan offer ────────────────────────────────────────────────────
    raw_offer = card.get("loan_offer", {})
    if raw_offer.get("eligible"):
        loan_offer_text = (
            f"Eligible — up to ₹{raw_offer.get('max_loan', 0):,.0f} "
            f"at {raw_offer.get('interest_rate', 'N/A')} "
            f"over {raw_offer.get('tenures', [])} months. "
            f"Recommended: {raw_offer.get('recommended_product', 'N/A')}"
        )
    else:
        loan_offer_text = "Not eligible for standard loan products."
        if card.get("alternative_products"):
            alts = "; ".join(
                f"{p.get('name', '?')} (up to ₹{p.get('max', 0):,.0f})"
                for p in card["alternative_products"][:3]
            )
            loan_offer_text += f" Alternative products: {alts}"

    # ── Format key features in plain English ─────────────────────────────────
    key_features_plain: dict[str, str] = {}
    priority_features = [
        "income_stability_score", "emergency_buffer_months", "bounced_transaction_count",
        "cash_withdrawal_dependency", "utility_payment_consistency", "avg_utility_dpd",
        "eod_balance_volatility", "gst_filing_consistency_score", "employment_vintage_days",
        "applicant_age_years", "business_vintage_months", "gst_to_bank_variance",
    ]
    for feat in priority_features:
        if feat in all_features:
            raw_val = all_features[feat]
            label   = FEATURE_LABELS.get(feat, feat)
            # Format value nicely
            if feat in ("income_stability_score", "utility_payment_consistency",
                        "cash_withdrawal_dependency", "eod_balance_volatility"):
                val_str = f"{raw_val:.0%}"
            elif feat in ("employment_vintage_days", "telecom_number_vintage_days"):
                val_str = f"{raw_val/365:.1f} years"
            elif feat == "gst_filing_consistency_score":
                val_str = f"{raw_val:.0f}/12 months"
            else:
                val_str = f"{raw_val}"
            key_features_plain[label] = val_str

    return {
        **card,
        "enriched_shap":       enriched_shap,
        "red_flags":           red_flags,
        "loan_offer_text":     loan_offer_text,
        "key_features_plain":  key_features_plain,
        "risk_band":           _infer_risk_band(card.get("default_probability", 1.0)),
        "fetched_at":          datetime.now(timezone.utc).isoformat(),
    }


def _infer_risk_band(pd: float) -> str:
    if pd < 0.20:  return "LOW"
    if pd < 0.45:  return "MEDIUM"
    return "HIGH"


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — PROMPT BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

# ── Shared system prompt header ───────────────────────────────────────────────

_SYSTEM_BASE = """You are a senior credit analyst at PDR Bank, using the PDR Alternative Credit Scoring System.
You are assisting a loan officer who is reviewing applicant files.

STRICT RULES — follow these at all times:
1. Only use data explicitly provided in the CONTEXT block below. Never invent numbers.
2. If the information needed is not available, say so clearly.
3. Be specific — cite actual values (e.g. "0.72 cash dependency" not "high cash usage").
4. Keep responses professional and concise (max 250 words, unless generating a formal letter).
5. Focus on what matters for a credit decision: risk drivers, protective factors, and actionable insights.
6. SHAP values indicate feature impact — positive means increases default risk, negative means reduces it.
7. Never reveal model internals (XGBoost, training data, feature engineering details).
"""

# ─────────────────────────────────────────────────────────────────────────────

def _format_card_block(ctx: dict, label: str = "APPLICANT") -> str:
    """Render one applicant card as a structured text block for LLM injection."""
    pd    = ctx.get("default_probability", 0.0)
    grade = ctx.get("grade", "?")
    dec   = ctx.get("decision", "UNKNOWN")

    shap_lines = []
    for s in ctx.get("enriched_shap", []):
        raw_val = f" | raw value: {s['raw_value']}" if s.get("raw_value") is not None else ""
        thresh  = f" {s['threshold_note']}" if s.get("threshold_note") else ""
        shap_lines.append(
            f"  {s['rank']}. {s['tag']} {s['label']}{raw_val} "
            f"[SHAP: {s.get('shap_value', 0):+.4f}]{thresh}"
        )

    kf_lines = [
        f"  • {label_}: {val_}"
        for label_, val_ in list(ctx.get("key_features_plain", {}).items())[:8]
    ]

    flags = ctx.get("red_flags", [])
    flags_block = "\n".join(f"  {f}" for f in flags) if flags else "  (none)"

    pre_layer = ctx.get("pre_layer_rule") or ctx.get("decision_source")
    rule_line = (
        f"  ⚡ Pre-layer rule override: {pre_layer}"
        if ctx.get("pre_layer_rule")
        else f"  Decision source: {pre_layer or 'model'}"
    )

    return f"""
━━━ {label} ━━━
Name          : {ctx.get('name', 'Unknown')}
ID            : {ctx.get('applicant_id', '?')}
City/Type     : {ctx.get('city', '?')} | {ctx.get('business_type', '?')}
Score Date    : {ctx.get('score_date', '?')}

DECISION
  Grade       : {grade}  |  Risk Band: {ctx.get('risk_band','?')}
  Decision    : {dec}
  Default Prob: {pd:.1%}
  Primary Reason: {ctx.get('primary_reason', '?')}
{rule_line}

TOP SHAP FACTORS (what drove this decision):
{"".join(f'{l}\n' for l in shap_lines) or "  (not available)"}
KEY FEATURES:
{"".join(f'{l}\n' for l in kf_lines) or "  (not available)"}
RED FLAGS:
{flags_block}

LOAN OFFER:
  {ctx.get('loan_offer_text', 'N/A')}
"""


# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATE 1: LOOKUP
# ─────────────────────────────────────────────────────────────────────────────

def _build_lookup_prompt(ctx: dict, raw_message: str) -> tuple[str, str]:
    system = _SYSTEM_BASE + (
        "\nYour task: Give a clear, plain-English 3–4 sentence summary of this applicant's "
        "credit profile. State the decision, the probability, the top 2 reasons, and the loan offer."
    )
    user = f"""CONTEXT:
{_format_card_block(ctx)}

LOAN OFFICER QUERY: {raw_message}

Summarise this applicant's credit profile for the loan officer."""
    return system, user


# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATE 2: EXPLANATION
# ─────────────────────────────────────────────────────────────────────────────

def _build_explanation_prompt(ctx: dict, raw_message: str, focus: str) -> tuple[str, str]:
    focus_instruction = {
        "rejection_reason":  "Explain clearly why this applicant was REJECTED. Cite the top 2–3 risk drivers with their actual values.",
        "approval_reason":   "Explain clearly why this applicant was APPROVED. Highlight the 2–3 strongest positive factors.",
        "risk_factors":      "Identify the 2–3 biggest risk factors for this applicant and explain what they mean in plain English.",
        "general":           "Explain the key factors that drove this credit decision, both positive and negative.",
    }.get(focus, "Explain the credit decision clearly.")

    system = _SYSTEM_BASE + f"\nYour task: {focus_instruction}"
    user = f"""CONTEXT:
{_format_card_block(ctx)}

LOAN OFFICER QUERY: {raw_message}

Explain the credit decision in 3–4 sentences. Use plain English. Cite actual values."""
    return system, user


# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATE 3: COMPARISON
# ─────────────────────────────────────────────────────────────────────────────

def _build_comparison_prompt(ctx_a: dict, ctx_b: dict, raw_message: str) -> tuple[str, str]:
    system = _SYSTEM_BASE + (
        "\nYour task: Compare the two applicants side-by-side. Highlight the most important "
        "differences in risk profile, key features, and decisions. Recommend which (if either) "
        "is preferable from a credit risk perspective. Keep it under 200 words."
    )
    user = f"""CONTEXT:
{_format_card_block(ctx_a, label='APPLICANT A')}
{_format_card_block(ctx_b, label='APPLICANT B')}

LOAN OFFICER QUERY: {raw_message}

Compare these two applicants. What are the key differences? Who is the better credit risk and why?"""
    return system, user


# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATE 4: SCENARIO
# ─────────────────────────────────────────────────────────────────────────────

def _build_scenario_prompt(ctx: dict, raw_message: str, params: dict) -> tuple[str, str]:
    target_feat = params.get("target_feature", "unknown feature")
    direction   = params.get("change_direction", "change")
    magnitude   = params.get("magnitude_pct")
    mag_str     = f"{magnitude:.0%}" if magnitude else "significantly"
    feat_label  = FEATURE_LABELS.get(target_feat, target_feat)

    # Current value of target feature
    raw_features = ctx.get("all_features", {})
    current_val  = raw_features.get(target_feat)
    current_str  = f"{current_val}" if current_val is not None else "unknown"

    # Determine new hypothetical value
    if current_val is not None and magnitude:
        factor = (1 + magnitude) if direction == "increase" else (1 - magnitude)
        new_val = current_val * factor
        change_line = (
            f"Hypothetical change: {feat_label} {direction}s from {current_str} "
            f"to {new_val:.4f} ({mag_str} {direction})"
        )
    else:
        change_line = f"Hypothetical change: {feat_label} {direction}s by {mag_str}"

    # Decision threshold reminder
    threshold_reminder = (
        "Decision thresholds: APPROVE if P(default) < 35% | "
        "MANUAL_REVIEW if 35–55% | REJECT if > 55%"
    )

    system = _SYSTEM_BASE + (
        f"\nYour task: Analyse how the proposed change would likely affect this applicant's "
        f"credit decision. Use the SHAP values to reason directionally — you do NOT have the "
        f"exact new model score, so reason from feature importance. State whether the change "
        f"is likely to shift the outcome, and what threshold would need to be crossed. "
        f"Be honest about uncertainty. {threshold_reminder}"
    )
    user = f"""CONTEXT:
{_format_card_block(ctx)}

SCENARIO:
  {change_line}

LOAN OFFICER QUERY: {raw_message}

Reason step-by-step: would this change materially improve the credit outcome? 
What else would need to change for a different decision?"""
    return system, user


# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATE 5: DECISION LETTER
# ─────────────────────────────────────────────────────────────────────────────

def _build_letter_prompt(ctx: dict, raw_message: str, letter_type: str) -> tuple[str, str]:
    # Resolve actual letter type from card if set to "auto"
    if letter_type == "auto":
        decision = ctx.get("decision", "UNKNOWN").upper()
        if "APPROVED" in decision:
            letter_type = "approval"
        elif "REJECT" in decision:
            letter_type = "rejection"
        else:
            letter_type = "review"

    today = datetime.now().strftime("%d %B %Y")
    ref   = f"PDR-{ctx.get('applicant_id','?').upper()}-{datetime.now().strftime('%Y%m%d')}"

    letter_heading = {
        "approval":  "CREDIT APPLICATION — APPROVED",
        "rejection": "CREDIT APPLICATION — DECLINED",
        "review":    "CREDIT APPLICATION — REFERRED FOR REVIEW",
    }.get(letter_type, "CREDIT DECISION")

    shap_reasons = "\n".join(
        f"  {i+1}. {s['label']}: {s.get('raw_value', 'N/A')} ({s['tag'].replace('⚠ ','').replace('✓ ','')})"
        for i, s in enumerate(ctx.get("enriched_shap", [])[:3])
    )

    system = _SYSTEM_BASE + f"""
Your task: Write a formal, professional credit decision letter on behalf of PDR Bank.

Letter format required:
  - Date: {today}
  - Reference: {ref}
  - Heading: {letter_heading}
  - Paragraph 1: Acknowledge the application and state the decision clearly.
  - Paragraph 2: Cite exactly 2–3 specific data-driven reasons for this decision 
    (use the values provided, in plain English — no technical jargon like "SHAP" or "XGBoost").
  - Paragraph 3: Next steps for the applicant (e.g. what to improve, who to contact, 
    alternative products if declined).
  - Close professionally. Sign off as "PDR Credit Assessment Team".

Keep the language professional but accessible. The applicant may not be financially literate.
Do NOT use the words "SHAP", "XGBoost", "model", "algorithm", or "feature" in the letter."""

    user = f"""APPLICANT DETAILS:
  Name           : {ctx.get('name', 'Applicant')}
  Application ID : {ref}
  Decision       : {ctx.get('decision', 'UNKNOWN')} (Grade {ctx.get('grade', '?')})
  Default Probability: {ctx.get('default_probability', 0):.1%}
  Primary Reason : {ctx.get('primary_reason', 'Risk assessment outcome')}

TOP DECISION FACTORS:
{shap_reasons or '  (not available)'}

RED FLAGS:
{chr(10).join('  ' + f for f in ctx.get('red_flags', [])) or '  (none)'}

LOAN OFFER:
  {ctx.get('loan_offer_text', 'N/A')}

LOAN OFFICER REQUEST: {raw_message}

Write the formal credit decision letter now."""
    return system, user


# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATE 6: RISK ASSESSMENT
# ─────────────────────────────────────────────────────────────────────────────

def _build_risk_assessment_prompt(ctx: dict, raw_message: str) -> tuple[str, str]:
    system = _SYSTEM_BASE + (
        "\nYour task: Identify the single biggest risk for this applicant. "
        "Explain in 2–3 sentences: what the risk is, how severe it is based on "
        "the actual value, and what it means in practice for the lender. "
        "Then briefly list 2 other notable risks. Finally, name one protective factor."
    )
    user = f"""CONTEXT:
{_format_card_block(ctx)}

LOAN OFFICER QUERY: {raw_message}

What is the primary credit risk for this applicant? Be specific and cite actual values."""
    return system, user


# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATE 7: AGGREGATE
# ─────────────────────────────────────────────────────────────────────────────

def _build_aggregate_prompt(
    db_path: str, raw_message: str, params: dict
) -> tuple[str, str]:
    """
    Runs aggregate SQL queries and injects portfolio-level data into the prompt.
    """
    # Gather grade distribution
    grade_dist = get_grade_distribution(db_path)

    # Gather filtered applicant list based on params
    filters: dict = {}
    if "grade" in params:
        filters["grade"] = params["grade"]
    if "decision" in params:
        filters["decision"] = params["decision"]
    if "risk_band" in params:
        # risk_band stored in score — approximate via score range
        rb = params["risk_band"]
        if rb == "HIGH":
            filters["score_min"] = 0.45
        elif rb == "MEDIUM":
            filters["score_min"] = 0.20
            filters["score_max"] = 0.45
        elif rb == "LOW":
            filters["score_max"] = 0.20

    matching = search_applicants(db_path, filters)

    # Limit rows shown to LLM
    limit = params.get("limit", 10)
    order = params.get("order", "top")   # top = highest risk first
    if order in ("top", "worst"):
        matching.sort(key=lambda x: x.get("default_probability", 0), reverse=True)
    elif order == "best":
        matching.sort(key=lambda x: x.get("default_probability", 0))

    shown = matching[:limit]
    rows_text = "\n".join(
        f"  {i+1}. {r['name']} ({r['applicant_id']}) — Grade {r['grade']}, "
        f"{r['decision']}, PD={r.get('default_probability',0):.1%}, "
        f"City: {r.get('city','?')}, Type: {r.get('business_type','?')}"
        for i, r in enumerate(shown)
    ) or "  (no matching applicants)"

    # Summary stats
    total = len(matching)
    if total > 0:
        avg_pd = sum(r.get("default_probability", 0) for r in matching) / total
        pd_str = f"{avg_pd:.1%}"
    else:
        pd_str = "N/A"

    system = _SYSTEM_BASE + (
        "\nYour task: Answer a portfolio-level question using the aggregate data provided. "
        "Give a clear, structured answer with numbers. Highlight any notable patterns. "
        "Keep it under 200 words."
    )
    user = f"""PORTFOLIO DATA:

Grade Distribution (all applicants):
{json.dumps(grade_dist, indent=2)}

Matching Applicants (filter: {filters or 'none'}):
  Total found: {total}
  Average default probability: {pd_str}
  
{rows_text}

LOAN OFFICER QUERY: {raw_message}

Answer this portfolio question using the data above. Be specific with numbers."""
    return system, user


# ─────────────────────────────────────────────────────────────────────────────
# MASTER PROMPT BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def build_prompt(
    routed: RoutedQuery,
    db_path: str,
) -> tuple[str, str]:
    """
    Build the (system_prompt, user_prompt) pair for Ollama/Claude based on
    the routed query type.

    Args:
        routed:  RoutedQuery from chatbot_router.route_query()
        db_path: Path to applicant_cards.db

    Returns:
        (system_prompt, user_prompt) — pass both to the LLM call.

    Raises:
        ValueError: If required applicant IDs are not found in the database.
    """
    qt  = routed.query_type
    ids = routed.applicant_ids
    msg = routed.raw_message
    prm = routed.parameters

    # ── AGGREGATE: no applicant context needed ────────────────────────────────
    if qt == QueryType.AGGREGATE:
        return _build_aggregate_prompt(db_path, msg, prm)

    # ── UNKNOWN ────────────────────────────────────────────────────────────────
    if qt == QueryType.UNKNOWN:
        hint = prm.get("hint", "")
        system = _SYSTEM_BASE
        user = (
            f"The loan officer said: {msg!r}\n\n"
            f"This query couldn't be classified. Politely ask them to rephrase "
            f"and give 2–3 example queries they could try.\n"
            f"Hint for suggestions: {hint}"
        )
        return system, user

    # ── All other types require at least one applicant ID ─────────────────────
    if not ids:
        system = _SYSTEM_BASE
        user = (
            f"The loan officer asked: {msg!r}\n\n"
            f"No applicant ID was found in the query. "
            f"Ask them to specify an applicant ID (e.g. 'ntc_001', 'msme_003')."
        )
        return system, user

    # ── Fetch primary applicant context ───────────────────────────────────────
    primary_id  = ids[0]
    primary_ctx = fetch_applicant_context(db_path, primary_id)

    if primary_ctx is None:
        system = _SYSTEM_BASE
        user = (
            f"The loan officer is looking for applicant '{primary_id}', but this ID "
            f"was not found in the database. Ask them to check the ID and confirm that "
            f"applicant cards have been built (run build_applicant_cards.py)."
        )
        return system, user

    # ── Route to specific template ─────────────────────────────────────────────
    if qt == QueryType.LOOKUP:
        return _build_lookup_prompt(primary_ctx, msg)

    elif qt == QueryType.EXPLANATION:
        focus = prm.get("focus", "general")
        return _build_explanation_prompt(primary_ctx, msg, focus)

    elif qt == QueryType.COMPARISON:
        if len(ids) < 2 or prm.get("comparison_incomplete"):
            # Graceful degradation to LOOKUP with a note
            sys_p, usr_p = _build_lookup_prompt(primary_ctx, msg)
            usr_p += "\n\nNote: Only one applicant ID was provided. Please specify a second ID to compare."
            return sys_p, usr_p
        secondary_id  = ids[1]
        secondary_ctx = fetch_applicant_context(db_path, secondary_id)
        if secondary_ctx is None:
            system = _SYSTEM_BASE
            user = (
                f"Applicant '{secondary_id}' (the second comparison target) was not found. "
                f"Tell the loan officer to check that ID."
            )
            return system, user
        return _build_comparison_prompt(primary_ctx, secondary_ctx, msg)

    elif qt == QueryType.SCENARIO:
        return _build_scenario_prompt(primary_ctx, msg, prm)

    elif qt == QueryType.DECISION_LETTER:
        letter_type = prm.get("letter_type", "auto")
        return _build_letter_prompt(primary_ctx, msg, letter_type)

    elif qt == QueryType.RISK_ASSESSMENT:
        return _build_risk_assessment_prompt(primary_ctx, msg)

    # Fallback
    return _build_lookup_prompt(primary_ctx, msg)


# ─────────────────────────────────────────────────────────────────────────────
# DEMO
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from chatbot_router import route_query
    from context_layer import init_database, save_applicant_card

    DB = "applicant_cards.db"
    init_database(DB)

    # Seed one demo card
    demo_result = {
        "grade": "E",
        "outcome": "REJECTED",
        "default_probability": 0.72,
        "decision_source": "model",
        "primary_reason": "High cash withdrawal dependency with bounced transactions",
        "pre_layer_decision": None,
        "shap_reasons": [
            {"feature": "cash_withdrawal_dependency", "reason": "Relies heavily on cash",
             "shap_value": 0.41, "direction": "risk", "impact": "High"},
            {"feature": "bounced_transaction_count",  "reason": "Multiple bounces",
             "shap_value": 0.32, "direction": "risk", "impact": "High"},
            {"feature": "income_stability_score",     "reason": "Irregular income",
             "shap_value": 0.19, "direction": "risk", "impact": "Medium"},
            {"feature": "utility_payment_consistency","reason": "Mostly pays on time",
             "shap_value": -0.09, "direction": "strength", "impact": "Low"},
            {"feature": "emergency_buffer_months",    "reason": "Some savings",
             "shap_value": -0.05, "direction": "strength", "impact": "Low"},
        ],
        "features": {
            "cash_withdrawal_dependency": 0.82,
            "bounced_transaction_count":  3,
            "income_stability_score":     0.41,
            "utility_payment_consistency": 0.78,
            "emergency_buffer_months":    1.1,
            "eod_balance_volatility":     0.68,
            "gst_filing_consistency_score": 3,
            "employment_vintage_days":    490,
            "applicant_age_years":        29,
            "p2p_circular_loop_flag":     0,
        },
        "loan_offer": {"eligible": False},
        "scored_at": "2026-03-28T10:00:00Z",
    }

    save_applicant_card(DB, demo_result, "msme_003",
                        name="Priya Singh", city="Mumbai", business_type="Kirana Owner")

    test_queries = [
        "Why was msme_003 rejected?",
        "Generate a rejection letter for msme_003",
        "What is the biggest risk for msme_003?",
        "What if msme_003 had 30% less cash withdrawals?",
    ]

    for q in test_queries:
        print(f"\n{'='*70}")
        print(f"QUERY: {q}")
        print(f"{'='*70}")
        routed = route_query(q)
        print(f"Routed: {routed}")
        system_p, user_p = build_prompt(routed, DB)
        print("\n--- SYSTEM PROMPT (first 300 chars) ---")
        print(system_p[:300] + "...")
        print("\n--- USER PROMPT (first 500 chars) ---")
        print(user_p[:500] + "...")
