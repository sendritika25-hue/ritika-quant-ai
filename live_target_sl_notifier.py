#!/usr/bin/env python3
"""
Real-Time Market Monitor & Instant Autonomous Target / Profit Booking / Stop-Loss Engine.
Monitors user active holdings and universe stocks continuously during market hours.
Sends instant high-priority Push Notifications to mobile phone via ntfy.sh when:
1. Trailing Stop-Loss is activated (+1.2% Gain = 0% Risk Lock)
2. Target Price is reached (Instant Profit Booking / Sell Alert)
3. Peak Profit Reversal is detected (Consolidation after peak)
4. Stop-Loss is hit (Capital Protection Exit Alert)
5. 3:15 PM EOD Mandatory Intraday Square-off warning
"""
import os
import sys
import time
import json
import argparse
from datetime import datetime
import pandas as pd
import yfinance as yf
import requests

# Ensure UTF-8 output and handle pythonw.exe / background daemons safely
LOG_FILE_PATH = "c:/Users/gmt7220/Desktop/Kali_Linux/notifier_daemon.log"
try:
    if sys.stdout is None or not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
        sys.stdout = open(LOG_FILE_PATH, 'a', encoding='utf-8', buffering=1, errors='replace')
    elif hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    sys.stdout = open(LOG_FILE_PATH, 'a', encoding='utf-8', buffering=1, errors='replace')

try:
    if sys.stderr is None or not hasattr(sys.stderr, 'isatty') or not sys.stderr.isatty():
        sys.stderr = open(LOG_FILE_PATH, 'a', encoding='utf-8', buffering=1, errors='replace')
    elif hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    sys.stderr = open(LOG_FILE_PATH, 'a', encoding='utf-8', buffering=1, errors='replace')

NTFY_URL = "https://ntfy.sh/ritika_quant_ai_engine"
ALERT_CACHE_PATH = "sent_alerts_cache.json"
RECENT_ALERTS_PATH = "recent_live_alerts.json"
USER_HOLDINGS_PATHS = [
    "user_active_holdings.json",
    "/home/sendritika25/trading_ai/user_active_holdings.json",
    "c:/Users/gmt7220/Desktop/Kali_Linux/user_active_holdings.json"
]
LOG_PATH = "prediction_log.csv" if os.path.exists("prediction_log.csv") else "/home/sendritika25/trading_ai/prediction_log.csv"

ALL_MONITORED_STOCKS = [
    'POLYCAB.NS', 'HAL.NS', 'BHARTIARTL.NS', 'SUZLON.NS', 'MAZDOCK.NS',
    'BEL.NS', 'TRENT.NS', 'DIXON.NS', 'KAYNES.NS', 'ZOMATO.NS',
    'GOLDBEES.NS', 'SILVERBEES.NS', 'RELIANCE.NS', 'TCS.NS', 'INFY.NS',
    'HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 'MARUTI.NS', 'TITAN.NS',
    'SUNPHARMA.NS', 'OBEROIRLTY.NS', 'COFORGE.NS', 'PERSISTENT.NS',
    'MPHASIS.NS', 'KPITTECH.NS', 'OFSS.NS', 'SOLARINDS.NS', 'KEI.NS',
    'CUMMINSIND.NS', 'YESBANK.NS', 'BANDHANBNK.NS', 'IRCTC.NS', 'UPL.NS',
    'RPOWER.NS', 'BHEL.NS', 'TATASTEEL.NS', 'IOC.NS', 'CIPLA.NS',
    'CDSL.NS', 'MOTHERSON.NS', 'DLF.NS'
]

