import pandas as pd
import os

log_path = "/home/sendritika25/trading_ai/prediction_log.csv"
if not os.path.exists(log_path):
    log_path = "prediction_log.csv"

if os.path.exists(log_path):
    df = pd.read_csv(log_path)
    df['Date_Parsed'] = pd.to_datetime(df['Date'], errors='coerce')
    
    recent_df = df.tail(30).copy()
    
    print("=== RECENT 3 DAYS PREDICTION AUDIT LOG ===")
    print(recent_df[['Date', 'Ticker', 'EntryPrice', 'Signal', 'Confidence', 'NextDayClose', 'ReturnPct', 'Outcome']].to_string(index=False))
    
    val = recent_df[recent_df['Status'] == 'VALIDATED']
    correct = val[val['Outcome'].astype(str).str.contains('CORRECT', case=False, na=False)]
    
    print("\n=== SUMMARY STATISTICS ===")
    print(f"Total Recent Logs: {len(recent_df)}")
    print(f"Total Validated Trades: {len(val)}")
    print(f"Correct Trades: {len(correct)}")
    if len(val) > 0:
        win_rate = (len(correct) / len(val)) * 100
        print(f"Recent Win-Rate Accuracy: {win_rate:.2f}%")
else:
    print("Log file not found.")

