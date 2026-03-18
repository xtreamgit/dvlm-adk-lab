#!/usr/bin/env python3
"""
Setup admin-users group and add the first user to it.
Run this to enable admin access for the first registered user.
"""

import sys
import os

# Add backend src to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(backend_dir, 'src')
sys.path.insert(0, src_dir)

from database.connection import get_db_connection
from database.repositories import GroupRepository, UserRepository
from services.user_service import UserService

def setup_admin_group():
    """Create admin-users group and add first user to it."""
    
    # Create admin-users group if it doesn't exist
    try:
        admin_group = GroupRepository.get_group_by_name('admin-users')
        if not admin_group:
            print("Creating admin-users group...")
            admin_group_id = GroupRepository.create({
                'name': 'admin-users',
                'description': 'Administrators with full system access',
                'is_active': True
            })
            print(f"✅ Created admin-users group with ID: {admin_group_id}")
        else:
            admin_group_id = admin_group['id']
            print(f"✅ admin-users group already exists (ID: {admin_group_id})")
    except Exception as e:
        print(f"❌ Error creating admin-users group: {e}")
        return False
    
    # Get all users
    try:
        all_users = UserRepository.get_all_users()
        if not all_users:
            print("⚠️  No users found in database. Register a user first.")
            return False
        
        print(f"\nFound {len(all_users)} user(s):")
        for i, user in enumerate(all_users, 1):
            print(f"  {i}. {user['username']} ({user['email']}) - ID: {user['id']}")
        
        # Add first user to admin-users group
        first_user_id = all_users[0]['id']
        first_username = all_users[0]['username']
        
        # Check if already in group
        user_groups = UserService.get_user_groups(first_user_id)
        if admin_group_id in user_groups:
            print(f"\n✅ User '{first_username}' is already in admin-users group")
        else:
            print(f"\nAdding user '{first_username}' to admin-users group...")
            success = UserService.add_user_to_group(first_user_id, admin_group_id)
            if success:
                print(f"✅ User '{first_username}' added to admin-users group")
            else:
                print(f"❌ Failed to add user to admin-users group")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up admin access: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Setting up admin-users group...\n")
    success = setup_admin_group()
    if success:
        print("\n✅ Admin setup complete! The first user now has admin access.")
        print("   You can now access the admin page at /admin")
    else:
        print("\n❌ Admin setup failed. Please check the errors above.")
        sys.exit(1)
