#!/usr/bin/env python3
"""
Ritika Quant AI - Multi-User Secure Database & Authentication Engine.
Manages users, authentication, private portfolios, paper trading accounts,
and admin controls using robust SQLite database.
"""
import os
import json
import sqlite3
import hashlib
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "trading_platform.db")
USER_HOLDINGS_JSON = os.path.join(BASE_DIR, "user_active_holdings.json")

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = "ritika_quant_salt_2026"
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables and seed default admin and existing holdings."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            plan TEXT DEFAULT 'FREE_UNLIMITED',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    """)

    # 2. User Holdings table (Private per-user portfolios)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_holdings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            name TEXT,
            entry REAL NOT NULL,
            target REAL NOT NULL,
            sl REAL NOT NULL,
            shares INTEGER DEFAULT 1,
            trade_type TEXT DEFAULT 'Delivery',
            buy_time TEXT,
            status TEXT DEFAULT 'ACTIVE',
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)
    try:
        cursor.execute("ALTER TABLE user_holdings ADD COLUMN shares INTEGER DEFAULT 1")
    except Exception:
        pass

    # 3. User Paper Accounts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_paper_accounts (
            user_id INTEGER PRIMARY KEY,
            cash REAL DEFAULT 100000.0,
            realized_profit REAL DEFAULT 0.0,
            positions_json TEXT DEFAULT '[]',
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    conn.commit()

    # Seed Default Admin (Ritika)
    cursor.execute("SELECT id FROM users WHERE username = 'ritika'")
    admin_row = cursor.fetchone()
    if not admin_row:
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role, plan)
            VALUES (?, ?, ?, ?, ?)
        """, ('ritika', 'sendritika25@gmail.com', hash_password('ritika7220'), 'admin', 'MASTER_ADMIN'))
        conn.commit()
        cursor.execute("SELECT id FROM users WHERE username = 'ritika'")
        admin_row = cursor.fetchone()

    admin_id = admin_row['id']

    # Also seed other demo accounts from previous valid credentials for smooth continuity
    demo_creds = {
        'admin': ('admin@quant.ai', 'admin123', 'admin'),
        'trader': ('trader@quant.ai', 'quant786', 'user'),
        'user': ('user@quant.ai', 'quant123', 'user')
    }
    for u_name, (u_email, u_pw, u_role) in demo_creds.items():
        cursor.execute("SELECT id FROM users WHERE username = ?", (u_name,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role, plan)
                VALUES (?, ?, ?, ?, ?)
            """, (u_name, u_email, hash_password(u_pw), u_role, 'FREE_UNLIMITED'))
    conn.commit()

    # Migrate existing holdings from user_active_holdings.json into Ritika's admin holdings
    cursor.execute("SELECT COUNT(*) as cnt FROM user_holdings WHERE user_id = ?", (admin_id,))
    if cursor.fetchone()['cnt'] == 0 and os.path.exists(USER_HOLDINGS_JSON):
        try:
            with open(USER_HOLDINGS_JSON, "r", encoding="utf-8") as f:
                h_list = json.load(f)
                if isinstance(h_list, list):
                    for h in h_list:
                        if isinstance(h, dict) and h.get("symbol"):
                            cursor.execute("""
                                INSERT INTO user_holdings (user_id, symbol, name, entry, target, sl, trade_type, buy_time, status)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                admin_id,
                                h.get("symbol"),
                                h.get("name", h.get("symbol", "").replace(".NS", "")),
                                float(h.get("entry", 0.0)),
                                float(h.get("target", 0.0)),
                                float(h.get("sl", 0.0)),
                                h.get("trade_type", "Delivery"),
                                h.get("buy_time", datetime.now().strftime("%Y-%m-%d %H:%M")),
                                h.get("status", "ACTIVE")
                            ))
                    conn.commit()
        except Exception:
            pass

    conn.close()

def register_user(username: str, email: str, password: str) -> tuple[bool, str]:
    """Register a new free user. Returns (success, message)."""
    username = username.strip().lower()
    email = email.strip().lower() if email else f"{username}@quant.ai"
    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters long."
    if not password or len(password) < 4:
        return False, "Password must be at least 4 characters long."

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            return False, "Username already exists. Please choose another username."

        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role, plan)
            VALUES (?, ?, ?, 'user', 'FREE_UNLIMITED')
        """, (username, email, hash_password(password)))
        new_id = cursor.lastrowid

        # Initialize paper trading account with 1,00,000 virtual cash
        cursor.execute("""
            INSERT INTO user_paper_accounts (user_id, cash, realized_profit, positions_json)
            VALUES (?, 100000.0, 0.0, '[]')
        """, (new_id,))

        conn.commit()
        conn.close()
        return True, "Account created successfully! You can now log in."
    except Exception as e:
        conn.close()
        return False, f"Registration failed: {e}"