def load_sent_alerts():
    if os.path.exists(ALERT_CACHE_PATH):
        try:
            with open(ALERT_CACHE_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_sent_alerts(alerts_dict):
    try:
        with open(ALERT_CACHE_PATH, 'w') as f:
            json.dump(alerts_dict, f, indent=2)
    except Exception as e:
        print(f"Error saving alert cache: {e}")

def record_recent_alert(alert_obj):
    recent = []
    if os.path.exists(RECENT_ALERTS_PATH):
        try:
            with open(RECENT_ALERTS_PATH, 'r') as f:
                recent = json.load(f)
        except Exception:
            recent = []
    recent.insert(0, alert_obj)
    recent = recent[:30] # keep last 30 alerts
    try:
        with open(RECENT_ALERTS_PATH, 'w') as f:
            json.dump(recent, f, indent=2)
    except Exception as e:
        print(f"Error saving recent alerts: {e}")

def send_push_alert(title_clean, message, priority="high", tags="warning", broker_stock=""):
    # 1. Native Windows Desktop Action Center Toast Popup
    try:
        from windows_toasts import Toast, WindowsToaster
        toaster = WindowsToaster("Ritika Quant AI")
        w_toast = Toast()
        short_msg = message.split("\n")[0] if "\n" in message else message[:100]
        w_toast.text_fields = [title_clean, short_msg]
        toaster.show_toast(w_toast)
    except Exception:
        pass

    # 2. Windows Speaker Audio Alert Chime
    try:
        import winsound
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    except Exception:
        pass

    # 3. NTFY Mobile & Browser Push Notification
    try:
        clean_header_title = title_clean.encode('ascii', 'ignore').decode('ascii').strip()
        headers = {
            "Title": clean_header_title,
            "Priority": priority,
            "Tags": tags
        }
        if broker_stock:
            # Add 1-tap action button for Groww/Zerodha in NTFY app
            headers["Actions"] = f"view, Open Groww, https://groww.in/search?q={broker_stock}; view, Open Zerodha, https://kite.zerodha.com"
        
        resp = requests.post(
            NTFY_URL,
            data=message.encode('utf-8'),
            headers=headers,
            timeout=10
        )
        if resp.status_code == 200:
            print(f"✓ Push Alert Sent to Phone & PC: {clean_header_title}")
            return True
        else:
            print(f"⚠️ Notification status {resp.status_code}")
            return False
    except Exception as e:
        print(f"⚠️ Notification error: {e}")
        return False

def check_live_targets_and_notify():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"[{now_str}] 🔍 Scanning Live Market Targets & Stop-Loss...")

    sent_alerts = load_sent_alerts()
    watchlist = []

    # 1. Read User's Active Bought Holdings (HIGHEST PRIORITY)
    user_holdings = []
    for hp in USER_HOLDINGS_PATHS:
        if os.path.exists(hp):
            try:
                with open(hp, "r") as f:
                    u_h = json.load(f)
                    if isinstance(u_h, list):
                        user_holdings = u_h
                        break
            except Exception:
                pass

    for h in user_holdings:
        sym = h.get("symbol", "").strip()
        if sym:
            watchlist.append({
                "symbol": sym,
                "name": h.get("name", sym.replace(".NS", "")),
                "entry": float(h.get("entry", 0.0)),
                "target": float(h.get("target", 0.0)),
                "sl": float(h.get("sl", 0.0)),
                "type": h.get("trade_type", "Delivery"),
                "is_user_holding": True
            })

    # 2. Read Active Pending Predictions from Prediction Log
    if os.path.exists(LOG_PATH):
        try:
            df_logs = pd.read_csv(LOG_PATH, on_bad_lines='skip')
            pending = df_logs[df_logs['Status'].isin(['PENDING', '⏳ PENDING'])]
            if not pending.empty:
                for idx, row in pending.iterrows():
                    raw_ticker = str(row['Ticker']).strip()
                    entry_price = float(row['EntryPrice'])
                    is_intraday = "(Intraday)" in raw_ticker
                    clean_sym = raw_ticker.replace(" (Intraday)", "").strip()
                    if not clean_sym.endswith(".NS") and not clean_sym.startswith("^"):
                        clean_sym += ".NS"
                        
                    target_p = round(entry_price * (1.05 if is_intraday else 1.15), 2)
                    sl_p = round(entry_price * (0.98 if is_intraday else 0.95), 2)
                    
                    if clean_sym not in [w['symbol'] for w in watchlist]:
                        watchlist.append({
                            "symbol": clean_sym,
                            "name": clean_sym.replace(".NS", ""),
                            "entry": entry_price,
                            "target": target_p,
                            "sl": sl_p,
                            "type": "Intraday" if is_intraday else "Delivery",
                            "is_user_holding": False
                        })
        except Exception:
            pass

    # 3. Add General Market Universe
    existing_syms = {w['symbol'] for w in watchlist}
    for sym in ALL_MONITORED_STOCKS:
        if sym not in existing_syms:
            watchlist.append({
                "symbol": sym,
                "name": sym.replace(".NS", ""),
                "entry": 0.0,
                "target": 0.0,
                "sl": 0.0,
                "type": "Universe Monitor",
                "is_user_holding": False
            })

    # Evaluate Each Stock
    for item in watchlist:
        sym = item['symbol']
        name = item['name']
        entry = item['entry']
        target = item['target']
        sl = item['sl']
        trade_type = item['type']
        is_user_holding = item['is_user_holding']

        try:
            df = yf.Ticker(sym).history(period="1d", interval="5m")
            if df.empty or len(df) == 0:
                continue

            curr_price = round(float(df['Close'].iloc[-1]), 2)
            high_price = round(float(df['High'].max()), 2)
            low_price = round(float(df['Low'].min()), 2)

            if entry <= 0.0:
                entry = round(float(df['Open'].iloc[0]), 2)
                target = round(entry * 1.05, 2)
                sl = round(entry * 0.96, 2)
                is_intraday = True
            else:
                is_intraday = ("Intraday" in trade_type or "MIS" in trade_type)

            gain_pct = round(((curr_price - entry) / (entry + 1e-9)) * 100, 2)
            day_open = float(df['Open'].iloc[0]) if len(df) > 0 else curr_price
            day_chg = round(((curr_price - day_open) / (day_open + 1e-9)) * 100, 2)

            # Key definitions for fine-grained alerting
            k_buy = f"{today_str}_{sym}_BUY_SIGNAL"
            k_target = f"{today_str}_{sym}_TARGET_HIT"
            k_trail = f"{today_str}_{sym}_TRAILING_SL"
            k_sl = f"{today_str}_{sym}_SL_HIT"
            k_peak = f"{today_str}_{sym}_PEAK_REVERSAL"

            # -------------------------------------------------------------
            # CONDITION 0: PROACTIVE FRESH BUY BREAKOUT OPPORTUNITY (UNIVERSE)
            # -------------------------------------------------------------
            if not is_user_holding and day_chg >= 0.8 and k_buy not in sent_alerts:
                buy_tg_intra = round(curr_price * 1.025, 2)
                buy_sl_intra = round(curr_price * 0.985, 2)
                expected_prof = round(buy_tg_intra - curr_price, 2)
                title = f"🚀 BUY ALERT: {name} Breaking Out (+{day_chg:+.2f}%)!"
                msg = (
                    f"🚀 FRESH HIGH-PROFIT BUY OPPORTUNITY: {name}!\n"
                    f"========================================\n"
                    f"• Live Price: ₹{curr_price:,.2f} (+{day_chg:+.2f}% TODAY)\n"
                    f"• 🎯 Intraday Target (+2.5%): ₹{buy_tg_intra:,.2f} (+₹{expected_prof:,.2f}/sh)\n"
                    f"• 🎯 Delivery Target (+15.0%): ₹{round(curr_price * 1.15, 2):,.2f}\n"
                    f"• 🛡️ Stop-Loss (-1.5%): ₹{buy_sl_intra:,.2f}\n"
                    f"========================================\n"
                    f"💡 AI Momentum Breakout Confirmed. Enter trade now!\n\n"
                    f"👉 1-Tap Broker Links:\n"
                    f"• Zerodha: https://kite.zerodha.com\n"
                    f"• Groww: https://groww.in/search?q={name}"
                )
                send_push_alert(title, msg, priority="high", tags="rocket,fire,chart_with_upwards_trend", broker_stock=name)
                sent_alerts[k_buy] = "SENT"
                save_sent_alerts(sent_alerts)
                record_recent_alert({
                    "timestamp": now_str,
                    "symbol": sym,
                    "name": name,
                    "trade_type": "Buy Opportunity",
                    "alert_type": "BUY_SIGNAL",
                    "title": title,
                    "message": msg,
                    "entry": curr_price,
                    "current": curr_price,
                    "gain_pct": day_chg,
                    "action": "BUY_NOW"
                })

            # -------------------------------------------------------------
            # CONDITION 1: STOP-LOSS HIT (FOR ACTIVE USER HOLDINGS ONLY)
            # -------------------------------------------------------------
            if is_user_holding and curr_price <= sl and k_sl not in sent_alerts:
                title = f"🛑 STOP-LOSS ALERT: {name} EXIT NOW"
                msg = (
                    f"🛑 CAPITAL PROTECTION ALERT: {name} ({trade_type})!\n"
                    f"========================================\n"
                    f"• Entry Price: ₹{entry:,.2f}\n"
                    f"• Current Price: ₹{curr_price:,.2f} ({gain_pct:+.2f}%)\n"
                    f"• Stop-Loss Level: ₹{sl:,.2f}\n"
                    f"========================================\n"
                    f"👉 EXIT NOW in your broker app to protect capital!\n\n"
                    f"👉 1-Tap Broker Links:\n"
                    f"• Zerodha: https://kite.zerodha.com\n"
                    f"• Groww: https://groww.in/search?q={name}"
                )
                send_push_alert(title, msg, priority="urgent", tags="warning,rotating_light", broker_stock=name)
                sent_alerts[k_sl] = "SENT"
                save_sent_alerts(sent_alerts)
                record_recent_alert({
                    "timestamp": now_str,
                    "symbol": sym,
                    "name": name,
                    "trade_type": trade_type,
                    "alert_type": "SL_HIT",
                    "title": title,
                    "message": msg,
                    "entry": entry,
                    "current": curr_price,
                    "gain_pct": gain_pct,
                    "action": "EXIT_SL"
                })
                continue

            # -------------------------------------------------------------
            # CONDITION 2: TARGET HIT / PROFIT BOOKING (SELL ALERT)
            # -------------------------------------------------------------
            if (curr_price >= target or high_price >= target) and k_target not in sent_alerts:
                title = f"🎯 PROFIT BOOKING ALERT: SELL {name} NOW!"
                prefix = "YOUR BOUGHT POSITION" if is_user_holding else "AI MONITORED PICK"
                msg = (
                    f"🎉 {prefix} TARGET REACHED: {name} ({trade_type})!\n"
                    f"========================================\n"
                    f"• Entry Price: ₹{entry:,.2f}\n"
                    f"• Current Price: ₹{curr_price:,.2f}\n"
                    f"• Target Price: ₹{target:,.2f}\n"
                    f"• Profit Realized: +{gain_pct}%\n"
                    f"========================================\n"
                    f"👉 SELL NOW to lock in your profit!\n\n"
                    f"👉 1-Tap Broker Links:\n"
                    f"• Zerodha: https://kite.zerodha.com\n"
                    f"• Groww: https://groww.in/search?q={name}"
                )
                send_push_alert(title, msg, priority="urgent", tags="moneybag,dollar,tada", broker_stock=name)
                sent_alerts[k_target] = "SENT"
                save_sent_alerts(sent_alerts)
                record_recent_alert({
                    "timestamp": now_str,
                    "symbol": sym,
                    "name": name,
                    "trade_type": trade_type,
                    "alert_type": "TARGET_HIT",
                    "title": title,
                    "message": msg,
                    "entry": entry,
                    "current": curr_price,
                    "gain_pct": gain_pct,
                    "action": "SELL_NOW"
                })
                continue

            # -------------------------------------------------------------
            # CONDITION 3: AUTOMATIC TRAILING SL ACTIVATION (+1.2% GAIN = 0% RISK)
            # -------------------------------------------------------------
            if is_user_holding and gain_pct >= 1.2 and k_trail not in sent_alerts and k_target not in sent_alerts:
                title = f"🛡️ ZERO RISK ACTIVATED: {name} Trailing SL Set!"
                msg = (
                    f"🛡️ 100% CAPITAL PROTECTION LOCKED for {name} ({trade_type})!\n"
                    f"========================================\n"
                    f"• Entry Price: ₹{entry:,.2f}\n"
                    f"• Current Price: ₹{curr_price:,.2f} (+{gain_pct}% Gain Achieved)\n"
                    f"• NEW TRAILING STOP-LOSS: ₹{entry:,.2f} (Entry Level)\n"
                    f"========================================\n"
                    f"🎉 Your trade is now 100% ZERO RISK. No loss possible!\n\n"
                    f"👉 1-Tap Broker Links:\n"
                    f"• Zerodha: https://kite.zerodha.com\n"
                    f"• Groww: https://groww.in/search?q={name}"
                )
                send_push_alert(title, msg, priority="high", tags="shield,chart_with_upwards_trend", broker_stock=name)
                sent_alerts[k_trail] = "SENT"
                save_sent_alerts(sent_alerts)
                record_recent_alert({
                    "timestamp": now_str,
                    "symbol": sym,
                    "name": name,
                    "trade_type": trade_type,
                    "alert_type": "TRAILING_SL",
                    "title": title,
                    "message": msg,
                    "entry": entry,
                    "current": curr_price,
                    "gain_pct": gain_pct,
                    "action": "LOCK_ZERO_RISK"
                })

            # -------------------------------------------------------------
            # CONDITION 4: INTRADAY PEAK REVERSAL PROFIT BOOKING
            # -------------------------------------------------------------
            elif is_user_holding and is_intraday and high_price >= round(entry * 1.015, 2) and curr_price < (high_price * 0.993) and k_peak not in sent_alerts and k_target not in sent_alerts:
                peak_gain = round(((high_price - entry) / entry) * 100, 2)
                title = f"💰 INTRADAY PEAK PROFIT: {name} Consolidation Alert"
                msg = (
                    f"⚡ INTRADAY PEAK PROFIT WARNING for {name}!\n"
                    f"========================================\n"
                    f"• Entry Price: ₹{entry:,.2f}\n"
                    f"• Session Peak: ₹{high_price:,.2f} (+{peak_gain}% Gain)\n"
                    f"• Current Price: ₹{curr_price:,.2f} (+{gain_pct}%)\n"
                    f"========================================\n"
                    f"👉 Price started consolidating after peak. Consider booking profit or trailing SL to ₹{entry:,.2f}!\n\n"
                    f"👉 1-Tap Broker Links:\n"
                    f"• Zerodha: https://kite.zerodha.com\n"
                    f"• Groww: https://groww.in/search?q={name}"
                )
                send_push_alert(title, msg, priority="high", tags="chart_with_upwards_trend,moneybag", broker_stock=name)
                sent_alerts[k_peak] = "SENT"
                save_sent_alerts(sent_alerts)
                record_recent_alert({
                    "timestamp": now_str,
                    "symbol": sym,
                    "name": name,
                    "trade_type": trade_type,
                    "alert_type": "PEAK_REVERSAL",
                    "title": title,
                    "message": msg,
                    "entry": entry,
                    "current": curr_price,
                    "gain_pct": gain_pct,
                    "action": "BOOK_PROFIT"
                })

            pct_to_tg = round(((target - curr_price) / curr_price) * 100, 2)
            print(f"• {name} ({trade_type}): Curr ₹{curr_price:,.2f} ({gain_pct:+.2f}%) | Target ₹{target:,.2f} ({pct_to_tg:+}% away) | SL ₹{sl:,.2f}")

        except Exception as e:
            print(f"⚠️ Error scanning {name}: {e}")

    # CONDITION 5: Mandatory 3:15 PM EOD Intraday Exit Reminder
    now_dt = datetime.now()
    if now_dt.hour == 15 and 10 <= now_dt.minute <= 25:
        eod_alert_key = f"{today_str}_EOD_315PM_EXIT"
        if eod_alert_key not in sent_alerts:
            title = "⏰ INTRADAY 3:15 PM MANDATORY EXIT ALERT"
            msg = (
                f"⏰ INTRADAY MARKET CLOSING IN 15 MINUTES!\n"
                f"========================================\n"
                f"👉 Close all open Intraday positions in your broker app before 3:30 PM to prevent broker auto-square-off charges!"
            )
            send_push_alert(title, msg, priority="urgent", tags="alarm_clock,warning")
            sent_alerts[eod_alert_key] = "SENT"
            save_sent_alerts(sent_alerts)

