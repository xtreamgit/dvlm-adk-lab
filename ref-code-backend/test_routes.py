#!/usr/bin/env python3
"""Test script to verify routes can be imported."""

import sys
sys.path.insert(0, 'src')

print("Testing route imports...")

try:
    from api.routes import (
        users_router,
        agents_router,
        corpora_router,
        admin_router,
        iap_auth_router,
        documents_router,
        chatbot_admin_router,
        google_groups_admin_router
    )
    print("✅ All routes imported successfully")
    print(f"  users_router: {users_router.prefix}")
    print(f"  agents_router: {agents_router.prefix}")
    print(f"  corpora_router: {corpora_router.prefix}")
    
    # Now test importing the server
    print("\nTesting server import...")
    from api.server import app, NEW_ROUTES_AVAILABLE
    print(f"  NEW_ROUTES_AVAILABLE: {NEW_ROUTES_AVAILABLE}")
    print(f"  App routes count: {len(app.routes)}")
    
    # List all registered routes
    print("\nRegistered routes:")
    for route in app.routes:
        if hasattr(route, 'path'):
            print(f"  {route.path}")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
