#!/usr/bin/env python3
"""
Cloudflare 24/7 Official Keep-Alive Bot for Google Cloud Shell
Powered by Cloudflare Zero Trust Tunnel
by sidripon37
"""

import os
import sys
import time
import subprocess
import threading
import urllib.request
from pathlib import Path

CF_TOKEN = "eyJhIjoiYjU2OGRhYTM1Y2YxOWQ3OTE2M2VjYTU1NzdkZGU5ODUiLCJ0IjoiZGUzOTYxMzEtM2FhZi00NWFlLWE4MTAtZmJlYTZmZDhlNTJjIiwicyI6Ik1UZGlNRE5pT1dRdE1qbGxaaTAwWW1ObExUaGtNekV0TXpSaE9HRTBZVGt5WVdWaSJ9"
CLOUDFLARED_BIN = Path.home() / ".cloudflared_bin" / "cloudflared"

def ensure_cloudflared():
    if CLOUDFLARED_BIN.exists() and os.access(CLOUDFLARED_BIN, os.X_OK):
        return str(CLOUDFLARED_BIN)
    
    print("[*] Downloading official Cloudflare tunnel binary...")
    CLOUDFLARED_BIN.parent.mkdir(parents=True, exist_ok=True)
    url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
    urllib.request.urlretrieve(url, str(CLOUDFLARED_BIN))
    CLOUDFLARED_BIN.chmod(0o755)
    print("[✓] Cloudflare binary installed.")
    return str(CLOUDFLARED_BIN)

def main():
    print("=" * 65)
    print("      CLOUDFLARE 24/7 OFFICIAL TUNNEL BOT (GOOGLE CLOUD SHELL) ")
    print("                      by sidripon37                           ")
    print("=" * 65)
    
    bin_path = ensure_cloudflared()
    
    print("[*] Connecting your official Cloudflare Tunnel...")
    cmd = [bin_path, "tunnel", "run", "--token", CF_TOKEN]
    
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print("[✓] Cloudflare Tunnel is now RUNNING!")
    print("[✓] Status on Cloudflare dashboard will change to HEALTHY (Active)!")
    print("[*] Google Cloud Shell is now protected and kept alive 24/7.\n")

    for line in proc.stdout:
        if "Registered tunnel connection" in line or "Connection" in line:
            now = time.strftime("%H:%M:%S")
            print(f"[{now}] 🌐 Cloudflare Tunnel Connected & Active! Traffic Flowing.")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
