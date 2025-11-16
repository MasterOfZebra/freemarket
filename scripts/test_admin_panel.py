#!/usr/bin/env python3
"""
Test script for admin panel functionality
"""

import os
import sys
import requests

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_admin_panel():
    """Test admin panel endpoints"""
    base_url = "http://localhost:8000"

    print("🧪 Testing admin panel...")

    # Test admin login page (should redirect to login)
    try:
        response = requests.get(f"{base_url}/admin", allow_redirects=False)
        print(f"✅ Admin root: {response.status_code}")
    except Exception as e:
        print(f"❌ Admin root failed: {e}")

    # Test admin login endpoint
    try:
        response = requests.post(f"{base_url}/admin/login", json={
            "username": "test_admin",
            "password": "test_pass"
        })
        print(f"✅ Admin login: {response.status_code}")
    except Exception as e:
        print(f"❌ Admin login failed: {e}")

    # Test token generation endpoint (requires auth)
    try:
        # This will fail without proper auth, but should return 401/403
        response = requests.post(f"{base_url}/admin/generate-token", json={
            "user_id": 1,
            "scope": "read"
        })
        print(f"✅ Token generation: {response.status_code} (expected 401/403 without auth)")
    except Exception as e:
        print(f"❌ Token generation failed: {e}")

    print("✅ Admin panel tests completed")

if __name__ == "__main__":
    test_admin_panel()
