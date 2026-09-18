import pandas as pd
import numpy as np

df = pd.read_csv("/home/sendritika25/trading_ai/prediction_log.csv")

intra_df = df[df['Ticker'].astype(str).str.contains('\(Intraday\)', case=False, na=False)].copy()
val_intra = intra_df[intra_df['Status'] == 'VALIDATED'].copy()

total_intraday = len(intra_df)
total_validated = len(val_intra)

# Actionable trades (BUY / SELL)
action_df = val_intra[val_intra['Signal'].isin(['BUY', 'SELL', 'UP', 'DOWN'])].copy()
action_total = len(action_df)
action_correct = len(action_df[action_df['Outcome'].astype(str).str.contains('CORRECT', case=False, na=False)])

win_rate = (action_correct / action_total * 100) if action_total > 0 else 0.0

print(f"--- INTRADAY ACCURACY AUDIT REPORT ---")
print(f"Total Intraday Signals Logged: {total_intraday}")
print(f"Validated Intraday Signals: {total_validated}")
print(f"Actionable Intraday Trades (BUY/SELL): {action_total}")
print(f"Correct Intraday Trades: {action_correct}")
print(f"INTRADAY WIN-RATE ACCURACY: {win_rate:.2f}%")

