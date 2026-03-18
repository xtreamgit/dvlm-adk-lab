#!/usr/bin/env python3
"""
Test script for CorpusSyncService.
Verifies that the sync service can connect to Vertex AI and sync corpora.

Usage:
    python backend/test_corpus_sync.py
"""

import os
import sys
from pathlib import Path

# Load .env.local BEFORE importing any database modules
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env.local'
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"✅ Loaded environment from {env_path}")
else:
    print(f"⚠️  No .env.local found at {env_path}")
    print("   Using environment variables or defaults")

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.corpus_sync_service import CorpusSyncService
from rag_agent.config import PROJECT_ID, LOCATION


def test_sync():
    """Test the corpus sync service."""
    print("=" * 70)
    print("Testing CorpusSyncService")
    print("=" * 70)
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print()
    
    print("Running sync test...")
    result = CorpusSyncService.sync_from_vertex(PROJECT_ID, LOCATION)
    
    print()
    print("=" * 70)
    print("Test Results:")
    print("=" * 70)
    print(f"Status: {result['status'].upper()}")
    print(f"Vertex AI corpora: {result['vertex_count']}")
    print(f"Database active corpora: {result['db_active_count']}")
    print(f"Added: {result['added']}")
    print(f"Updated: {result['updated']}")
    print(f"Deactivated: {result['deactivated']}")
    
    if result['errors']:
        print(f"\nErrors ({len(result['errors'])}):")
        for error in result['errors']:
            print(f"  - {error}")
        print()
        print("❌ Test FAILED with errors")
        return False
    
    if result['status'] == 'success':
        print()
        print("✅ Test PASSED - Sync completed successfully")
        return True
    elif result['status'] == 'partial':
        print()
        print("⚠️  Test PARTIAL - Sync completed with some errors")
        return True
    else:
        print()
        print("❌ Test FAILED")
        return False


if __name__ == "__main__":
    success = test_sync()
    sys.exit(0 if success else 1)
