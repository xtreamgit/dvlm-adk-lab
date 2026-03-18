"""
Test script for agent type hierarchy endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def login():
    """Login and get auth token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "username": "alice",
            "password": "alice123"
        }
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    else:
        print(f"Login failed: {response.status_code}")
        print(response.text)
        return None

def test_agent_type_hierarchy(token):
    """Test GET /api/admin/chatbot/agent-type-hierarchy"""
    print("\n" + "="*70)
    print("TEST 1: Get Agent Type Hierarchy")
    print("="*70)
    
    response = requests.get(
        f"{BASE_URL}/api/admin/chatbot/agent-type-hierarchy",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Success! Found {len(data)} agent types:\n")
        for agent_type in data:
            print(f"  🎭 {agent_type['display_name']} ({agent_type['type']})")
            print(f"     Description: {agent_type['description']}")
            print(f"     Tools: {len(agent_type['tools'])} total, {len(agent_type['incremental_tools'])} new")
            print(f"     Color: {agent_type['color']}")
            print(f"     All tools: {', '.join(agent_type['tools'])}")
            print()
    else:
        print(f"❌ Failed: {response.text}")

def test_agent_type_tools(token, agent_type):
    """Test GET /api/admin/chatbot/agent-type-tools/{agent_type}"""
    print("\n" + "="*70)
    print(f"TEST 2: Get Tools for Agent Type '{agent_type}'")
    print("="*70)
    
    response = requests.get(
        f"{BASE_URL}/api/admin/chatbot/agent-type-tools/{agent_type}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Success!")
        print(f"   Agent Type: {data['agent_type']}")
        print(f"   Tool Count: {data['tool_count']}")
        print(f"   Tools: {', '.join(data['tools'])}")
    else:
        print(f"❌ Failed: {response.text}")

def test_my_agent_type(token):
    """Test GET /api/admin/chatbot/my-agent-type"""
    print("\n" + "="*70)
    print("TEST 3: Get My Agent Type")
    print("="*70)
    
    response = requests.get(
        f"{BASE_URL}/api/admin/chatbot/my-agent-type",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Success!")
        print(f"   Your Agent Type: {data['agent_type']}")
        print(f"   Tool Count: {data['tool_count']}")
        if data['allowed_tools']:
            print(f"   Allowed Tools: {', '.join(data['allowed_tools'])}")
        else:
            print(f"   ⚠️  No agent type assigned yet")
    else:
        print(f"❌ Failed: {response.text}")

def main():
    print("🧪 Testing Agent Type Hierarchy Endpoints")
    print("="*70)
    
    # Login
    print("\n📝 Logging in as alice...")
    token = login()
    
    if not token:
        print("❌ Could not get auth token. Exiting.")
        return
    
    print(f"✅ Got auth token: {token[:20]}...")
    
    # Test all endpoints
    test_agent_type_hierarchy(token)
    
    # Test each agent type
    for agent_type in ["viewer", "contributor", "content-manager", "corpus-manager"]:
        test_agent_type_tools(token, agent_type)
    
    # Test invalid agent type
    print("\n" + "="*70)
    print("TEST: Invalid Agent Type")
    print("="*70)
    response = requests.get(
        f"{BASE_URL}/api/admin/chatbot/agent-type-tools/invalid-type",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 400:
        print(f"✅ Correctly rejected invalid agent type")
        print(f"   Error: {response.json()['detail']}")
    else:
        print(f"❌ Unexpected response: {response.text}")
    
    # Test my agent type
    test_my_agent_type(token)
    
    print("\n" + "="*70)
    print("✅ All tests completed!")
    print("="*70)

if __name__ == "__main__":
    main()