def authenticate_user(username_or_email: str, password: str) -> dict | None:
    """Authenticate user with username or email and password."""
    clean_identifier = username_or_email.strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM users
        WHERE (username = ? OR email = ?) AND is_active = 1
    """, (clean_identifier, clean_identifier))
    user = cursor.fetchone()
    conn.close()

    if user and user['password_hash'] == hash_password(password.strip()):
        return dict(user)
    return None

def get_user_by_id(user_id: int) -> dict | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_holdings(user_id: int) -> list:
    """Get active holdings for a specific user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT symbol, name, entry, target, sl, shares, trade_type, buy_time, status
        FROM user_holdings
        WHERE user_id = ? AND status = 'ACTIVE'
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_user_holding(user_id: int, holding: dict):
    """Save or update a holding for a specific user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sym = holding.get("symbol", "").strip()
    shares_cnt = int(holding.get("shares", 1))
    cursor.execute("SELECT id FROM user_holdings WHERE user_id = ? AND symbol = ?", (user_id, sym))
    existing = cursor.fetchone()
    if existing:
        cursor.execute("""
            UPDATE user_holdings
            SET name = ?, entry = ?, target = ?, sl = ?, shares = ?, trade_type = ?, buy_time = ?, status = 'ACTIVE'
            WHERE id = ?
        """, (
            holding.get("name", sym.replace(".NS", "")),
            float(holding.get("entry", 0.0)),
            float(holding.get("target", 0.0)),
            float(holding.get("sl", 0.0)),
            shares_cnt,
            holding.get("trade_type", "Delivery"),
            holding.get("buy_time", datetime.now().strftime("%Y-%m-%d %H:%M")),
            existing['id']
        ))
    else:
        cursor.execute("""
            INSERT INTO user_holdings (user_id, symbol, name, entry, target, sl, shares, trade_type, buy_time, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE')
        """, (
            user_id,
            sym,
            holding.get("name", sym.replace(".NS", "")),
            float(holding.get("entry", 0.0)),
            float(holding.get("target", 0.0)),
            float(holding.get("sl", 0.0)),
            shares_cnt,
            holding.get("trade_type", "Delivery"),
            holding.get("buy_time", datetime.now().strftime("%Y-%m-%d %H:%M"))
        ))
    conn.commit()
    conn.close()
    _sync_all_active_holdings_to_json()

def remove_user_holding(user_id: int, symbol: str):
    """Remove a holding for a specific user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_holdings WHERE user_id = ? AND symbol = ?", (user_id, symbol.strip()))
    conn.commit()
    conn.close()
    _sync_all_active_holdings_to_json()

def _sync_all_active_holdings_to_json():
    """Sync all active holdings to user_active_holdings.json so notifier stays updated."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT symbol, name, entry, target, sl, shares, trade_type, buy_time, status FROM user_holdings WHERE status = 'ACTIVE'")
        rows = cursor.fetchall()
        conn.close()
        holdings = [dict(r) for r in rows]
        with open(USER_HOLDINGS_JSON, "w", encoding="utf-8") as f:
            json.dump(holdings, f, indent=2)
    except Exception:
        pass

def get_all_users() -> list:
    """Admin function: List all registered users."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, role, plan, created_at, is_active FROM users ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Initialize database on module import
init_db()
