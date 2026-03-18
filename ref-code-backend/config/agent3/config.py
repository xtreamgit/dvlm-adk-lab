"""
Configuration settings for the RAG Agent - AGENT3 Account
Account: agent3

These settings are used by the various RAG tools.
Vertex AI initialization is performed in the package's __init__.py
"""

import os

# Account identifier
ACCOUNT_NAME = "agent3"
ACCOUNT_DESCRIPTION = "Generic Agent3 configuration"

# Vertex AI settings (defaults; real values should come from env/Cloud Run)
PROJECT_ID = os.environ.get("PROJECT_ID", "adk-rag-ma")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-west1")

# RAG settings
DEFAULT_CHUNK_SIZE = 512
DEFAULT_CHUNK_OVERLAP = 100
DEFAULT_TOP_K = 3
DEFAULT_DISTANCE_THRESHOLD = 0.5
DEFAULT_EMBEDDING_MODEL = "publishers/google/models/text-embedding-005"
DEFAULT_EMBEDDING_REQUESTS_PER_MIN = 1000

# Corpus to GCS Bucket Mapping (can be customized per agent later)
CORPUS_TO_BUCKET_MAPPING = {
    "ai-books": "ipad-book-collection",
    "general-docs": "develom-documents",
}

# Account-specific settings
ORGANIZATION_DOMAIN = os.environ.get("ORGANIZATION_DOMAIN", "develom.com")
DEFAULT_CORPUS_NAME = os.environ.get("DEFAULT_CORPUS_NAME", "ai-books")
