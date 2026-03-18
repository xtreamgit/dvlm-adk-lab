"""
Configuration settings for the RAG Agent.

These settings are used by the various RAG tools.
Vertex AI initialization is performed in the package's __init__.py
"""

import os

# Vertex AI settings
PROJECT_ID = os.environ.get("PROJECT_ID", "adk-rag-ma")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-west1")

# RAG settings
DEFAULT_CHUNK_SIZE = 512
DEFAULT_CHUNK_OVERLAP = 100
DEFAULT_TOP_K = 3
DEFAULT_DISTANCE_THRESHOLD = 0.5
DEFAULT_EMBEDDING_MODEL = "publishers/google/models/text-embedding-005"
DEFAULT_EMBEDDING_REQUESTS_PER_MIN = 1000

# Corpus to GCS Bucket Mapping
# This dictionary maps a corpus's display name to the GCS bucket where its files are stored.
# This is necessary because the corpus name in Vertex AI may not match the GCS bucket name.
# Add new mappings here as needed.
CORPUS_TO_BUCKET_MAPPING = {
    "ai-books": "ipad-book-collection",
}
