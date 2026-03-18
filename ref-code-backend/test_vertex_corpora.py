#!/usr/bin/env python3
"""
Test script to list Vertex AI corpora and their file counts
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import vertexai
from vertexai import rag
import google.auth

# Load config
from config.config_loader import load_config
account = os.getenv('ACCOUNT_ENV', 'develom')
config = load_config(account)
PROJECT_ID = config.PROJECT_ID
LOCATION = config.LOCATION

print(f"Initializing Vertex AI with project={PROJECT_ID}, location={LOCATION}")

# Initialize Vertex AI
credentials, _ = google.auth.default()
vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)

# List corpora
print("\n=== Listing Vertex AI Corpora ===")
corpora = rag.list_corpora()

for i, corpus in enumerate(corpora, 1):
    print(f"\n{i}. Corpus:")
    print(f"   Resource Name: {corpus.name}")
    print(f"   Display Name: {corpus.display_name}")
    
    # Count files
    try:
        files = list(rag.list_files(corpus.name))
        print(f"   File Count: {len(files)}")
        if files:
            print(f"   Sample files:")
            for j, f in enumerate(files[:3], 1):
                print(f"     {j}. {f.display_name if hasattr(f, 'display_name') else 'N/A'}")
    except Exception as e:
        print(f"   Error listing files: {e}")

print("\n=== Complete ===")
