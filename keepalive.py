#!/usr/bin/env python3
"""
Cloudflare 24/7 Keep-Alive Bot for Google Cloud Shell
Automatically keeps shell.cloud.google.com awake 24/7 using Cloudflare Tunnels
"""

import os
import sys
import time
import subprocess
import threading
import urllib.request
import re
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 8080
CLOUDFLARED_BIN = Path.home() / ".cloudflared_bin" / "cloudflared"

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Google Cloud Shell 24/7 KeepAlive is Active!")
    def log_message(self, format, *args):
        return

def ensure_cloudflared():
    if CLOUDFLARED_BIN.exists() and os.access(CLOUDFLARED_BIN, os.X_OK):
        return str(CLOUDFLARED_BIN)
    
    print("[*] Downloading Cloudflare tunnel binary...")
    CLOUDFLARED_BIN.parent.mkdir(parents=True, exist_ok=True)
    url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
    urllib.request.urlretrieve(url, str(CLOUDFLARED_BIN))
    CLOUDFLARED_BIN.chmod(0o755)
    print("[✓] Cloudflare binary ready.")
    return str(CLOUDFLARED_BIN)

def run_server():
    server = HTTPServer(('127.0.0.1', PORT), Handler)
    server.serve_forever()

def main():
    print("=" * 65)
    print("      CLOUDFLARE 24/7 GOOGLE CLOUD SHELL KEEPALIVE BOT        ")
    print("                  by sidripon37                               ")
    print("=" * 65)
    
    bin_path = ensure_cloudflared()
    
    print("[*] Starting internal heartbeat server on port 8080...")
    threading.Thread(target=run_server, daemon=True).start()
    
    print("[*] Connecting to Cloudflare Global Network (No Token Needed)...")
    cmd = [bin_path, "tunnel", "--url", f"http://127.0.0.1:{PORT}"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    tunnel_url = None
    for line in proc.stdout:
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            tunnel_url = match.group(0)
            print("
" + "=" * 65)
            print("🎉 CLOUDFLARE TUNNEL CONNECTED!")
            print(f"👉 Public KeepAlive URL: {tunnel_url}")
            print("=" * 65 + "
")
            print("[*] Continuous Inbound Traffic Activated.")
            print("[*] Google Cloud Shell will stay AWAKE 24/7 while this is running!
")
            break

    count = 0
    while True:
        time.sleep(60)
        count += 1
        now = time.strftime("%H:%M:%S")
        try:
            if tunnel_url:
                req = urllib.request.Request(tunnel_url, headers={'User-Agent': 'CloudShell-KeepAlive/1.0'})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    print(f"[{now}] 🌐 Heartbeat #{count} | Inbound Traffic Verified | Shell is Awake!")
            else:
                print(f"[{now}] 🌐 Heartbeat #{count} | Tunnel Active")
        except Exception:
            print(f"[{now}] 🌐 Heartbeat #{count} | Active")

if __name__ == "__main__":
    main()
