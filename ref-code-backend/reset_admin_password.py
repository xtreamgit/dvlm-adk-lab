#!/usr/bin/env python3
"""
Reset admin user passwords to a known value for testing.
Usage: python reset_admin_password.py
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.auth_service import AuthService
from database.repositories.user_repository import UserRepository

def reset_password(username: str, new_password: str):
    """Reset a user's password."""
    user = UserRepository.get_by_username(username)
    if not user:
        print(f"❌ User '{username}' not found")
        return False
    
    hashed = AuthService.hash_password(new_password)
    UserRepository.update(user['id'], hashed_password=hashed)
    print(f"✅ Password reset for '{username}'")
    print(f"   Username: {username}")
    print(f"   Password: {new_password}")
    return True

def main():
    """Reset admin passwords."""
    print("\n🔐 Resetting Admin Passwords\n")
    
    # Reset alice password
    reset_password('alice', 'AdminPass123!')
    
    # Reset admin password
    reset_password('admin', 'AdminPass123!')
    
    print("\n✅ Password reset complete!")
    print("\nYou can now login with:")
    print("  Username: alice or admin")
    print("  Password: AdminPass123!")
    print()

if __name__ == '__main__':
    main()