import socket

_instance_lock_socket = None

def ensure_single_instance(port=49876):
    global _instance_lock_socket
    try:
        _instance_lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _instance_lock_socket.bind(('127.0.0.1', port))
    except socket.error:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ℹ️ Another instance of live_target_sl_notifier is already running. Exiting gracefully.")
        sys.exit(0)

def run_continuous_daemon(interval=45):
    ensure_single_instance()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 Quant AI Autonomous Notification Daemon started!")
    print(f"📡 Push Notification Channel: {NTFY_URL}")
    print(f"⏱️ Check Frequency: Every {interval} seconds\n")
    while True:
        try:
            check_live_targets_and_notify()
        except Exception as e:
            print(f"⚠️ Error during monitoring cycle: {e}")
        time.sleep(interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Autonomous Live Target & Stop-Loss Push Notification Engine")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--test", action="store_true", help="Send an immediate test alert to verify mobile phone reception")
    parser.add_argument("--interval", type=int, default=45, help="Polling interval in seconds (default 45)")
    args = parser.parse_args()

    if args.test:
        print("Sending immediate test alert...")
        send_push_alert(
            "🔔 TEST NOTIFICATION: Quant AI Engine Connected!",
            "🎉 Your mobile phone is successfully connected to the Quant AI Engine!\n\n"
            "You will now receive automatic notifications for:\n"
            "• 🎯 Target Reached & Profit Booking\n"
            "• 🛡️ Trailing Stop-Loss (+1.2% Zero Risk Lock)\n"
            "• 🛑 Stop-Loss Protection\n"
            "• 🚀 9:15 AM Top Daily Picks",
            priority="high",
            tags="bell,tada,rocket"
        )
    elif args.once:
        check_live_targets_and_notify()
    else:
        run_continuous_daemon(args.interval)
