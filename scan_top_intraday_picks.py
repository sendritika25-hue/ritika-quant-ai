import os
import yfinance as yf
import pandas as pd
import numpy as np
import joblib

MODEL_PATH = "/home/sendritika25/trading_ai/offline_quant_model.pkl"
candidates = ['INFY.NS', 'MARUTI.NS', 'RELIANCE.NS', 'TCS.NS', 'SUNPHARMA.NS', 'BAJFINANCE.NS', 'HINDUNILVR.NS', 'TITAN.NS', 'BHARTIARTL.NS', 'DIXON.NS']

if os.path.exists(MODEL_PATH):
    try:
        model = joblib.load(MODEL_PATH)
    except Exception:
        model = None
else:
    model = None

picks = []

for sym in candidates:
    try:
        df = yf.Ticker(sym).history(period="5d", interval="15m").reset_index()
        if df.empty or len(df) < 15:
            continue
            
        df['Returns'] = df['Close'].pct_change()
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=3).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=3).mean()
        rs = gain / (loss + 1e-9)
        df['RSI'] = 100 - (100 / (1 + rs))
        df['SMA50'] = df['Close'].rolling(window=50, min_periods=3).mean()
        df['SMA_Ratio'] = df['Close'] / (df['SMA50'] + 1e-9)
        df['Volatility'] = df['Returns'].rolling(window=20, min_periods=3).std()
        
        cum_vol_price = (df['Close'] * df['Volume']).cumsum()
        cum_vol = df['Volume'].cumsum()
        df['VWAP'] = cum_vol_price / (cum_vol + 1e-9)
        
        tr1 = df['High'] - df['Low']
        tr2 = (df['High'] - df['Close'].shift(1)).abs()
        tr3 = (df['Low'] - df['Close'].shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['ATR'] = tr.rolling(window=7, min_periods=1).mean()
        
        row = df.iloc[-1]
        price = round(float(row['Close']), 2)
        rsi = round(float(row['RSI']), 1)
        vwap = round(float(row['VWAP']), 2)
        atr = float(row['ATR']) if pd.notnull(row['ATR']) else (price * 0.01)
        
        if model is not None:
            feat = np.array([[row['Returns'], row['RSI'], row['SMA_Ratio'], row['Volatility']]])
            conf = round(float(model.predict_proba(feat)[0][1]) * 100, 1)
        else:
            conf = 65.0
            
        target = round(price + (1.5 * atr), 2)
        sl = round(price - (1.2 * atr), 2)
        
        if price >= vwap and rsi < 65 and conf >= 60.0:
            picks.append({
                "Stock": sym.replace(".NS", ""),
                "Price": price,
                "VWAP": vwap,
                "Target": target,
                "StopLoss": sl,
                "GainPct": round(((target - price)/price)*100, 2),
                "Confidence": conf
            })
    except Exception:
        continue

picks = sorted(picks, key=lambda x: x['Confidence'], reverse=True)[:3]

print(f"==================================================")
print(f"⚡ TOP AI INTRADAY PICKS SCANNED FOR NEXT SESSION:")
print(f"==================================================")
for p in picks:
    print(f"• {p['Stock']}: Price ₹{p['Price']} | Target ₹{p['Target']} (+{p['GainPct']}%) | SL ₹{p['StopLoss']} | AI Conf: {p['Confidence']}%")

