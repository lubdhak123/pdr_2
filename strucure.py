import pandas as pd

df = pd.read_csv('pdr_training_data_realistic.csv')
print(df.describe())
print(df.head())