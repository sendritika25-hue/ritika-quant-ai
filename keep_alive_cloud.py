#!/usr/bin/env python3
"""
Cloud Keep-Alive Engine:
Sends regular HTTP keep-alive pings to cloud services (Streamlit Cloud, Render, etc.)
so they never enter idle sleep mode, keeping background market alerting active 24/7.
"""
import os
import sys
import time
import requests
from datetime import datetime

TARGET_URLS = [
    # Add any cloud deployed URLs here
]

# Read public URL if available
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUB_FILE = os.path.join(BASE_DIR, "public_url.txt")
if os.path.exists(PUB_FILE):
    try:
        with open(PUB_FILE, "r") as f:
            u = f.read().strip()
            if u.startswith("http"):
                TARGET_URLS.append(u)
    except Exception:
        pass

def ping_target(url):
    try:
        resp = requests.get(url, timeout=15)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🟢 Keep-Alive Ping to {url} -> Status {resp.status_code}")
        return True
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ⚠️ Ping failed for {url}: {e}")
        return False

def main():
    print("🚀 Starting 24/7 Cloud Keep-Alive Engine...")
    if not TARGET_URLS:
        print("ℹ️ No target URLs configured. Add URLs to TARGET_URLS list in keep_alive_cloud.py.")
        return

    while True:
        for url in TARGET_URLS:
            ping_target(url)
        # Sleep for 10 minutes between pings (prevents cloud inactivity sleep)
        time.sleep(600)

if __name__ == "__main__":
    main()
