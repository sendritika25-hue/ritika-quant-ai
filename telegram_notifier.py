#!/usr/bin/env python3
"""
Ritika Quant AI - Telegram Notification Module
Sends real-time high-conviction trading alerts, Target Hits, Stop-Loss Triggers,
Trailing SL locks, and Morning Breakout Picks directly to Telegram.
"""
import os
import json
import requests
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "telegram_config.json")

def get_telegram_config():
    """Retrieve saved Telegram Bot Token and Chat/Channel ID."""
    config = {
        "bot_token": os.environ.get("TELEGRAM_BOT_TOKEN", "").strip(),
        "chat_id": os.environ.get("TELEGRAM_CHAT_ID", "").strip(),
        "enabled": True
    }
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if saved.get("bot_token"):
                    config["bot_token"] = saved.get("bot_token").strip()
                if saved.get("chat_id"):
                    config["chat_id"] = str(saved.get("chat_id")).strip()
                if "enabled" in saved:
                    config["enabled"] = bool(saved.get("enabled"))
        except Exception:
            pass
    return config

def save_telegram_config(bot_token: str, chat_id: str, enabled: bool = True):
    """Save Telegram credentials to local config."""
    data = {
        "bot_token": bot_token.strip(),
        "chat_id": str(chat_id).strip(),
        "enabled": bool(enabled),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving telegram config: {e}")
        return False

def test_telegram_connection(bot_token: str, chat_id: str) -> tuple[bool, str]:
    """Test connection with Telegram API using provided token and chat ID."""
    if not bot_token or not chat_id:
        return False, "Bot Token and Chat ID cannot be empty."

    url = f"https://api.telegram.org/bot{bot_token.strip()}/sendMessage"
    payload = {
        "chat_id": str(chat_id).strip(),
        "text": (
            "🚀 <b>Ritika Quant AI • Telegram Connected!</b>\n\n"
            "✅ <i>Congratulations!</i> Your 24x7 Real-Time Trading Alert Engine is now connected to Telegram.\n\n"
            "🔔 You will now receive instant push alerts for:\n"
            "• 🎯 Target Hit & Profit Booking\n"
            "• 🛑 Stop-Loss Protection\n"
            "• 🛡️ Trailing SL (0% Risk Locks)\n"
            "• ⚡ Intraday & Delivery Morning Breakouts\n\n"
            f"⏰ <b>Verified at:</b> {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}"
        ),
        "parse_mode": "HTML"
    }

    try:
        resp = requests.post(url, json=payload, timeout=12)
        res_data = resp.json()
        if resp.status_code == 200 and res_data.get("ok"):
            return True, "Success! Test alert sent to Telegram."
        else:
            err_desc = res_data.get("description", "Unknown Telegram error")
            return False, f"Telegram Error: {err_desc}"
    except Exception as e:
        return False, f"Network error connecting to Telegram: {str(e)}"

def send_telegram_alert(title: str, message: str, broker_stock: str = "") -> bool:
    """Send formatted alert to Telegram."""
    cfg = get_telegram_config()
    bot_token = cfg.get("bot_token")
    chat_id = cfg.get("chat_id")
    enabled = cfg.get("enabled", True)

    if not enabled or not bot_token or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    # Format header emoji and clean text
    clean_stock = broker_stock.replace(".NS", "").replace(".BO", "").strip() if broker_stock else ""
    
    html_text = f"<b>{title}</b>\n\n"
    # Format message lines
    for line in message.split("\n"):
        line_clean = line.strip()
        if not line_clean:
            continue
        if any(line_clean.startswith(x) for x in ["•", "-", "Stock:", "Action:", "Price:", "Target:", "SL:", "Profit:"]):
            html_text += f"{line_clean}\n"
        else:
            html_text += f"{line_clean}\n"

    html_text += f"\n⏰ <i>{datetime.now().strftime('%I:%M:%S %p • %d %b %Y')}</i>"

    payload = {
        "chat_id": chat_id,
        "text": html_text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    # Add 1-tap broker action buttons if stock symbol is present
    if clean_stock:
        payload["reply_markup"] = {
            "inline_keyboard": [
                [
                    {"text": f"📈 Open {clean_stock} on Groww", "url": f"https://groww.in/search?q={clean_stock}"},
                    {"text": "🪁 Open Zerodha Kite", "url": "https://kite.zerodha.com"}
                ]
            ]
        }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200 and resp.json().get("ok"):
            print(f"✓ Telegram Alert Sent: {title}")
            return True
        else:
            print(f"⚠️ Telegram send failed: {resp.text}")
            return False
    except Exception as e:
        print(f"⚠️ Telegram request exception: {e}")
        return False

if __name__ == "__main__":
    cfg = get_telegram_config()
    print("Telegram Config:", cfg)
