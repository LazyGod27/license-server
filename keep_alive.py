import requests
import threading
import time
import os
from datetime import datetime

def keep_alive():
    """Send periodic requests to keep the app alive"""
    app_url = os.getenv('RENDER_EXTERNAL_URL', 'https://license-server-016g.onrender.com')
    health_url = f"{app_url}/"
    
    while True:
        try:
            print(f"🔄 Keep-alive ping at {datetime.now().strftime('%H:%M:%S')}")
            response = requests.get(health_url, timeout=10)
            print(f"✅ Keep-alive successful: {response.status_code}")
        except Exception as e:
            print(f"❌ Keep-alive failed: {e}")
        
        # Ping every 10 minutes (Render spins down after 15 minutes)
        time.sleep(600)

def start_keep_alive():
    """Start the keep-alive thread"""
    thread = threading.Thread(target=keep_alive, daemon=True)
    thread.start()
    print("🚀 Keep-alive service started")

if __name__ == "__main__":
    start_keep_alive()
    keep_alive()  # For testing
