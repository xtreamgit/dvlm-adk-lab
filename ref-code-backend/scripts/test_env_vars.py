#!/usr/bin/env python3
"""Test script to verify environment variables in Cloud Run"""
import os

print("=== Environment Variables ===")
print(f"DB_TYPE: {os.getenv('DB_TYPE', 'NOT SET')}")
print(f"DB_NAME: {os.getenv('DB_NAME', 'NOT SET')}")
print(f"DB_USER: {os.getenv('DB_USER', 'NOT SET')}")
print(f"DB_HOST: {os.getenv('DB_HOST', 'NOT SET')}")
print(f"DB_PASSWORD: {'SET' if os.getenv('DB_PASSWORD') else 'NOT SET'}")
print(f"CLOUD_SQL_CONNECTION_NAME: {os.getenv('CLOUD_SQL_CONNECTION_NAME', 'NOT SET')}")

# Try importing the connection module
import sys
sys.path.insert(0, '/app/src')

try:
    from database import connection
    print(f"\n=== Connection Module ===")
    print(f"DB_TYPE from module: {connection.DB_TYPE}")
    print(f"PG_CONFIG: {connection.PG_CONFIG}")
except Exception as e:
    print(f"Error importing: {e}")
