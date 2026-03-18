"""
Test script for agent access control API endpoints.
Tests all the new agent-related endpoints.
"""

import requests
import json

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/admin/chatbot"

# Login credentials (using alice as test user)
LOGIN_DATA = {
    "username": "alice",
    "password": "alice123"
}

def get_auth_token():
    """Login and get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=LOGIN_DATA)
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        return None

def test_get_all_agents(token):
    """Test GET /api/admin/chatbot/agents"""
    print("\n📋 Testing: GET /agents")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE}/agents", headers=headers)
    
    if response.status_code == 200:
        agents = response.json()
        print(f"✅ Success! Found {len(agents)} agents:")
        for agent in agents:
            print(f"   - {agent['display_name']} ({agent['agent_type']})")
            print(f"     Tools: {', '.join(agent['tools'])}")
        return agents
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return []

def test_get_agent_by_id(token, agent_id):
    """Test GET /api/admin/chatbot/agents/{agent_id}"""
    print(f"\n📋 Testing: GET /agents/{agent_id}")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE}/agents/{agent_id}", headers=headers)
    
    if response.status_code == 200:
        agent = response.json()
        print(f"✅ Success! Agent details:")
        print(f"   Name: {agent['display_name']}")
        print(f"   Type: {agent['agent_type']}")
        print(f"   Tools: {', '.join(agent['tools'])}")
        return agent
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return None

def test_get_group_agents(token, group_id):
    """Test GET /api/admin/chatbot/groups/{group_id}/agents"""
    print(f"\n📋 Testing: GET /groups/{group_id}/agents")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE}/groups/{group_id}/agents", headers=headers)
    
    if response.status_code == 200:
        agents = response.json()
        print(f"✅ Success! Group has {len(agents)} agent(s):")
        for agent in agents:
            print(f"   - {agent['display_name']} (can_use: {agent['can_use']})")
        return agents
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return []

def test_get_user_available_agents(token, user_id):
    """Test GET /api/admin/chatbot/users/{user_id}/available-agents"""
    print(f"\n📋 Testing: GET /users/{user_id}/available-agents")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE}/users/{user_id}/available-agents", headers=headers)
    
    if response.status_code == 200:
        agents = response.json()
        print(f"✅ Success! User has access to {len(agents)} agent(s):")
        for agent in agents:
            print(f"   - {agent['display_name']} ({agent['agent_type']})")
        return agents
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return []

def test_assign_agent_to_group(token, group_id, agent_id):
    """Test POST /api/admin/chatbot/groups/{group_id}/agents/{agent_id}"""
    print(f"\n📋 Testing: POST /groups/{group_id}/agents/{agent_id}")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_BASE}/groups/{group_id}/agents/{agent_id}", headers=headers)
    
    if response.status_code == 200:
        print(f"✅ Success! {response.json()['message']}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return False

def test_remove_agent_from_group(token, group_id, agent_id):
    """Test DELETE /api/admin/chatbot/groups/{group_id}/agents/{agent_id}"""
    print(f"\n📋 Testing: DELETE /groups/{group_id}/agents/{agent_id}")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(f"{API_BASE}/groups/{group_id}/agents/{agent_id}", headers=headers)
    
    if response.status_code == 200:
        print(f"✅ Success! {response.json()['message']}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return False

def get_groups(token):
    """Get all groups to find test group IDs"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE}/groups", headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def get_users(token):
    """Get all users to find test user IDs"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE}/users", headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def main():
    print("🚀 Starting Agent API Endpoint Tests")
    print("=" * 60)
    
    # Get authentication token
    print("\n🔐 Authenticating...")
    token = get_auth_token()
    if not token:
        print("❌ Cannot proceed without authentication")
        return
    print("✅ Authentication successful!")
    
    # Test 1: Get all agents
    agents = test_get_all_agents(token)
    if not agents:
        print("❌ No agents found, cannot continue tests")
        return
    
    # Test 2: Get specific agent by ID
    test_agent_id = agents[0]['id']
    test_get_agent_by_id(token, test_agent_id)
    
    # Get groups for testing
    print("\n📋 Fetching groups...")
    groups = get_groups(token)
    viewer_group = next((g for g in groups if g['name'] == 'viewer-group'), None)
    
    if viewer_group:
        print(f"✅ Found viewer-group (ID: {viewer_group['id']})")
        
        # Test 3: Get agents for a specific group
        test_get_group_agents(token, viewer_group['id'])
        
        # Test 4: Get users
        print("\n📋 Fetching users...")
        users = get_users(token)
        if users:
            test_user_id = users[0]['id']
            print(f"✅ Found test user (ID: {test_user_id})")
            
            # Test 5: Get available agents for a user
            test_get_user_available_agents(token, test_user_id)
    else:
        print("⚠️ viewer-group not found, skipping group-specific tests")
    
    print("\n" + "=" * 60)
    print("✨ Agent API Endpoint Tests Complete!")

if __name__ == '__main__':
    main()
