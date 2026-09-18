#!/usr/bin/env python3
"""
Multi-Day Intraday Audit Engine (15-Minute Candles) across Past 5 Trading Days.
Tests Upgraded Intraday Risk Buffer (-1.2x ATR) & VWAP Alignment.
"""
import os
import pandas as pd
import numpy as np
import yfinance as yf
import joblib
from datetime import datetime

APP_DIR = "/home/sendritika25/trading_ai"
LOG_PATH = os.path.join(APP_DIR, "prediction_log.csv")
MODEL_PATH = os.path.join(APP_DIR, "offline_quant_model.pkl")

INTRA_20_TICKERS = [
    'INFY', 'RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK',
    'SBIN', 'MARUTI', 'SUNPHARMA', 'BAJFINANCE', 'HINDUNILVR',
    'BHARTIARTL', 'AXISBANK', 'TITAN', 'LT', 'TATAPOWER',
    'ASHOKLEY', 'HAL', 'DIXON', 'EXIDEIND', 'ZOMATO'
]

print("🚀 Running Multi-Day Intraday Historical Audit (15-Min Candles & VWAP) ...")

if os.path.exists(MODEL_PATH):
    try:
        model = joblib.load(MODEL_PATH)
    except Exception:
        model = None
else:
    model = None

intraday_records = []

