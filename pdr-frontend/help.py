import pandas as pd

df_hc = pd.read_csv('application_train.csv')
df_lc = pd.read_csv('accepted_2007_to_2018Q4.csv')
df_msme = df_lc[df_lc['purpose'] == 'small_business'].copy()
print(df_hc['TARGET'].value_counts(normalize=True))
print(df_msme['loan_status'].value_counts())

# Drop 'Current' and 'In Grace Period' — no outcome yet
df_msme = df_msme[~df_msme['loan_status'].isin([
    'Current', 
    'In Grace Period',
    'Late (16-30 days)',   # ambiguous — could still recover
    'Late (31-120 days)'  # ambiguous
])]

# Now create clean binary label
default_statuses = [
    'Charged Off',
    'Does not meet the credit policy. Status:Charged Off'
]
df_msme['TARGET'] = df_msme['loan_status'].isin(default_statuses).astype(int)

print(df_msme['TARGET'].value_counts())
print(f"Clean MSME rows: {len(df_msme)}")