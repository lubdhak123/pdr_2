"""Pre-layer rule engine for PDR.
Three rule types in strict priority order:
  Type 1 - Hard rejection: unambiguous fraud or extreme stress
  Type 2 - Edge case protection: legitimate non-standard profiles
  Type 3 - Manual review: ambiguous signals for human judgment
Returns None if no rule fires - send to ML model.
"""

def apply_pre_layer(features: dict) -> tuple | None:
    # TYPE 1: HARD REJECTION
    if features.get('p2p_circular_loop_flag', 0) == 1 and features.get('bounced_transaction_count', 0) >= 3:
        return ('E', 'REJECTED', 'Circular fund flow detected with repeated bounce charges - funds cycling between same counterparties with payment failures')

    if features.get('gst_to_bank_variance', 0) > 1.5:
        return ('E', 'REJECTED', 'Declared GST turnover does not match actual bank credits - possible inflation of turnover to appear eligible for larger loan')

    if features.get('bounced_transaction_count', 0) >= 5:
        return ('E', 'REJECTED', 'Excessive payment failures - five or more bounce charges indicate chronic inability to meet obligations')

    if features.get('min_balance_violation_count', 0) >= 3:
        return ('E', 'REJECTED', 'Account balance critically depleted three or more times - severe and recurring liquidity failure')

    if features.get('cash_withdrawal_dependency', 0) > 0.80 and features.get('bounced_transaction_count', 0) >= 3:
        return ('E', 'REJECTED', 'Extreme off-book cash dependency combined with payment failures - high probability of undisclosed financial obligations')

    # TYPE 2: EDGE CASE PROTECTION

    # Clean established business — strong multi-signal trust across utility, telecom, GST, and banking
    if (features.get('bounced_transaction_count', 0) == 0 and
        features.get('p2p_circular_loop_flag', 0) == 0 and
        features.get('identity_device_mismatch', 0) == 0 and
        features.get('min_balance_violation_count', 0) == 0 and
        features.get('telecom_number_vintage_days', 0) > 1000 and
        features.get('gst_filing_consistency_score', 0) >= 6 and
        features.get('utility_payment_consistency', 0) >= 6 and
        features.get('cash_withdrawal_dependency', 0) < 0.15):
        return ('A', 'APPROVED', 'Established business with strong multi-signal trust - zero payment failures, long identity vintage, consistent GST filing, high utility discipline, and minimal cash dependency confirm exceptional creditworthiness')
    if (features.get('bounced_transaction_count', 0) == 0 and 
        features.get('telecom_number_vintage_days', 0) > 1000 and 
        features.get('p2p_circular_loop_flag', 0) == 0 and 
        features.get('gst_to_bank_variance', 0) < 0.8 and 
        features.get('min_balance_violation_count', 0) == 0 and
        features.get('gst_filing_consistency_score', 0) > 0 and
        features.get('gst_to_bank_variance', 0) > 0):
        return ('B', 'APPROVED WITH CONDITIONS', 'Stable non-standard income pattern - zero payment failures and long identity vintage confirm financial discipline despite irregular income timing consistent with seasonal or agricultural income')

    if (features.get('gst_filing_consistency_score', 0) == 0 and 
        features.get('bounced_transaction_count', 0) == 0 and 
        features.get('cash_withdrawal_dependency', 0) < 0.2 and 
        features.get('telecom_number_vintage_days', 0) > 500 and 
        features.get('p2p_circular_loop_flag', 0) == 0):
        return ('B', 'APPROVED WITH CONDITIONS', 'Alternative income source verified - remittance or platform income with zero payment failures and fully digital spending confirms financial stability')

    if (features.get('business_vintage_months', 0) <= 12 and 
        features.get('bounced_transaction_count', 0) == 0 and 
        features.get('telecom_number_vintage_days', 0) > 1500 and 
        features.get('gst_filing_consistency_score', 0) <= 2 and 
        features.get('emergency_buffer_months', 0) > 2.0):
        return ('B', 'APPROVED WITH CONDITIONS', 'Stable pension or fixed income profile - consistent low-volatility credits with strong savings buffer and zero payment failures confirm reliable repayment capacity')

    # TYPE 3: MANUAL REVIEW
    if (features.get('customer_concentration_ratio', 0) > 0.85 and
        (features.get('telecom_number_vintage_days', 0) < 500 or
         features.get('gst_to_bank_variance', 0) > 0.3 or
         features.get('bounced_transaction_count', 0) > 0)):
        return ('C', 'MANUAL REVIEW', 'Revenue concentrated in fewer than three customers with additional risk signals - single client dependency requires verification')

    if features.get('turnover_inflation_spike', 0) == 1:
        return ('C', 'MANUAL REVIEW', 'Possible turnover inflation - round number transactions with GST variance requires verification')

    if features.get('identity_device_mismatch', 0) == 1:
        return ('C', 'MANUAL REVIEW', 'Identity verification signals inconsistent - manual document check required')

    return None

