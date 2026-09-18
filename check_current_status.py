import json
import sys
import yfinance as yf

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

with open("user_active_holdings.json") as f:
    holdings = json.load(f)

print(f"{'Stock':<12} | {'Type':<10} | {'Entry':<8} | {'Current':<8} | {'Gain %':<8} | {'Target':<8} | {'SL':<8} | {'Status'}")
print("-" * 80)
for h in holdings:
    sym = h["symbol"]
    name = h["name"]
    entry = float(h["entry"])
    target = float(h["target"])
    sl = float(h["sl"])
    ttype = h["trade_type"]
    try:
        df = yf.Ticker(sym).history(period="1d", interval="5m")
        if df.empty or len(df) == 0:
            print(f"{name:<12} | {ttype:<10} | {entry:<8.2f} | {'N/A':<8} | {'N/A':<8} | {target:<8.2f} | {sl:<8.2f} | Data Unavailable")
            continue
        curr = round(float(df["Close"].iloc[-1]), 2)
        gain = round(((curr - entry) / entry) * 100, 2)
        
        status = "NORMAL"
        if curr >= target:
            status = "🎯 TARGET HIT (PROFIT BOOK NOW!)"
        elif gain >= 1.2:
            status = "🛡️ TRAILING SL ACTIVE (Zero Risk)"
        elif curr <= sl:
            status = "🛑 SL HIT (EXIT NOW)"
        elif gain > 0:
            status = "🟢 PROFIT"
        else:
            status = "🔻 LOSS"

        print(f"{name:<12} | {ttype:<10} | {entry:<8.2f} | {curr:<8.2f} | {gain:+7.2f}% | {target:<8.2f} | {sl:<8.2f} | {status}")
    except Exception as e:
        print(f"{name:<12} | {ttype:<10} | Error: {e}")
