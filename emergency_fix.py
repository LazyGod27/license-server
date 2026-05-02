#!/usr/bin/env python3
"""
Emergency Database Fix Script
Use this when the web app is hanging due to database issues
"""

import os
import sys
import requests
import time

def test_app_health():
    """Test if the app is responding"""
    print("🔍 Testing app health...")
    try:
        response = requests.get('https://license-server-016g.onrender.com/health', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ App is online")
            print(f"📊 Database status: {data.get('database', 'unknown')}")
            return True
        else:
            print(f"❌ App returned status: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("❌ App request timed out")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to app")
        return False
    except Exception as e:
        print(f"❌ Error testing app: {e}")
        return False

def emergency_init_database():
    """Initialize database using emergency endpoint"""
    print("🚀 Emergency database initialization...")
    try:
        response = requests.post('https://license-server-016g.onrender.com/emergency-init-db', 
                               timeout=30, json={})
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Database initialized successfully!")
                print(f"📋 Tables created: {data.get('tables', [])}")
                return True
            else:
                print(f"❌ Database initialization failed: {data.get('error')}")
                return False
        else:
            print(f"❌ Server returned status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"❌ Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"❌ Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Emergency initialization failed: {e}")
        return False

def generate_test_licenses():
    """Generate test licenses after database is ready"""
    print("🎯 Generating test licenses...")
    try:
        # First login to get token
        login_response = requests.post('https://license-server-016g.onrender.com/admin/api/login',
                                     timeout=10, json={
                                         'username': 'filbertace',
                                         'password': 'eca@09976944805'
                                     })
        
        if login_response.status_code != 200:
            print("❌ Login failed")
            return False
        
        token = login_response.json().get('token')
        
        # Generate licenses
        response = requests.post('https://license-server-016g.onrender.com/admin/api/generate-test-licenses',
                               timeout=10, json={},
                               headers={'Authorization': f'Bearer {token}'})
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Test licenses generated successfully!")
                print(f"🎫 Licenses: {data.get('licenses', [])}")
                return True
            else:
                print(f"❌ License generation failed: {data.get('error')}")
                return False
        else:
            print(f"❌ Server returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ License generation failed: {e}")
        return False

def main():
    print("=" * 60)
    print("EMERGENCY DATABASE FIX")
    print("=" * 60)
    
    # Step 1: Test app health
    if not test_app_health():
        print("\n❌ App is not responding. Check Render dashboard for deployment issues.")
        print("📝 Possible issues:")
        print("   - App is still deploying")
        print("   - Database connection is failing")
        print("   - App crashed during startup")
        return
    
    print("\n" + "="*40)
    
    # Step 2: Emergency database initialization
    if emergency_init_database():
        print("\n" + "="*40)
        
        # Step 3: Generate test licenses
        if generate_test_licenses():
            print("\n" + "="*40)
            print("🎉 SUCCESS! Your license server is now ready!")
            print("🌐 You can now access: https://license-server-016g.onrender.com/admin")
        else:
            print("\n⚠️ Database initialized but license generation failed")
            print("🌐 Try accessing admin panel manually")
    else:
        print("\n❌ Emergency database initialization failed")
        print("📝 Check the Render dashboard logs for detailed error information")

if __name__ == "__main__":
    main()
