import subprocess
import time
import os
import re

print("Checking 24/7 Services...")

nginx_dir = os.path.expanduser("~/nginx_app")
for d in ["client_body_temp", "proxy_temp", "fastcgi_temp", "uwsgi_temp", "scgi_temp", "logs"]:
    os.makedirs(os.path.join(nginx_dir, d), exist_ok=True)

# 1. Check & Start Streamlit
st_check = subprocess.run(["pgrep", "-f", "streamlit run app.py"], capture_output=True, text=True)
if not st_check.stdout.strip():
    log_st = open(os.path.expanduser("~/trading_ai/streamlit.log"), "a")
    subprocess.Popen(
        [
            os.path.expanduser("~/trading_ai_env/bin/streamlit"),
            "run", "app.py",
            "--server.port=8502",
            "--server.address=127.0.0.1",
            "--server.headless=true"
        ],
        cwd=os.path.expanduser("~/trading_ai"),
        stdout=log_st,
        stderr=log_st,
        start_new_session=True
    )
    print("Streamlit started on 127.0.0.1:8502")
else:
    print("Streamlit is already running.")

# 2. Check & Start Nginx
ng_check = subprocess.run(["pgrep", "-f", "nginx_app/usr/sbin/nginx"], capture_output=True, text=True)
if not ng_check.stdout.strip():
    nginx_bin = os.path.join(nginx_dir, "usr/sbin/nginx")
    nginx_cfg = os.path.join(nginx_dir, "nginx.conf")
    subprocess.run([nginx_bin, "-c", nginx_cfg])
    print("Nginx started on 0.0.0.0:8501")
else:
    print("Nginx is already running.")

# 3. Check & Start Cloudflare Tunnel (DO NOT RESTART IF ALREADY RUNNING)
cf_check = subprocess.run(["pgrep", "-f", "cloudflared tunnel"], capture_output=True, text=True)
if not cf_check.stdout.strip():
    log_cf = open(os.path.expanduser("~/cloudflared.log"), "w")
    subprocess.Popen(
        [
            os.path.expanduser("~/cloudflared"),
            "tunnel",
            "--url", "http://localhost:8501",
            "--no-autoupdate",
            "--protocol", "http2"
        ],
        stdout=log_cf,
        stderr=log_cf,
        start_new_session=True
    )
    print("Cloudflared tunnel started.")
    time.sleep(5)
else:
    print("Cloudflared tunnel is already running.")

# 4. Extract active URL
active_url = None
if os.path.exists(os.path.expanduser("~/cloudflared.log")):
    with open(os.path.expanduser("~/cloudflared.log")) as f:
        content = f.read()
        matches = re.findall(r"https://[a-zA-Z0-9.-]+\.trycloudflare\.com", content)
        if matches:
            active_url = matches[-1]

if active_url:
    print(f"\n=======================================================")
    print(f"🎉 PERMANENT 24/7 GLOBAL PUBLIC URL (STABLE):")
    print(f"👉 {active_url}")
    print(f"=======================================================\n")
    with open(os.path.expanduser("~/public_url.txt"), "w") as f:
        f.write(active_url + "\n")
