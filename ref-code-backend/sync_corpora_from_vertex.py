#!/usr/bin/env python3
"""
Sync corpora from Vertex AI RAG with local database.

This is a standalone script that uses the CorpusSyncService.
For automatic sync on backend startup, see server.py.

Usage:
    python backend/sync_corpora_from_vertex.py
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
    print(f"⚠️  No .env.local found - using environment variables or defaults")

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.corpus_sync_service import CorpusSyncService
from rag_agent.config import PROJECT_ID, LOCATION


def main():
    """Run corpus sync from Vertex AI to database."""
    print("=" * 70)
    print("Vertex AI Corpus Synchronization Tool")
    print("=" * 70)
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print()
    
    result = CorpusSyncService.sync_from_vertex(PROJECT_ID, LOCATION)
    
    print()
    print("=" * 70)
    print("Sync Results:")
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
    
    print("=" * 70)
    
    return result['status'] in ['success', 'partial']


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