if __name__ == '__main__':
    test_1 = {'p2p_circular_loop_flag': 1, 'bounced_transaction_count': 3,
              'gst_to_bank_variance': 0.5, 'min_balance_violation_count': 0,
              'cash_withdrawal_dependency': 0.3, 'telecom_number_vintage_days': 95,
              'gst_filing_consistency_score': 2, 'customer_concentration_ratio': 0.5,
              'turnover_inflation_spike': 0, 'identity_device_mismatch': 0,
              'business_vintage_months': 8, 'emergency_buffer_months': 0.5}
    assert apply_pre_layer(test_1) is not None and apply_pre_layer(test_1)[0] == 'E', "FAIL: Farouk should be E"
    print("[OK] Rule 1 fires - Farouk -> E")

    test_2 = {'p2p_circular_loop_flag': 0, 'bounced_transaction_count': 0,
              'telecom_number_vintage_days': 3200, 'gst_to_bank_variance': 0.1,
              'min_balance_violation_count': 0, 'gst_filing_consistency_score': 4,
              'cash_withdrawal_dependency': 0.05, 'business_vintage_months': 72,
              'emergency_buffer_months': 3.0, 'customer_concentration_ratio': 0.6,
              'turnover_inflation_spike': 0, 'identity_device_mismatch': 0}
    assert apply_pre_layer(test_2) is not None and apply_pre_layer(test_2)[0] == 'B', "FAIL: Sukhwinder should be B"
    print("[OK] Rule 6 fires - Sukhwinder -> B")

    test_3 = {'p2p_circular_loop_flag': 0, 'bounced_transaction_count': 0,
              'gst_filing_consistency_score': 0, 'cash_withdrawal_dependency': 0.05,
              'telecom_number_vintage_days': 1800, 'min_balance_violation_count': 0,
              'gst_to_bank_variance': 0.5, 'business_vintage_months': 0,
              'emergency_buffer_months': 5.0, 'customer_concentration_ratio': 0.7,
              'turnover_inflation_spike': 0, 'identity_device_mismatch': 0}
    assert apply_pre_layer(test_3) is not None and apply_pre_layer(test_3)[0] == 'B', "FAIL: Arjun should be B"
    print("[OK] Rule 7 fires - Arjun -> B")

    test_4 = {'p2p_circular_loop_flag': 0, 'bounced_transaction_count': 1,
              'gst_to_bank_variance': 0.2, 'min_balance_violation_count': 1,
              'cash_withdrawal_dependency': 0.3, 'telecom_number_vintage_days': 600,
              'gst_filing_consistency_score': 5, 'customer_concentration_ratio': 0.5,
              'turnover_inflation_spike': 0, 'identity_device_mismatch': 0,
              'business_vintage_months': 24, 'emergency_buffer_months': 1.5}
    assert apply_pre_layer(test_4) is None, "FAIL: ambiguous should be None"
    print("[OK] No rule fires - ambiguous -> None (goes to model)")
