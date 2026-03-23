import pandas as pd
df = pd.read_csv('MyTransaction.csv')
df1 = pd.read_csv('upi_transactions_2024.csv')
print(df.describe())
print(df.head())
print(df1.describe())
print(df1.head())