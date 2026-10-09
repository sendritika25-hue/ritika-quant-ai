#!/usr/bin/env python3
"""
Ritika Quant AI - Autonomous 24/7 Cloud Worker Engine
Runs continuously in the cloud (Render, Koyeb, Railway, Docker, or VPS)
independent of local office computers.
Monitors user holdings and universe stocks every 45-60 seconds and delivers
instant high-priority Push Notifications to mobile via ntfy.sh.
"""
import os
import sys
import time
import json
import socket
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("PORT", 8080))

# Global health & telemetry metrics
server_metrics = {
    "boot_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "last_scan_time": "Initializing...",
    "total_scans_completed": 0,
    "last_status": "Starting Engine",
    "last_alert_sent": "None yet",
    "holdings_count": 0,
    "holdings_symbols": []
}

def get_active_holdings_summary():
    holdings_path = os.path.join(BASE_DIR, "user_active_holdings.json")
    if os.path.exists(holdings_path):
        try:
            with open(holdings_path, "r", encoding="utf-8") as f:
                h_list = json.load(f)
                if isinstance(h_list, list):
                    symbols = [h.get("symbol", "") for h in h_list if isinstance(h, dict) and h.get("symbol")]
                    return len(symbols), symbols
        except Exception:
            pass
    return 0, []

def autonomous_scanner_daemon():
    """Background scanning daemon running 24/7"""
    import live_target_sl_notifier
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 Cloud Autonomous Scanner Daemon started in background thread.")
    
    # Initial sleep to allow HTTP server to bind
    time.sleep(5)
    
    while True:
        try:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            h_count, h_syms = get_active_holdings_summary()
            server_metrics["holdings_count"] = h_count
            server_metrics["holdings_symbols"] = h_syms
            server_metrics["last_status"] = "Scanning Market..."
            
            # Execute market target and stop-loss check
            live_target_sl_notifier.check_live_targets_and_notify()
            
            server_metrics["total_scans_completed"] += 1
            server_metrics["last_scan_time"] = now_str
            server_metrics["last_status"] = "Active & Standing By"
        except Exception as e:
            server_metrics["last_status"] = f"Error: {e}"
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ⚠️ Cloud scanner error: {e}")
        
        # Scan frequency: 45 seconds
        time.sleep(45)

class CloudWorkerHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response_data = {
                "status": "healthy",
                "service": "Ritika Quant AI 24/7 Cloud Worker",
                "boot_time": server_metrics["boot_time"],
                "last_scan": server_metrics["last_scan_time"],
                "scans_completed": server_metrics["total_scans_completed"],
                "engine_status": server_metrics["last_status"],
                "active_holdings": server_metrics["holdings_symbols"]
            }
            self.wfile.write(json.dumps(response_data, indent=2).encode("utf-8"))
            return

        if self.path == "/test_alert":
            try:
                import live_target_sl_notifier
                live_target_sl_notifier.send_push_alert(
                    "🔔 24/7 CLOUD BOT: Direct Mobile Test!",
                    "🎉 Ritika Quant AI 24/7 Cloud Engine is running live in the cloud!\n\n"
                    "• Your office PC can be completely turned off\n"
                    "• Market monitoring and alerts will run autonomously\n"
                    "• NTFY push alerts will arrive continuously on your mobile phone!",
                    priority="high",
                    tags="crown,rocket,white_check_mark"
                )
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"<h1>Test Alert Sent Successfully! Check your phone!</h1><p><a href='/'>Go back</a></p>")
                return
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(f"Failed to send alert: {e}".encode("utf-8"))
                return

        # Default root landing dashboard
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        
        h_count, h_syms = get_active_holdings_summary()
        symbols_html = "".join([f"<span class='badge'>{s}</span>" for s in h_syms]) if h_syms else "None"
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Ritika Quant AI - 24/7 Cloud Engine</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{
            background: #0b0f19;
            color: #f8fafc;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 30px 20px;
            display: flex;
            justify-content: center;
        }}
        .card {{
            background: #111827;
            border: 1px solid #1f2937;
            border-radius: 16px;
            padding: 28px;
            max-width: 620px;
            width: 100%;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }}
        h1 {{
            font-size: 22px;
            margin-top: 0;
            color: #38bdf8;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .status-dot {{
            width: 12px;
            height: 12px;
            background: #22c55e;
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 12px #22c55e;
        }}
        .metric-row {{
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #1e293b;
            font-size: 14px;
        }}
        .label {{ color: #94a3b8; }}
        .value {{ color: #f1f5f9; font-weight: 600; text-align: right; }}
        .badge {{
            background: #1e293b;
            color: #38bdf8;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 12px;
            margin: 2px;
            display: inline-block;
        }}
        .btn {{
            display: block;
            width: 100%;
            text-align: center;
            background: #2563eb;
            color: #ffffff;
            padding: 12px 0;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            margin-top: 24px;
            transition: background 0.2s;
        }}
        .btn:hover {{ background: #1d4ed8; }}
        .footer {{
            text-align: center;
            color: #64748b;
            font-size: 11px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="card">
        <h1><span class="status-dot"></span> Ritika Quant AI • 24/7 Cloud Bot</h1>
        <p style="color: #94a3b8; font-size: 13px; margin-bottom: 20px;">
            Autonomous Cloud Engine is active. Live target, SL, and breakout alerts will be delivered to your phone even if your office PC is turned off.
        </p>

        <div class="metric-row">
            <span class="label">Server Status</span>
            <span class="value" style="color: #22c55e;">🟢 {server_metrics['last_status']}</span>
        </div>
        <div class="metric-row">
            <span class="label">Last Market Scan</span>
            <span class="value">{server_metrics['last_scan_time']}</span>
        </div>
        <div class="metric-row">
            <span class="label">Total Scans Executed</span>
            <span class="value">{server_metrics['total_scans_completed']} cycles</span>
        </div>
        <div class="metric-row">
            <span class="label">Push Channel</span>
            <span class="value" style="color: #a855f7;">ntfy.sh/ritika_quant_ai_engine</span>
        </div>
        <div class="metric-row">
            <span class="label">Active Holdings Monitored</span>
            <span class="value">{symbols_html}</span>
        </div>
        <div class="metric-row">
            <span class="label">Cloud Boot Time</span>
            <span class="value">{server_metrics['boot_time']}</span>
        </div>

        <a href="/test_alert" class="btn">🚀 Send Test Alert to Mobile Phone</a>
        <div class="footer">👑 Ritika Quant AI Autonomous Cloud Engine • 24x7 Always-On</div>
    </div>
</body>
</html>
"""
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        # Keep logs clean
        return

def run_server():
    # Start autonomous scanner in background thread
    t = threading.Thread(target=autonomous_scanner_daemon, daemon=True, name="CloudAutonomousScanner")
    t.start()
    
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, CloudWorkerHandler)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🌐 Ritika Quant AI 24/7 Cloud Worker HTTP Server running on port {PORT}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down cloud worker...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
