#!/usr/bin/env python3
"""
Terminal Database Initialization Script
Initialize your license server database from terminal
"""

import requests
import json
import sys

def init_database():
    """Initialize database using emergency endpoint"""
    print("🚀 Initializing database tables...")
    
    try:
        response = requests.post(
            'https://license-server-016g.onrender.com/emergency-init-db',
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Database initialized successfully!")
                print(f"📋 Tables created: {', '.join(data.get('tables', []))}")
                return True
            else:
                print(f"❌ Initialization failed: {data.get('error')}")
                return False
        else:
            print(f"❌ Server error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"❌ Details: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"❌ Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out - app might be starting up")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to app - check if it's deployed")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def generate_licenses():
    """Generate test licenses"""
    print("\n🎯 Generating test licenses...")
    
    try:
        # Login first
        print("🔐 Logging in...")
        login_response = requests.post(
            'https://license-server-016g.onrender.com/admin/api/login',
            timeout=10,
            json={
                'username': 'filbertace',
                'password': 'eca@09976944805'
            }
        )
        
        if login_response.status_code != 200:
            print("❌ Login failed")
            return False
        
        token = login_response.json().get('token')
        print("✅ Login successful")
        
        # Generate licenses
        response = requests.post(
            'https://license-server-016g.onrender.com/admin/api/generate-test-licenses',
            timeout=10,
            headers={'Authorization': f'Bearer {token}'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Test licenses generated!")
                for i, license_key in enumerate(data.get('licenses', []), 1):
                    print(f"   {i}. {license_key}")
                return True
            else:
                print(f"❌ License generation failed: {data.get('error')}")
                return False
        else:
            print(f"❌ Server error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ License generation error: {e}")
        return False

def check_app_health():
    """Check if app is running"""
    print("🔍 Checking app health...")
    
    try:
        response = requests.get('https://license-server-016g.onrender.com/health', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ App is online")
            print(f"📊 Database: {data.get('database', 'unknown')}")
            return True
        else:
            print(f"⚠️ App returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def main():
    print("=" * 50)
    print("DATABASE INITIALIZATION - TERMINAL VERSION")
    print("=" * 50)
    
    # Check app health first
    if not check_app_health():
        print("\n❌ App is not responding. Please check:")
        print("   1. App is deployed on Render")
        print("   2. Wait a few minutes for deployment")
        print("   3. Check Render dashboard for errors")
        return
    
    # Initialize database
    print("\n" + "-" * 40)
    if init_database():
        print("\n" + "-" * 40)
        # Generate test licenses
        if generate_licenses():
            print("\n" + "=" * 50)
            print("🎉 SUCCESS! Database is ready!")
            print("🌐 Access your admin panel: https://license-server-016g.onrender.com/admin")
            print("=" * 50)
        else:
            print("\n⚠️ Database initialized but license generation failed")
            print("🌐 Try accessing admin panel manually")
    else:
        print("\n❌ Database initialization failed")
        print("📝 Check Render dashboard logs for details")

if __name__ == "__main__":
    main()
