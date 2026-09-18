#!/usr/bin/env python3
"""
Pre-download 150+ NSE Stock Daily CSV files for Pure Offline Engine Mode
"""
import os
import yfinance as yf
import pandas as pd
from datetime import datetime

APP_DIR = "/home/sendritika25/trading_ai"

NSE_UNIVERSE = [
    'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'SBIN', 'BHARTIARTL',
    'ITC', 'KOTAKBANK', 'LT', 'HINDUNILVR', 'AXISBANK', 'MARUTI', 'SUNPHARMA',
    'BAJFINANCE', 'TITAN', 'ULTRACEMCO', 'ASIANPAINT', 'TATAMOTORS', 'NTPC',
    'TATASTEEL', 'POWERGRID', 'M&M', 'ADANIENT', 'ADANIPORTS', 'COALINDIA',
    'BAJAJFINSV', 'ONGC', 'JSWSTEEL', 'DIVISLAB', 'DRREDDY', 'CIPLA',
    'GRASIM', 'BPCL', 'EICHERMOT', 'HEROMOTOCO', 'APOLLOHOSP', 'WIPRO',
    'NESTLEIND', 'BRITANNIA', 'HINDALCO', 'INDUSINDBK', 'TECHM', 'HCLTECH',
    'BAJAJ-AUTO', 'TATACONSUM', 'SHRIRAMFIN', 'SBILIFE', 'HDFCLIFE', 'LTIM',
    'DIXON', 'ZOMATO', 'PAYTM', 'TRENT', 'BEL', 'HAL', 'POLYCAB', 'HAVELLS',
    'PIDILITIND', 'SIEMENS', 'ABB', 'KPITTECH', 'TIMKEN', 'DLF', 'VBL',
    'TORNTPHARM', 'VEDL', 'IRCTC', 'PERSISTENT', 'BOSCHLTD', 'JIOFIN',
    'TATACOMM', 'CHOLAFIN', 'MUTHOOTFIN', 'PFC', 'RECLTD', 'SBICARD',
    'HDFCAMC', 'ICICIGI', 'ICICIPRULI', 'CANBK', 'BANKBARODA', 'PNB',
    'UNIONBANK', 'IDFCFIRSTB', 'FEDERALBNK', 'TVSMOTOR', 'BHARATFORG',
    'MOTHERSON', 'MRF', 'BALKRISIND', 'ASHOKLEY', 'APOLLOTYRE', 'EXIDEIND',
    'ADANIGREEN', 'ADANIPOWER', 'TATAPOWER', 'GAIL', 'NHPC', 'IEX', 'OIL',
    'NMDC', 'JINDALSTEL', 'SAIL', 'NATIONALUM', 'DABUR', 'MARICO',
    'GODREJCP', 'COLPAL', 'EMAMILTD', 'RADICO', 'UBL', 'LUPIN',
    'AUROPHARMA', 'ALKEM', 'ZYDUSLIFE', 'MAXHEALTH', 'BIOCON', 'SYNGENE',
    'GLENMARK', 'MANKIND', 'BHEL', 'CUMMINSIND', 'VOLTAS', 'CGPOWER',
    'ASTRAL', 'SUPREMEIND', 'KAYNES', 'MAZDOCK', 'DMART', 'NYKAA',
    'POLICYBZR', 'LODHA', 'GODREJPROP', 'OBEROIRLTY', 'PHOENIXLTD',
    'PRESTIGE', 'INDIGO', 'DELHIVERY', 'CONCOR', 'BLUEDART', 'BERGEPAINT',
    'SRF', 'PIIND', 'DEEPAKNTR', 'TATACHEM', 'GUJGASLTD', 'FLUOROCHEM',
    'COFORGE', 'TATAELXSI', 'LTTS', 'MPHASIS', 'OFSS', 'CYIENT'
]

print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 📥 DOWNLOADING LOCAL CSVS FOR 150+ NSE STOCKS...")

count = 0
for symbol in NSE_UNIVERSE:
    try:
        ticker = f"{symbol}.NS"
        df = yf.Ticker(ticker).history(period="2y").reset_index()
        if not df.empty and len(df) > 30:
            target_path = os.path.join(APP_DIR, f"{symbol}_Daily.csv")
            df.to_csv(target_path, index=False)
            count += 1
            if count % 20 == 0:
                print(f"Downloaded {count}/{len(NSE_UNIVERSE)} stock CSVs...")
    except Exception as e:
        continue

print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✓ SUCCESS: Pre-downloaded {count} stock CSVs for Offline Mode!")

