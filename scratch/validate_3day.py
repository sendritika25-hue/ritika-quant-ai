import pandas as pd
import yfinance as yf
import os

log_path = "/home/sendritika25/trading_ai/prediction_log.csv"
if not os.path.exists(log_path):
    log_path = "prediction_log.csv"

if os.path.exists(log_path):
    df = pd.read_csv(log_path)
    pending_mask = (df['Status'] == 'PENDING') | (df['Outcome'].astype(str).str.contains('PENDING', case=False, na=False))
    pending_indices = df[pending_mask].index
    print(f"Pending rows count: {len(pending_indices)}")

    for idx in pending_indices:
        row = df.loc[idx]
        ticker = str(row['Ticker']).replace(' (Intraday)', '').replace(' (LongTerm)', '').strip()
        signal = str(row['Signal']).upper()
        entry_p = float(row['EntryPrice']) if pd.notnull(row['EntryPrice']) else 0.0
        
        if entry_p > 0:
            try:
                data = yf.Ticker(ticker).history(period='5d').reset_index()
                if not data.empty and len(data) >= 1:
                    close_p = float(data['Close'].iloc[-1])
                    ret_pct = round(((close_p - entry_p) / entry_p) * 100, 2)
                    df.at[idx, 'NextDayClose'] = close_p
                    df.at[idx, 'ReturnPct'] = ret_pct
                    df.at[idx, 'Status'] = 'VALIDATED'
                    
                    if signal == 'BUY':
                        df.at[idx, 'Outcome'] = '✅ CORRECT (Target Hit)' if close_p > entry_p else '❌ WRONG'
                    elif signal == 'SELL':
                        df.at[idx, 'Outcome'] = '✅ CORRECT (Profit Close)' if close_p < entry_p else '❌ WRONG'
                    else:
                        df.at[idx, 'Outcome'] = '✅ CORRECT (Hold Validated)' if abs(ret_pct) < 1.8 else '❌ WRONG'
            except Exception as e:
                print(f"Error validating {ticker}: {e}")

    df.to_csv(log_path, index=False)
    print("Updated prediction_log.csv successfully.")

    # Show 3-Day Statistics
    val = df[df['Status'] == 'VALIDATED']
    correct = val[val['Outcome'].astype(str).str.contains('CORRECT', case=False, na=False)]
    
    intra_val = val[val['Ticker'].astype(str).str.contains('\(Intraday\)', case=False, na=False)]
    intra_correct = intra_val[intra_val['Outcome'].astype(str).str.contains('CORRECT', case=False, na=False)]
    
    deliv_val = val[~val['Ticker'].astype(str).str.contains('\(Intraday\)|\(LongTerm\)', case=False, na=False)]
    deliv_correct = deliv_val[deliv_val['Outcome'].astype(str).str.contains('CORRECT', case=False, na=False)]
    
    print("\n=== AUDIT RESULTS SUMMARY ===")
    print(f"Total Validated Signals: {len(val)}")
    print(f"Total Correct Signals: {len(correct)}")
    if len(val) > 0:
        print(f"Overall Win-Rate: {(len(correct)/len(val))*100:.2f}%")
        
    if len(intra_val) > 0:
        print(f"Intraday Win-Rate: {(len(intra_correct)/len(intra_val))*100:.2f}% ({len(intra_correct)}/{len(intra_val)})")
        
    if len(deliv_val) > 0:
        print(f"Delivery Win-Rate: {(len(deliv_correct)/len(deliv_val))*100:.2f}% ({len(deliv_correct)}/{len(deliv_val)})")

