import pandas as pd
df = pd.read_csv('pdr_training_data_realistic.csv')
print(df.groupby('default_label')[
    ['bounced_transaction_count','telecom_number_vintage_days',
     'p2p_circular_loop_flag','gst_filing_consistency_score']
].mean().round(3).T)

assert df[df.default_label==0]['bounced_transaction_count'].mean() > 0.05, \
    'STOP: good borrowers still have zero bounces — Fix 1b did not apply'
assert df[df.default_label==0]['p2p_circular_loop_flag'].mean() > 0.001, \
    'STOP: p2p_flag still perfectly separated — Fix 1d did not apply'

print('Distribution check PASSED — safe to train')
