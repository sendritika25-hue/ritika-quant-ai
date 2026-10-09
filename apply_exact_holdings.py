import json
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "trading_platform.db")
JSON_PATH = os.path.join(BASE_DIR, "user_active_holdings.json")
PAPER_PATH = os.path.join(BASE_DIR, "paper_positions.json")

# Complete list of user's active holdings with exact user quantities
active_holdings = [
    {
        "symbol": "SOLARINDS.NS",
        "name": "SOLARINDS",
        "shares": 1,
        "entry": 19800.0,
        "target": 22770.0,
        "sl": 18810.0,
        "trade_type": "Delivery",
        "buy_time": "2026-09-24 07:37",
        "status": "ACTIVE"
    },
    {
        "symbol": "COFORGE.NS",
        "name": "COFORGE",
        "shares": 3,
        "entry": 1796.4,
        "target": 2065.86,
        "sl": 1706.58,
        "trade_type": "Delivery",
        "buy_time": "2026-09-24 07:37",
        "status": "ACTIVE"
    },
    {
        "symbol": "ICICIBANK.NS",
        "name": "ICICIBANK",
        "shares": 4,
        "entry": 1334.2,
        "target": 1561.01,
        "sl": 1267.49,
        "trade_type": "Delivery",
        "buy_time": "2026-09-24 07:38",
        "status": "ACTIVE"
    },
    {
        "symbol": "TCS.NS",
        "name": "TCS",
        "shares": 4,
        "entry": 2154.7,
        "target": 2208.57,
        "sl": 2122.38,
        "trade_type": "Intraday",
        "buy_time": "2026-10-09 12:01",
        "status": "ACTIVE"
    },
    {
        "symbol": "BHARTIARTL.NS",
        "name": "BHARTIARTL",
        "shares": 11,
        "entry": 1807.2,
        "target": 1852.38,
        "sl": 1780.09,
        "trade_type": "Intraday",
        "buy_time": "2026-10-09 12:01",
        "status": "ACTIVE"
    },
    {
        "symbol": "CDSL.NS",
        "name": "CDSL",
        "shares": 15,
        "entry": 1256.2,
        "target": 1287.61,
        "sl": 1237.36,
        "trade_type": "Intraday",
        "buy_time": "2026-10-09 12:01",
        "status": "ACTIVE"
    },
    {
        "symbol": "BDL.NS",
        "name": "BDL",
        "shares": 18,
        "entry": 1072.5,
        "target": 1099.31,
        "sl": 1056.41,
        "trade_type": "Intraday",
        "buy_time": "2026-10-09 12:01",
        "status": "ACTIVE"
    }
]

# 1. Update user_active_holdings.json
with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(active_holdings, f, indent=2)
print("1. Updated user_active_holdings.json with exact quantities!")

# 2. Update SQLite database for user ritika
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Ensure shares column exists in user_holdings table
try:
    cursor.execute("ALTER TABLE user_holdings ADD COLUMN shares INTEGER DEFAULT 1")
except Exception:
    pass

cursor.execute("SELECT id FROM users WHERE username = 'ritika'")
user_row = cursor.fetchone()
if user_row:
    u_id = user_row[0]
    # Delete old records for ritika and re-insert fresh with exact shares
    cursor.execute("DELETE FROM user_holdings WHERE user_id = ?", (u_id,))
    for h in active_holdings:
        cursor.execute("""
            INSERT INTO user_holdings (user_id, symbol, name, entry, target, sl, shares, trade_type, buy_time, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            u_id,
            h["symbol"],
            h["name"],
            h["entry"],
            h["target"],
            h["sl"],
            h["shares"],
            h["trade_type"],
            h["buy_time"],
            h["status"]
        ))
    conn.commit()
    print("2. Updated SQLite database for user ritika with exact quantities!")

conn.close()

# 3. Update paper_positions.json
paper_data = {
    "cash": 45000.00,
    "realized_profit": 1622.51,
    "positions": [
        {
            "Ticker": "SOLARINDS.NS",
            "Type": "DELIVERY (CNC)",
            "BuyPrice": 19800.0,
            "Shares": 1,
            "AITarget": 22770.0,
            "AIScore": "88% (High Conviction)",
            "BuyTime": "2026-09-24 07:37"
        },
        {
            "Ticker": "COFORGE.NS",
            "Type": "DELIVERY (CNC)",
            "BuyPrice": 1796.4,
            "Shares": 3,
            "AITarget": 2065.86,
            "AIScore": "89% (High Conviction)",
            "BuyTime": "2026-09-24 07:37"
        },
        {
            "Ticker": "ICICIBANK.NS",
            "Type": "DELIVERY (CNC)",
            "BuyPrice": 1334.2,
            "Shares": 4,
            "AITarget": 1561.01,
            "AIScore": "86% (Banking Breakout)",
            "BuyTime": "2026-09-24 07:38"
        },
        {
            "Ticker": "TCS.NS",
            "Type": "INTRADAY (MIS)",
            "BuyPrice": 2154.7,
            "Shares": 4,
            "AITarget": 2208.57,
            "AIScore": "93% (IT Breakout)",
            "BuyTime": "2026-10-09 12:01"
        },
        {
            "Ticker": "BHARTIARTL.NS",
            "Type": "INTRADAY (MIS)",
            "BuyPrice": 1807.2,
            "Shares": 11,
            "AITarget": 1852.38,
            "AIScore": "91% (Telecom Surge)",
            "BuyTime": "2026-10-09 12:01"
        },
        {
            "Ticker": "CDSL.NS",
            "Type": "INTRADAY (MIS)",
            "BuyPrice": 1256.2,
            "Shares": 15,
            "AITarget": 1287.61,
            "AIScore": "89% (Capital Market Surge)",
            "BuyTime": "2026-10-09 12:01"
        },
        {
            "Ticker": "BDL.NS",
            "Type": "INTRADAY (MIS)",
            "BuyPrice": 1072.5,
            "Shares": 18,
            "AITarget": 1099.31,
            "AIScore": "88% (Defence Breakout)",
            "BuyTime": "2026-10-09 12:01"
        }
    ]
}

with open(PAPER_PATH, "w", encoding="utf-8") as f:
    json.dump(paper_data, f, indent=2)
print("3. Updated paper_positions.json with exact quantities!")
