import yfinance as yf
import pandas as pd

ticker = yf.Ticker('SIEMENS.NS')
df = ticker.history(period='1mo', interval='1d').reset_index()

if not df.empty:
    last_p = float(df['Close'].iloc[-1])
    tr1 = df['High'] - df['Low']
    tr2 = (df['High'] - df['Close'].shift(1)).abs()
    tr3 = (df['Low'] - df['Close'].shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = float(tr.rolling(14).mean().iloc[-1])
    target_down = round(last_p - (1.5 * atr), 2)
    sl_up = round(last_p + (1.0 * atr), 2)
    print(f"SIEMENS Current Price: ₹{last_p:,.2f}")
    print(f"Daily ATR Volatility: ₹{atr:,.2f}")
    print(f"Short/SELL Profit Target: ₹{target_down:,.2f}")
    print(f"Stop-Loss: ₹{sl_up:,.2f}")

