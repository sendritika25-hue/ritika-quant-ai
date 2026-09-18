import pandas as pd
import os

log_path = "/home/sendritika25/trading_ai/prediction_log.csv"
if os.path.exists(log_path):
    df = pd.read_csv(log_path, on_bad_lines='skip')
    pending = df[df['Status'].astype(str).str.upper().isin(['PENDING', '⏳ PENDING'])]
    
    print(f"==================================================")
    print(f"📋 100 REAL PENDING PREDICTIONS LOGGED FOR TOMORROW:")
    print(f"• Total Logged Rows   : {len(df)}")
    print(f"• Pending for Tomorrow: {len(pending)}")
    print(f"==================================================")
    
    signals_count = pending['Signal'].value_counts()
    print("\n📊 Signal Distribution:")
    for sig, cnt in signals_count.items():
        print(f"  - {sig}: {cnt} stocks")
        
    print("\n📋 Sample 15 Pending Tickers:")
    print(pending[['Ticker', 'EntryPrice', 'Signal', 'Confidence', 'Outcome']].head(15).to_string(index=False))

