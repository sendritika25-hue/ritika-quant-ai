#!/usr/bin/env python3
"""
Cloudflare Tunnel Manager for Windows.
Keeps the Cloudflare tunnel running 24/7 so Ritika can access the dashboard from any mobile phone outside.
Saves the live URL into public_url.txt and sends an NTFY notification with 1-tap link.
"""
import os
import sys
import time
import re
import subprocess
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLOUDFLARED_EXE = os.path.join(BASE_DIR, "cloudflared.exe")
LOG_FILE = os.path.join(BASE_DIR, "cloudflared.log")
PUBLIC_URL_FILE = os.path.join(BASE_DIR, "public_url.txt")
NTFY_URL = "https://ntfy.sh/ritika_quant_ai_engine"

def send_ntfy_link(public_url):
    try:
        title = "👑 MOBILE APP LINK READY"
        message = (
            f"👑 RITIKA QUANT AI: Mobile App Link is Online!\n\n"
            f"👉 Tap below to open your dashboard on mobile:\n{public_url}\n\n"
            f"💡 Tip: Browser menu (3 dots) me jakar 'Add to Home screen' dabayein taaki phone screen par direct app icon ban jaye!"
        )
        headers = {
            "Title": "MOBILE APP LINK READY",
            "Priority": "urgent",
            "Tags": "crown,iphone,rocket",
            "Actions": f"view, Open App Now, {public_url}"
        }
        requests.post(NTFY_URL, data=message.encode('utf-8'), headers=headers, timeout=5)
        print(f"✓ Push notification with mobile link sent to NTFY!")
    except Exception as e:
        print(f"⚠️ Error sending NTFY notification: {e}")

def main():
    if not os.path.exists(CLOUDFLARED_EXE):
        print(f"Error: {CLOUDFLARED_EXE} not found.")
        sys.exit(1)

    # Check if cloudflared is already running
    check = subprocess.run(
        'tasklist /FI "IMAGENAME eq cloudflared.exe" /NH',
        capture_output=True, text=True, shell=True
    )
    if "cloudflared.exe" in check.stdout:
        print("cloudflared is already running.")
    else:
        print("Starting cloudflared tunnel with native logfile...")
        subprocess.Popen(
            [
                CLOUDFLARED_EXE, "tunnel",
                "--url", "http://localhost:8501",
                "--no-autoupdate",
                "--logfile", LOG_FILE
            ],
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )

    # Extract URL from log file or existing public_url.txt
    active_url = None
    for _ in range(25):
        time.sleep(1)
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    matches = re.findall(r"https://[a-zA-Z0-9.-]+\.trycloudflare\.com", content)
                    if matches:
                        active_url = matches[-1]
                        break
            except Exception:
                pass

    if not active_url and os.path.exists(PUBLIC_URL_FILE):
        try:
            with open(PUBLIC_URL_FILE, "r") as f:
                saved = f.read().strip()
                if "trycloudflare.com" in saved:
                    active_url = saved
        except Exception:
            pass

    if active_url:
        print(f"=======================================================")
        print(f"🎉 GLOBAL MOBILE DASHBOARD URL:")
        print(f"👉 {active_url}")
        print(f"=======================================================")
        with open(PUBLIC_URL_FILE, "w", encoding="utf-8") as f:
            f.write(active_url + "\n")
        
        try:
            home_path = os.path.expanduser("~/public_url.txt")
            with open(home_path, "w", encoding="utf-8") as f:
                f.write(active_url + "\n")
        except Exception:
            pass

        send_ntfy_link(active_url)
    else:
        print("⚠️ Could not extract Cloudflare URL yet.")

if __name__ == "__main__":
    main()
