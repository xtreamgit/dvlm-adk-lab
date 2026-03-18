"""
Configuration settings for the RAG Agent - USFS Account
Account: usfs (U.S. Forest Service)
Project: usfs-rag-agent (update with actual project)
Region: us-central1 (update with actual region)

These settings are used by the various RAG tools.
Vertex AI initialization is performed in the package's __init__.py
"""

import os

# Account identifier
ACCOUNT_NAME = "usfs"
ACCOUNT_DESCRIPTION = "U.S. Forest Service Account"

# Vertex AI settings
PROJECT_ID = os.environ.get("PROJECT_ID", "usfs-gcp-arch-testing")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-east4")

# RAG settings
DEFAULT_CHUNK_SIZE = 512
DEFAULT_CHUNK_OVERLAP = 100
DEFAULT_TOP_K = 5  # USFS may want more results
DEFAULT_DISTANCE_THRESHOLD = 0.5
DEFAULT_EMBEDDING_MODEL = "publishers/google/models/text-embedding-005"
DEFAULT_EMBEDDING_REQUESTS_PER_MIN = 1000

# Corpus to GCS Bucket Mapping
# This dictionary maps a corpus's display name to the GCS bucket where its files are stored.
# This is necessary because the corpus name in Vertex AI may not match the GCS bucket name.
# Add new mappings here as needed.
CORPUS_TO_BUCKET_MAPPING = {
    "forest-policies": "usfs-forest-policies",
    "environmental-reports": "usfs-environmental-reports",
    "fire-management": "usfs-fire-management-docs",
}

# Account-specific settings
ORGANIZATION_DOMAIN = "usda.gov"
DEFAULT_CORPUS_NAME = "usfs-forest-service"
