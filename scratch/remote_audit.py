import pandas as pd

df = pd.read_csv('/home/sendritika25/trading_ai/prediction_log.csv')
validated = df[df['Status'] == 'VALIDATED']

buy_sell = validated[validated['Signal'].isin(['BUY', 'SELL'])]
bs_total = len(buy_sell)
bs_correct = len(buy_sell[buy_sell['Outcome'].str.contains('CORRECT', na=False)])
bs_win = (bs_correct / bs_total * 100) if bs_total > 0 else 0

top_picks = buy_sell[buy_sell['Confidence'].astype(str).str.rstrip('%').astype(float) >= 70.0]
tp_total = len(top_picks)
tp_correct = len(top_picks[top_picks['Outcome'].str.contains('CORRECT', na=False)])
tp_win = (tp_correct / tp_total * 100) if tp_total > 0 else 0

holds = validated[validated['Signal'] == 'HOLD']
h_total = len(holds)
h_neutral = len(holds[holds['Outcome'].str.contains('NEUTRAL', na=False)])
h_safety = (h_neutral / h_total * 100) if h_total > 0 else 0

print("--- AUDIT SUMMARY REPORT ---")
print(f"Total Logged Predictions: {len(df)}")
print(f"Validated Predictions: {len(validated)}")
print(f"BUY/SELL Action Trades: {bs_total} | Correct: {bs_correct} | Win Rate: {bs_win:.2f}%")
print(f"70%+ Top Confidence Picks: {tp_total} | Correct: {tp_correct} | Win Rate: {tp_win:.2f}%")
print(f"HOLD Capital Safety Protection: {h_total} | Neutral Protection: {h_neutral} | Safety Rate: {h_safety:.2f}%")

