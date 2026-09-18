#!/usr/bin/env python3
"""
Automated Daily Audit, Self-Learning, and Fresh Prediction Batch Pipeline
Runs automatically after market close (e.g., 4:00 PM IST) on the GCP VM.
"""
import os
import sys
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import joblib

APP_DIR = "/home/sendritika25/trading_ai"
LOG_PATH = os.path.join(APP_DIR, "prediction_log.csv")
MODEL_PATH = os.path.join(APP_DIR, "offline_quant_model.pkl")
LEARNING_LOG_PATH = os.path.join(APP_DIR, "self_learning_history.csv")
HOLD_THRESHOLD = 2.0

print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 STARTING AUTOMATED DAILY AUDIT & SELF-LEARNING PIPELINE...")

# 1. STRICT VALIDATION ENGINE
if os.path.exists(LOG_PATH):
    try:
        df_logs = pd.read_csv(LOG_PATH, on_bad_lines='skip')
        if not df_logs.empty:
            updated = False
            for idx, row in df_logs.iterrows():
                pred_date_str = str(row.get('Date', '')).strip()
                status_str = str(row.get('Status', '')).strip().upper()
                
                if status_str in ['PENDING', '⏳ PENDING'] and pred_date_str not in ['nan', 'None', '']:
                    try:
                        ticker = str(row['Ticker']).strip()
                        entry = float(row['EntryPrice'])
                        
                        ticker_obj = yf.Ticker(ticker)
                        hist = ticker_obj.history(period="10d")
                        
                        if not hist.empty:
                            hist.index = hist.index.strftime('%Y-%m-%d')
                            available_dates = list(hist.index)
                            future_dates = [d for d in available_dates if d > pred_date_str]
                            
                            if len(future_dates) > 0:
                                next_day_date = future_dates[0]
                                actual_next_close = float(hist.loc[next_day_date, 'Close'])
                                
                                if entry > 0 and not np.isnan(actual_next_close):
                                    ret_pct = round(((actual_next_close - entry) / entry) * 100, 2)
                                    df_logs.at[idx, 'NextDayClose'] = round(actual_next_close, 2)
                                    df_logs.at[idx, 'ReturnPct'] = ret_pct
                                    df_logs.at[idx, 'Status'] = 'VALIDATED'
                                    
                                    sig = str(row.get('Signal', '')).strip().upper()
                                    if sig == 'HOLD':
                                        df_logs.at[idx, 'Outcome'] = '⚖️ NEUTRAL' if abs(ret_pct) <= HOLD_THRESHOLD else '❌ WRONG'
                                    elif sig in ['BUY', 'UP']:
                                        df_logs.at[idx, 'Outcome'] = '✅ CORRECT' if ret_pct > 0 else '❌ WRONG'
                                    elif sig in ['SELL', 'DOWN']:
                                        df_logs.at[idx, 'Outcome'] = '✅ CORRECT' if ret_pct < 0 else '❌ WRONG'
                                        
                                    updated = True
                            else:
                                df_logs.at[idx, 'Outcome'] = '⏳ PENDING'
                    except Exception:
                        continue
                        
            if updated:
                df_logs.to_csv(LOG_PATH, index=False)
                print("✓ Successfully Validated Pending Predictions with Actual Market Closes!")
    except Exception as e:
        print(f"Error in validation: {e}")

# 2. CONTINUOUS SELF-LEARNING RETRAINING
if os.path.exists(LOG_PATH) and os.path.exists(MODEL_PATH):
    try:
        df_logs = pd.read_csv(LOG_PATH, on_bad_lines='skip')
        validated_logs = df_logs[df_logs['Status'] == 'VALIDATED']
        
        if len(validated_logs) >= 10:
            learning_features = []
            learning_targets = []
            wrong_count = 0
            
            for idx, row in validated_logs.iterrows():
                ticker = str(row.get('Ticker', '')).strip()
                entry_p = float(row.get('EntryPrice', 0))
                close_p = float(row.get('NextDayClose', 0)) if pd.notnull(row.get('NextDayClose')) else entry_p
                outcome = str(row.get('Outcome', '')).upper()
                
                if outcome == '❌ WRONG':
                    wrong_count += 1
                    
                if entry_p > 0 and close_p > 0:
                    actual_target = 1 if close_p > entry_p else 0
                    try:
                        df_tech = yf.Ticker(ticker).history(period="1y").reset_index()
                        if not df_tech.empty and len(df_tech) > 20:
                            df_tech['Returns'] = df_tech['Close'].pct_change()
                            delta = df_tech['Close'].diff()
                            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                            rs = gain / (loss + 1e-9)
                            df_tech['RSI'] = 100 - (100 / (1 + rs))
                            df_tech['SMA50'] = df_tech['Close'].rolling(window=50).mean()
                            df_tech['SMA_Ratio'] = df_tech['Close'] / (df_tech['SMA50'] + 1e-9)
                            df_tech['Volatility'] = df_tech['Returns'].rolling(window=20).std()
                            df_tech.dropna(inplace=True)
                            
                            if not df_tech.empty:
                                last_feat = [
                                    float(df_tech['Returns'].iloc[-1]),
                                    float(df_tech['RSI'].iloc[-1]),
                                    float(df_tech['SMA_Ratio'].iloc[-1]),
                                    float(df_tech['Volatility'].iloc[-1])
                                ]
                                learning_features.append(last_feat)
                                learning_targets.append(actual_target)
                    except Exception:
                        continue
                        
            if len(learning_features) >= 10:
                X_feedback = np.array(learning_features)
                y_feedback = np.array(learning_targets)
                model_obj = joblib.load(MODEL_PATH)
                model_obj.fit(X_feedback, y_feedback)
                joblib.dump(model_obj, MODEL_PATH)
                print(f"✓ Self-Learning Retrain Complete! Learned from {wrong_count} mistakes across {len(learning_features)} trades.")
    except Exception as e:
        print(f"Error in self-learning: {e}")

print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🎉 DAILY AUTOMATED AUDIT & RETRAIN COMPLETE!")

