#!/usr/bin/env python3
"""
Test script for backend login endpoint
Tests login with user alice and password alice123
"""

import requests
import json
import sys

BACKEND_URL = "https://backend-351592762922.us-west1.run.app"
USERNAME = "alice"
PASSWORD = "alice123"

def test_login():
    """Test the login endpoint"""
    print("=" * 60)
    print("Testing Backend Login Endpoint")
    print("=" * 60)
    print(f"\nBackend URL: {BACKEND_URL}")
    print(f"Username: {USERNAME}")
    print(f"Password: {PASSWORD}")
    
    # Test login
    print("\n1. Testing login endpoint...")
    login_url = f"{BACKEND_URL}/api/auth/login-legacy"
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    try:
        response = requests.post(
            login_url,
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                token = data["access_token"]
                print(f"   ✅ Login successful!")
                print(f"   Token (first 40 chars): {token[:40]}...")
                
                # Test token with a protected endpoint
                print("\n2. Testing token with /api/corpora/ endpoint...")
                corpora_response = requests.get(
                    f"{BACKEND_URL}/api/corpora/",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10
                )
                
                print(f"   Status Code: {corpora_response.status_code}")
                if corpora_response.status_code == 200:
                    corpora = corpora_response.json()
                    print(f"   ✅ Token is valid!")
                    print(f"   Corpora count: {len(corpora)}")
                    if corpora:
                        print(f"   Corpora names: {', '.join([c['display_name'] for c in corpora])}")
                else:
                    print(f"   ❌ Token validation failed")
                    print(f"   Response: {corpora_response.text[:200]}")
                
                # Test session creation
                print("\n3. Testing session creation...")
                session_response = requests.post(
                    f"{BACKEND_URL}/api/sessions",
                    headers={
                        "Authorization": f"Bearer {token}"
                    },
                    timeout=10
                )
                
                print(f"   Status Code: {session_response.status_code}")
                if session_response.status_code == 200:
                    session_data = session_response.json()
                    session_id = session_data.get("session_id")
                    print(f"   ✅ Session created successfully!")
                    print(f"   Session ID: {session_id}")
                    
                    # Test chat endpoint
                    print("\n4. Testing chat endpoint...")
                    chat_response = requests.post(
                        f"{BACKEND_URL}/api/sessions/{session_id}/chat",
                        json={
                            "message": "Hello, can you help me?",
                            "corpora": []
                        },
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Content-Type": "application/json"
                        },
                        timeout=30
                    )
                    
                    print(f"   Status Code: {chat_response.status_code}")
                    if chat_response.status_code == 200:
                        chat_data = chat_response.json()
                        print(f"   ✅ Chat endpoint working!")
                        print(f"   Response preview: {chat_data.get('response', '')[:100]}...")
                    else:
                        print(f"   ❌ Chat endpoint failed")
                        print(f"   Response: {chat_response.text[:300]}")
                else:
                    print(f"   ❌ Session creation failed")
                    print(f"   Response: {session_response.text[:200]}")
                
                print("\n" + "=" * 60)
                print("✅ ALL TESTS PASSED - Backend is working correctly!")
                print("=" * 60)
                return True
            else:
                print(f"   ❌ No access_token in response")
                print(f"   Response: {response.text}")
                return False
        else:
            print(f"   ❌ Login failed")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {str(e)}")
        return False
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON decode error: {str(e)}")
        print(f"   Response text: {response.text}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_login()
    sys.exit(0 if success else 1)
