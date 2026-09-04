"""
Public Online Tunnel Launcher for Hardware Dashboard
Enables remote access from smartphones and external networks via secure HTTPS tunnel.
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "tunnel_config.json"


def ensure_pyngrok_installed():
    """Installs pyngrok automatically if missing."""
    try:
        import pyngrok
    except ImportError:
        print("[*] pyngrok is not installed. Installing now...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyngrok", "--quiet"])
        print("[+] pyngrok successfully installed.\n")


def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"authtoken": "", "static_domain": ""}


def save_config(config: dict):
    CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")


def main():
    print("=" * 65)
    print("   ⚡ Hardware Dashboard - Remote Access Tunnel (Online Mode) ⚡")
    print("=" * 65)
    print()

    ensure_pyngrok_installed()
    from pyngrok import ngrok, conf

    config = load_config()
    authtoken = os.environ.get("NGROK_AUTHTOKEN") or config.get("authtoken", "").strip()
    domain = os.environ.get("NGROK_DOMAIN") or config.get("static_domain", "").strip()

    # If no authtoken configured, prompt user once and save it
    if not authtoken:
        print("💡 Ngrok requires a free account token to expose your dashboard online.")
        print("   1. Create a free account at: https://dashboard.ngrok.com/signup")
        print("   2. Copy your AuthToken from: https://dashboard.ngrok.com/get-started/your-authtoken")
        print()
        entered_token = input("👉 Paste your Ngrok AuthToken (press Enter to skip if already in config): ").strip()
        if entered_token:
            authtoken = entered_token
            config["authtoken"] = authtoken
            save_config(config)
            print("[+] Token saved to tunnel_config.json.")

    if authtoken:
        ngrok.set_auth_token(authtoken)
    else:
        print("[!] Warning: Running without AuthToken. May encounter connection limits.")

    # Optional static domain
    if not domain and authtoken:
        print()
        print("💡 Ngrok provides 1 Free Static Domain that never changes:")
        print("   (Find it at: https://dashboard.ngrok.com/cloud-edge/domains)")
        entered_domain = input("👉 Paste your free static domain (or press Enter for dynamic link): ").strip()
        if entered_domain:
            domain = entered_domain
            config["static_domain"] = domain
            save_config(config)

    # Launch Streamlit server
    print()
    print("[*] Starting local Streamlit dashboard on port 8501...")
    streamlit_proc = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ],
        cwd=str(Path(__file__).parent),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Wait 2 seconds for server startup
    time.sleep(2.5)

    try:
        print("[*] Connecting secure public HTTPS tunnel...")
        if domain:
            public_tunnel = ngrok.connect(8501, domain=domain)
            print(f"[+] Attached to static domain: {domain}")
        else:
            public_tunnel = ngrok.connect(8501)

        public_url = public_tunnel.public_url
        if public_url.startswith("http://"):
            public_url = public_url.replace("http://", "https://", 1)

        print()
        print("*" * 65)
        print("  🎉 YOUR HARDWARE DASHBOARD IS NOW LIVE WORLDWIDE!")
        print(f"  👉 Permanent Public Link: {public_url}")
        print("*" * 65)
        print()
        print("📱 You can open this link from your phone, laptop, or any outside network.")
        print("🖥️ The dashboard reflects your PC's real-time CPU thermals & Downloads lag.")
        print()
        print("Press Ctrl+C in this window at any time to disconnect the tunnel.")
        print("-" * 65)

        streamlit_proc.wait()

    except KeyboardInterrupt:
        print("\n[*] Shutting down remote tunnel and dashboard server...")
    except Exception as e:
        print(f"\n[!] Tunnel Error: {e}")
    finally:
        try:
            ngrok.kill()
        except Exception:
            pass
        streamlit_proc.terminate()
        print("[+] Disconnected cleanly.")


if __name__ == "__main__":
    main()
