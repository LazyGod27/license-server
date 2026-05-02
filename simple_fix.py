#!/usr/bin/env python3
"""
Simple Database Fix - Just Create Tables!
"""

import requests

print("Creating database tables...")

try:
    response = requests.post('https://license-server-016g.onrender.com/emergency-init-db')
    
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            print("✅ Tables created successfully!")
            print(f"Tables: {', '.join(data['tables'])}")
        else:
            print(f"❌ Error: {data['error']}")
    else:
        print(f"❌ Server error: {response.status_code}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("Done!")
