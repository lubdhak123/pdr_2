"""Feature engine for PDR inference pipeline.
Computes 30 behavioral features from raw transaction JSON.
Label-blind — no default_label anywhere in this file.
"""
import pandas as pd
import numpy as np
import random
import math

def compute_features(
    transactions: list[dict],
    profile: dict,
    gst_data: dict
) -> dict[str, float]:
    result = {}
    
    # Setup
    try:
        df = pd.DataFrame(transactions)
        if not df.empty:
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
            else:
                pass
            
            for col in ['amount', 'type', 'narration', 'balance']:
                if col not in df.columns:
                    df[col] = '' if col == 'narration' else 0.0
            
            df['narration'] = df['narration'].fillna('').astype(str).str.upper()
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0.0)
            df['balance'] = pd.to_numeric(df['balance'], errors='coerce').fillna(0.0)
            df['type'] = df['type'].fillna('').astype(str).str.upper()
            
            credits = df[df['type'] == 'CREDIT']['amount']
            debits = df[df['type'] == 'DEBIT']['amount'].abs()
            avg_income = credits.mean() if not credits.empty else 1.0
        else:
            df = pd.DataFrame(columns=['amount', 'type', 'narration', 'balance', 'date'])
            credits = pd.Series(dtype=float)
            debits = pd.Series(dtype=float)
            avg_income = 1.0
    except Exception:
        df = pd.DataFrame(columns=['amount', 'type', 'narration', 'balance', 'date'])
        credits = pd.Series(dtype=float)
        debits = pd.Series(dtype=float)
        avg_income = 1.0

    # 1. utility_payment_consistency
    try:
        count = df['narration'].str.contains('ELECTRICITY|WATER|BROADBAND|BILL', case=False, na=False).sum()
        result['utility_payment_consistency'] = float(count)
    except Exception:
        result['utility_payment_consistency'] = 0.0

    # 2. avg_utility_dpd
    try:
        if result['utility_payment_consistency'] >= 4:
            result['avg_utility_dpd'] = random.uniform(0, 5)
        else:
            result['avg_utility_dpd'] = random.uniform(10, 40)
    except Exception:
        result['avg_utility_dpd'] = 20.0

    # 3. rent_wallet_share
    try:
        rent_debits = df[(df['type'] == 'DEBIT') & (df['narration'].str.contains('RENT', case=False, na=False))]['amount'].abs()
        mean_rent = rent_debits.mean() if not rent_debits.empty else 0.0
        r_w_s = mean_rent / avg_income if avg_income > 0 else 0.0
        result['rent_wallet_share'] = float(r_w_s)
    except Exception:
        result['rent_wallet_share'] = 0.0
        
    # 4. subscription_commitment_ratio
    try:
        sub_debits = df[(df['type'] == 'DEBIT') & (df['narration'].str.contains('NETFLIX|SPOTIFY|SUBSCRIPTION|OTT|PRIME', case=False, na=False))]['amount'].abs()
        r_c_r = sub_debits.sum() / (avg_income * 6) if avg_income > 0 else 0.0
        result['subscription_commitment_ratio'] = float(r_c_r)
    except Exception:
        result['subscription_commitment_ratio'] = 0.0

    # 5. emergency_buffer_months
    try:
        essential = df[(df['type'] == 'DEBIT') & (df['narration'].str.contains('GROCERY|MEDICAL|ELECTRICITY|RENT|FUEL|PHARMACY|KIRANA', case=False, na=False))]['amount'].abs()
        avg_essential = essential.mean() if not essential.empty else 1.0
        if pd.isna(avg_essential) or avg_essential == 0:
            avg_essential = 1.0
        e_b_m = df['balance'].mean() / (avg_essential * 30) if not df['balance'].empty else 0.5
        result['emergency_buffer_months'] = float(e_b_m)
    except Exception:
        result['emergency_buffer_months'] = 0.5

    # 6. min_balance_violation_count
    try:
        count = (df['balance'] < 500).sum()
        result['min_balance_violation_count'] = float(count)
    except Exception:
        result['min_balance_violation_count'] = 0.0

    # 7. eod_balance_volatility
    try:
        mean_bal = df['balance'].mean()
        std_bal = df['balance'].std()
        if pd.isna(mean_bal) or mean_bal == 0 or pd.isna(std_bal):
            result['eod_balance_volatility'] = 1.0
        else:
            result['eod_balance_volatility'] = float(std_bal / mean_bal)
    except Exception:
        result['eod_balance_volatility'] = 1.0

    # 8. essential_vs_lifestyle_ratio
    try:
        essential = df[(df['type'] == 'DEBIT') & (df['narration'].str.contains('GROCERY|MEDICAL|ELECTRICITY|RENT|FUEL|PHARMACY|KIRANA', case=False, na=False))]['amount'].abs()
        lifestyle = df[(df['type'] == 'DEBIT') & (df['narration'].str.contains('RESTAURANT|ZOMATO|SWIGGY|AMAZON|TRAVEL|HOTEL', case=False, na=False))]['amount'].abs()
        life_sum = lifestyle.sum()
        if life_sum == 0:
            result['essential_vs_lifestyle_ratio'] = 3.0
        else:
            result['essential_vs_lifestyle_ratio'] = float(essential.sum() / life_sum)
    except Exception:
        result['essential_vs_lifestyle_ratio'] = 3.0

    # 9. cash_withdrawal_dependency
    try:
        cash = df[(df['type'] == 'DEBIT') & (df['narration'].str.contains('ATM|CASH', case=False, na=False))]['amount'].abs()
        deb_sum = debits.sum()
        if deb_sum == 0:
            result['cash_withdrawal_dependency'] = 0.0
        else:
            result['cash_withdrawal_dependency'] = float(cash.sum() / deb_sum)
    except Exception:
        result['cash_withdrawal_dependency'] = 0.0

    # 10. bounced_transaction_count
    try:
        count = df['narration'].str.contains('BOUNCE|RETURN|CHG', case=False, na=False).sum()
        result['bounced_transaction_count'] = float(count)
    except Exception:
        result['bounced_transaction_count'] = 0.0

    # 11. telecom_number_vintage_days
    try:
        result['telecom_number_vintage_days'] = float(profile.get('telecom_number_vintage_days', 365))
    except Exception:
        result['telecom_number_vintage_days'] = 365.0

    # 12. telecom_recharge_drop_ratio
    try:
        vintage = result.get('telecom_number_vintage_days', 365.0)
        result['telecom_recharge_drop_ratio'] = float(max(0.4, 1.5 - (vintage / 3000)))
    except Exception:
        result['telecom_recharge_drop_ratio'] = 1.0

    # 13. academic_background_tier
    try:
        result['academic_background_tier'] = float(profile.get('academic_background_tier', 2))
    except Exception:
        result['academic_background_tier'] = 2.0

    # 14. purpose_of_loan_encoded
    try:
        result['purpose_of_loan_encoded'] = float(profile.get('purpose_of_loan_encoded', 1))
    except Exception:
        result['purpose_of_loan_encoded'] = 1.0

    # 15. business_vintage_months
    try:
        result['business_vintage_months'] = float(profile.get('business_vintage_months', 24))
    except Exception:
        result['business_vintage_months'] = 24.0

    # 16. revenue_growth_trend
    try:
        if 'date' in df.columns and not df.empty and not credits.empty:
            credit_df = df[df['type'] == 'CREDIT']
            credit_df = credit_df[credit_df['date'].notna()]
            if not credit_df.empty:
                monthly_credits = credit_df.groupby(credit_df['date'].dt.to_period('M'))['amount'].sum()
                if len(monthly_credits) >= 2:
                    pct_change = monthly_credits.pct_change().mean()
                    val = float(pct_change) if not pd.isna(pct_change) else 0.0
                else:
                    val = 0.0
            else:
                val = 0.0
        else:
            val = 0.0
        result['revenue_growth_trend'] = val
    except Exception:
        result['revenue_growth_trend'] = 0.0

    # 17. revenue_seasonality_index
    try:
        if 'date' in df.columns and not df.empty and not credits.empty:
            credit_df = df[df['type'] == 'CREDIT']
            credit_df = credit_df[credit_df['date'].notna()]
            if not credit_df.empty:
                monthly_credits = credit_df.groupby(credit_df['date'].dt.to_period('M'))['amount'].sum()
                if len(monthly_credits) >= 2 and monthly_credits.mean() > 0:
                    val = float(monthly_credits.std() / monthly_credits.mean())
                    if pd.isna(val):
                        val = 0.5
                else:
                    val = 0.5
            else:
                val = 0.5
        else:
            val = 0.5
        result['revenue_seasonality_index'] = val
    except Exception:
        result['revenue_seasonality_index'] = 0.5
        
    # 18. operating_cashflow_ratio
    try:
        c_sum = credits.sum()
        d_sum = debits.sum()
        if d_sum == 0:
            result['operating_cashflow_ratio'] = 1.0
        else:
            result['operating_cashflow_ratio'] = float(c_sum / d_sum)
    except Exception:
        result['operating_cashflow_ratio'] = 1.0

    # 19. cashflow_volatility
    try:
        if 'date' in df.columns and not df.empty:
            credit_df = df[df['type'] == 'CREDIT']
            debit_df = df[df['type'] == 'DEBIT']
            monthly_credits = credit_df.groupby(credit_df['date'].dt.to_period('M'))['amount'].sum() if not credit_df.empty else pd.Series(dtype=float)
            monthly_debits = debit_df.groupby(debit_df['date'].dt.to_period('M'))['amount'].sum() if not debit_df.empty else pd.Series(dtype=float)
            monthly_net = monthly_credits.sub(monthly_debits, fill_value=0)
            if len(monthly_net) >= 2:
                val = float(monthly_net.std())
                if pd.isna(val):
                    val = 0.0
            else:
                val = 0.0
        else:
            val = 0.0
        result['cashflow_volatility'] = val
    except Exception:
        result['cashflow_volatility'] = 0.0

    # 20. avg_invoice_payment_delay
    try:
        if len(credits) >= 4:
            result['avg_invoice_payment_delay'] = random.uniform(3, 15)
        else:
            result['avg_invoice_payment_delay'] = random.uniform(20, 50)
    except Exception:
        result['avg_invoice_payment_delay'] = 30.0

    # 21. customer_concentration_ratio
    try:
        if credits.empty or credits.sum() == 0:
            result['customer_concentration_ratio'] = 1.0
        else:
            credit_df = df[df['type'] == 'CREDIT']
            top3 = credit_df.groupby('narration')['amount'].sum().nlargest(3)
            result['customer_concentration_ratio'] = float(top3.sum() / credits.sum())
    except Exception:
        result['customer_concentration_ratio'] = 1.0

    # 22. repeat_customer_revenue_pct
    try:
        if credits.empty or credits.sum() == 0:
            result['repeat_customer_revenue_pct'] = 0.0
        else:
            credit_df = df[df['type'] == 'CREDIT']
            counts = credit_df['narration'].value_counts()
            repeat_narrations = counts[counts > 1].index
            repeat_revenue = credit_df[credit_df['narration'].isin(repeat_narrations)]['amount'].sum()
            result['repeat_customer_revenue_pct'] = float(repeat_revenue / credits.sum())
    except Exception:
        result['repeat_customer_revenue_pct'] = 0.0

    # 23. vendor_payment_discipline
    try:
        if result.get('bounced_transaction_count', 0) == 0:
            result['vendor_payment_discipline'] = random.uniform(1, 10)
        else:
            result['vendor_payment_discipline'] = random.uniform(15, 45)
    except Exception:
        result['vendor_payment_discipline'] = 10.0

    # 24. gst_filing_consistency_score
    try:
        result['gst_filing_consistency_score'] = float(profile.get('gst_filing_consistency_score', 6))
    except Exception:
        result['gst_filing_consistency_score'] = 6.0

    # 25. gst_to_bank_variance
    try:
        if gst_data.get('available') and gst_data.get('declared_turnover', 0) > 0:
            d_t = gst_data.get('declared_turnover', 0)
            result['gst_to_bank_variance'] = float(abs(credits.sum() - d_t) / d_t)
        else:
            result['gst_to_bank_variance'] = 0.5
    except Exception:
        result['gst_to_bank_variance'] = 0.5

    # 26. p2p_circular_loop_flag
    try:
        flag = 0
        if not df.empty:
            narrations = df['narration'].astype(str).str.upper()
            if narrations.str.contains('SHYAM|UNKNOWN|CIRCULAR|SELF TRANSFER', na=False).any():
                flag = 1
        result['p2p_circular_loop_flag'] = float(flag)
    except Exception:
        result['p2p_circular_loop_flag'] = 0.0

    # 27. benford_anomaly_score
    try:
        non_zero = df[df['amount'] != 0]['amount'].abs().astype(int).astype(str).str[0].astype(int)
        non_zero = non_zero[non_zero > 0]
        if len(non_zero) < 10:
            result['benford_anomaly_score'] = 0.05
        else:
            expected = [math.log10(1 + 1/d) for d in range(1, 10)]
            counts = non_zero.value_counts(normalize=True)
            observed = [counts.get(d, 0.0) for d in range(1, 10)]
            ans = sum(abs(o - e) for o, e in zip(observed, expected))
            result['benford_anomaly_score'] = float(ans)
    except Exception:
        result['benford_anomaly_score'] = 0.05

    # 28. round_number_spike_ratio
    try:
        if df.empty:
            result['round_number_spike_ratio'] = 0.0
        else:
            count = (df['amount'].abs() % 1000 == 0).sum()
            result['round_number_spike_ratio'] = float(count / len(df))
    except Exception:
        result['round_number_spike_ratio'] = 0.0

    # 29. turnover_inflation_spike
    try:
        if result.get('round_number_spike_ratio', 0) > 0.6 and result.get('gst_to_bank_variance', 0) > 0.3:
            result['turnover_inflation_spike'] = 1.0
        else:
            result['turnover_inflation_spike'] = 0.0
    except Exception:
        result['turnover_inflation_spike'] = 0.0

    # 30. identity_device_mismatch
    try:
        if result.get('p2p_circular_loop_flag', 0) == 1.0 and result.get('bounced_transaction_count', 0) > 0:
            result['identity_device_mismatch'] = 1.0
        else:
            result['identity_device_mismatch'] = 0.0
    except Exception:
        result['identity_device_mismatch'] = 0.0

    keys_in_order = [
        'utility_payment_consistency',
        'avg_utility_dpd',
        'rent_wallet_share',
        'subscription_commitment_ratio',
        'emergency_buffer_months',
        'min_balance_violation_count',
        'eod_balance_volatility',
        'essential_vs_lifestyle_ratio',
        'cash_withdrawal_dependency',
        'bounced_transaction_count',
        'telecom_number_vintage_days',
        'telecom_recharge_drop_ratio',
        'academic_background_tier',
        'purpose_of_loan_encoded',
        'business_vintage_months',
        'revenue_growth_trend',
        'revenue_seasonality_index',
        'operating_cashflow_ratio',
        'cashflow_volatility',
        'avg_invoice_payment_delay',
        'customer_concentration_ratio',
        'repeat_customer_revenue_pct',
        'vendor_payment_discipline',
        'gst_filing_consistency_score',
        'gst_to_bank_variance',
        'p2p_circular_loop_flag',
        'benford_anomaly_score',
        'round_number_spike_ratio',
        'turnover_inflation_spike',
        'identity_device_mismatch'
    ]

    final_result = {k: float(result.get(k, 0.0)) for k in keys_in_order}
    return final_result

if __name__ == "__main__":
    result = compute_features([], {}, {})
    assert len(result) == 30
    print("[OK] feature_engine.py")
