#!/usr/bin/env python3
"""
Fix password hashes in Cloud SQL by generating fresh bcrypt hashes
and providing SQL UPDATE statements
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Test users and their passwords
users = [
    ("alice", "alice123"),
    ("bob", "bob123"),
    ("admin", "admin123"),
]

print("=" * 70)
print("SQL UPDATE Statements for Cloud SQL Password Reset")
print("=" * 70)
print()
print("-- Copy and paste these commands into Cloud SQL:")
print()

for username, password in users:
    hashed = pwd_context.hash(password)
    print(f"UPDATE users SET hashed_password = '{hashed}' WHERE username = '{username}';")

print()
print("-- Verify the updates:")
print("SELECT username, email, LEFT(hashed_password, 30) as pwd_prefix FROM users WHERE username IN ('alice', 'bob', 'admin');")
print()
print("=" * 70)
