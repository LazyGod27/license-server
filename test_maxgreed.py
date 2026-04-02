import requests
import json

# Test MaxGreed license generation
def test_maxgreed_license():
    url = "http://localhost:8080/admin/api/licenses"
    
    # Login first
    login_url = "http://localhost:8080/admin/api/login"
    login_data = {
        "username": "filbertace",
        "password": "eca@09976944805"
    }
    
    session = requests.Session()
    login_response = session.post(login_url, json=login_data)
    
    if login_response.status_code != 200:
        print("❌ Login failed")
        print(login_response.text)
        return
    
    print("✅ Login successful")
    
    # Generate MaxGreed license
    license_data = {
        "product_id": "MAXGreed",
        "max_activations": 5,
        "expires_at": "2025-12-31",
        "features": {
            "arena_reset": True,
            "lobby": True,
            "cards": True,
            "dropper": True,
            "bug": True
        }
    }
    
    response = session.post(url, json=license_data)
    
    if response.status_code == 200:
        result = response.json()
        license_key = result.get('license_key')
        print(f"✅ MaxGreed license generated: {license_key}")
        
        # Test verification
        verify_url = "http://localhost:8080/api/v1/verify"
        verify_data = {
            "license_key": license_key,
            "username": "testuser",
            "product_id": "MAXGreed",
            "hardware_data": "test_hw_12345"
        }
        
        verify_response = requests.post(verify_url, json=verify_data)
        if verify_response.status_code == 200:
            verify_result = verify_response.json()
            print(f"✅ MaxGreed license verification: {verify_result.get('valid', False)}")
            print(f"✅ Features returned: {verify_result.get('features', {})}")
        else:
            print(f"❌ Verification failed: {verify_response.text}")
    else:
        print(f"❌ License generation failed: {response.text}")

if __name__ == "__main__":
    test_maxgreed_license()
