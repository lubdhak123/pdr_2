import pandas as pd
df = pd.read_csv('pdr_training_data_v2.csv')
# Remove the leaked column
df = df.drop(columns=['default_prob'], errors='ignore')
df.to_csv('pdr_training_data_v2_clean.csv', index=False)
print("✅ Cleaned file saved as pdr_training_data_v2_clean.csv")