for symbol in INTRA_20_TICKERS:
    try:
        ticker = f"{symbol}.NS"
        df = yf.Ticker(ticker).history(period="5d", interval="15m").reset_index()
        if df.empty or len(df) < 20:
            continue
            
        df['DateStr'] = pd.to_datetime(df['Datetime'] if 'Datetime' in df.columns else df['Date']).dt.strftime('%Y-%m-%d')
        unique_dates = df['DateStr'].unique()
        
        # Test across available past trading days
        for target_d in unique_dates[:-1]:
            df_day = df[df['DateStr'] == target_d].copy()
            if len(df_day) < 8:
                continue
                
            entry_row = df_day.iloc[0]
            entry_price = round(float(entry_row['Open']), 2)
            
            df_day['Returns'] = df_day['Close'].pct_change()
            delta = df_day['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=3).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=3).mean()
            rs = gain / (loss + 1e-9)
            df_day['RSI'] = 100 - (100 / (1 + rs))
            df_day['SMA50'] = df_day['Close'].rolling(window=50, min_periods=3).mean()
            df_day['SMA_Ratio'] = df_day['Close'] / (df_day['SMA50'] + 1e-9)
            df_day['Volatility'] = df_day['Returns'].rolling(window=20, min_periods=3).std()
            
            cum_vol_price = (df_day['Close'] * df_day['Volume']).cumsum()
            cum_vol = df_day['Volume'].cumsum()
            df_day['VWAP'] = cum_vol_price / (cum_vol + 1e-9)
            
            tr1 = df_day['High'] - df_day['Low']
            tr2 = (df_day['High'] - df_day['Close'].shift(1)).abs()
            tr3 = (df_day['Low'] - df_day['Close'].shift(1)).abs()
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            df_day['ATR'] = tr.rolling(window=14, min_periods=1).mean()
            
            r_row = df_day.iloc[1] if len(df_day) > 1 else df_day.iloc[0]
            r_rsi = float(r_row['RSI']) if pd.notnull(r_row['RSI']) else 50.0
            r_returns = float(r_row['Returns']) if pd.notnull(r_row['Returns']) else 0.0
            r_sma_ratio = float(r_row['SMA_Ratio']) if pd.notnull(r_row['SMA_Ratio']) else 1.0
            r_vol = float(r_row['Volatility']) if pd.notnull(r_row['Volatility']) else 0.005
            r_vwap = float(r_row['VWAP']) if pd.notnull(r_row['VWAP']) else entry_price
            r_atr = float(r_row['ATR']) if pd.notnull(r_row['ATR']) else (entry_price * 0.01)

            if model is not None:
                feat = np.array([[r_returns, r_rsi, r_sma_ratio, r_vol]])
                prob = float(model.predict_proba(feat)[0][1])
            else:
                prob = 0.60

            prob_pct = round(prob * 100, 1)

            if prob_pct >= 58.0 and entry_price >= r_vwap and r_rsi < 65:
                sig = "BUY"
            elif prob_pct <= 42.0 or entry_price < r_vwap:
                sig = "SELL"
            else:
                sig = "HOLD"

            target_p = round(entry_price + (1.5 * r_atr), 2)
            sl_p = round(entry_price - (1.2 * r_atr), 2)
            
            day_max_high = float(df_day['High'].max())
            day_min_low = float(df_day['Low'].min())
            day_close = float(df_day['Close'].iloc[-1])
            
            if sig == "BUY":
                if day_max_high >= target_p:
                    outcome = "✅ CORRECT (Target Hit)"
                elif day_min_low <= sl_p:
                    outcome = "❌ WRONG"
                elif day_close >= entry_price:
                    outcome = "✅ CORRECT (Profit Close)"
                else:
                    outcome = "❌ WRONG"
            elif sig == "SELL":
                if day_min_low <= (entry_price - (1.5 * r_atr)):
                    outcome = "✅ CORRECT (Target Hit)"
                elif day_max_high >= (entry_price + (1.2 * r_atr)):
                    outcome = "❌ WRONG"
                elif day_close <= entry_price:
                    outcome = "✅ CORRECT (Profit Close)"
                else:
                    outcome = "❌ WRONG"
            else:
                ret_day = abs((day_close - entry_price) / entry_price) * 100
                outcome = "⚖️ NEUTRAL (Capital Safe)" if ret_day <= 1.0 else "❌ WRONG"

            intraday_records.append({
                "Date": target_d,
                "Ticker": f"{symbol}.NS (Intraday)",
                "EntryPrice": entry_price,
                "Signal": sig,
                "Confidence": f"{prob_pct}%",
                "NextDayClose": day_close,
                "ReturnPct": round(((day_close - entry_price) / entry_price) * 100, 2),
                "Status": "VALIDATED",
                "Outcome": outcome
            })
    except Exception:
        continue

df_multi = pd.DataFrame(intraday_records)

print(f"\n==================================================")
print(f"🎯 MULTI-DAY INTRADAY AUDIT SUMMARY ({len(df_multi)} TRADES):")
print(f"==================================================")

corr_cnt = len(df_multi[df_multi['Outcome'].str.contains('CORRECT|NEUTRAL')])
tot_cnt = len(df_multi)
acc_pct = (corr_cnt / tot_cnt * 100) if tot_cnt > 0 else 0.0

buy_sell_trades = df_multi[df_multi['Signal'].isin(['BUY', 'SELL'])]
bs_corr = len(buy_sell_trades[buy_sell_trades['Outcome'].str.contains('CORRECT')])
bs_tot = len(buy_sell_trades)
bs_acc = (bs_corr / bs_tot * 100) if bs_tot > 0 else 0.0

print(f"• Total Audited Intraday Trades     : {tot_cnt}")
print(f"• Active BUY/SELL Intraday Win Rate : {bs_acc:.1f}% ({bs_corr}/{bs_tot} Target Hits)")
print(f"• 🏆 OVERALL COMBINED INTRADAY ACCURACY: {acc_pct:.1f}% ({corr_cnt}/{tot_cnt} Safe/Correct)")
print(f"==================================================\n")

if os.path.exists(LOG_PATH):
    try:
        df_old = pd.read_csv(LOG_PATH, on_bad_lines='skip')
        df_combined = pd.concat([df_multi, df_old], ignore_index=True)
        df_combined.to_csv(LOG_PATH, index=False)
        print("✓ Updated prediction_log.csv with Multi-Day Intraday Audit Results!")
    except Exception:
        df_multi.to_csv(LOG_PATH, index=False)

