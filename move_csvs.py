import os
import shutil

os.makedirs('profile_transactions', exist_ok=True)
for f in os.listdir('demo_csvs'):
    if f.endswith('.csv'):
        parts = f.replace('.csv', '').split('_')
        user_id = f"{parts[-2]}_{parts[-1]}"
        new_name = f"{user_id}_statement.csv"
        shutil.copy(os.path.join('demo_csvs', f), os.path.join('profile_transactions', new_name))
        print(f"Copied {f} to profile_transactions/{new_name}")

shutil.rmtree('demo_csvs')
print("Deleted demo_csvs directory.")
