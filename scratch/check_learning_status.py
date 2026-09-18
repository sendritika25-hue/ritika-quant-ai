import pandas as pd
import os

path = "/home/sendritika25/trading_ai/self_learning_history.csv"
if not os.path.exists(path):
    path = "self_learning_history.csv"

if os.path.exists(path):
    df = pd.read_csv(path)
    print("=== SELF-LEARNING AI RETRAINING AUDIT ===")
    print(df.to_string(index=False))
    print(f"\nTotal Retraining Epochs Completed: {len(df)}")
    if 'MistakesLearned' in df.columns:
        print(f"Total Past Mistakes Learned & Corrected: {df['MistakesLearned'].sum()}")
else:
    print("Self learning log not found.")

