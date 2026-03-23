import pandas as pd
import matplotlib.pyplot as plt
import os

UPI_PATH = r"C:\Users\kanis\OneDrive\Desktop\ecirricula\datasets\new dataset\upitransactions2024.csv"
CHARTS_DIR = os.path.join(os.path.dirname(__file__), "charts")

def analyze_upi_fraud():
    # Ensure charts directory exists
    os.makedirs(CHARTS_DIR, exist_ok=True)
    
    # Check if the file actually exists for local testing, otherwise create mock dataframe
    if os.path.exists(UPI_PATH):
        df = pd.read_csv(UPI_PATH)
    else:
        # Fallback to local path if running on this machine
        local_path = "../upi_transactions_2024.csv"
        if os.path.exists(local_path):
            df = pd.read_csv(local_path)
        else:
            print("UPI CSV not found. Unable to run analysis.")
            return

    # 1. Total row count
    total_rows = len(df)
    print("\n--- UPI FRAUD ANALYSIS ---")
    print(f"1. Total row count: {total_rows}")

    # 2. Fraud count and fraud rate
    # Assume fraud_flag column is 1 for fraud, 0 for normal
    fraud_count = df['fraud_flag'].sum() if 'fraud_flag' in df.columns else 0
    fraud_rate = fraud_count / total_rows if total_rows > 0 else 0
    print(f"2. Fraud count: {fraud_count} (Fraud Rate: {fraud_rate:.4%})")

    # 3. Transaction status distribution
    if 'transaction_status' in df.columns:
        print("\n3. Transaction status distribution:")
        print(df['transaction_status'].value_counts())

    # 4. Transaction type distribution
    if 'transaction_type' in df.columns:
        print("\n4. Transaction type distribution:")
        print(df['transaction_type'].value_counts(normalize=True))

    # Calculate and plot fraud rates if fraud_flag exists
    if 'fraud_flag' in df.columns:
        # 5. Fraud rate by transaction_type
        if 'transaction_type' in df.columns:
            print("\n5. Fraud rate by transaction_type:")
            fr_by_type = df.groupby('transaction_type')['fraud_flag'].mean().sort_values(ascending=False)
            print(fr_by_type)
            
            # Plot
            plt.figure(figsize=(10, 6))
            fr_by_type.plot(kind='bar', color='salmon')
            plt.title('Fraud Rate by Transaction Type')
            plt.ylabel('Fraud Rate')
            plt.tight_layout()
            plt.savefig(os.path.join(CHARTS_DIR, 'fraud_by_type.png'))
            plt.close()

        # 6. Fraud rate by merchant_category
        if 'merchant_category' in df.columns:
            print("\n6. Fraud rate by merchant_category:")
            fr_by_cat = df.groupby('merchant_category')['fraud_flag'].mean().sort_values(ascending=False)
            print(fr_by_cat.head(10))
            
            # Plot Top 10
            plt.figure(figsize=(12, 6))
            fr_by_cat.head(10).plot(kind='bar', color='skyblue')
            plt.title('Top 10 Merchant Categories by Fraud Rate')
            plt.ylabel('Fraud Rate')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig(os.path.join(CHARTS_DIR, 'fraud_by_category.png'))
            plt.close()

        # 7. Fraud rate by sender_state
        if 'sender_state' in df.columns:
            print("\n7. Fraud rate by sender_state:")
            fr_by_state = df.groupby('sender_state')['fraud_flag'].mean().sort_values(ascending=False)
            print(fr_by_state.head(10))

        # 8. Fraud rate by device_type
        if 'device_type' in df.columns:
            print("\n8. Fraud rate by device_type:")
            fr_by_device = df.groupby('device_type')['fraud_flag'].mean().sort_values(ascending=False)
            print(fr_by_device)

        # 9. Fraud rate by network_type
        if 'network_type' in df.columns:
            print("\n9. Fraud rate by network_type:")
            fr_by_network = df.groupby('network_type')['fraud_flag'].mean().sort_values(ascending=False)
            print(fr_by_network)

        # 10. Fraud rate by hour_of_day
        if 'hour_of_day' in df.columns:
            print("\n10. Fraud rate by hour_of_day:")
            fr_by_hour = df.groupby('hour_of_day')['fraud_flag'].mean()
            print(fr_by_hour)
            
            # Plot
            plt.figure(figsize=(10, 6))
            fr_by_hour.plot(kind='line', marker='o', color='purple')
            plt.title('Fraud Rate by Hour of Day')
            plt.xlabel('Hour')
            plt.ylabel('Fraud Rate')
            plt.grid(True, alpha=0.3)
            plt.xticks(range(0, 24))
            plt.tight_layout()
            plt.savefig(os.path.join(CHARTS_DIR, 'fraud_by_hour.png'))
            plt.close()

    # 11. Amount summary split by fraud_flag
    if 'amount' in df.columns and 'fraud_flag' in df.columns:
        print("\n11. Amount summary split by fraud_flag:")
        print(df.groupby('fraud_flag')['amount'].describe())

if __name__ == "__main__":
    analyze_upi_fraud()
