"""
Vertex AI RAG Agent

A package for interacting with Google Cloud Vertex AI RAG capabilities.
"""

import vertexai

# Import config to get PROJECT_ID and LOCATION
from . import config

# Initialize Vertex AI at package load time
try:
    import os
    print(f"DEBUG: Raw env vars - PROJECT_ID={os.environ.get('PROJECT_ID')}, GOOGLE_CLOUD_LOCATION={os.environ.get('GOOGLE_CLOUD_LOCATION')}")
    print(f"DEBUG: Config values - PROJECT_ID={config.PROJECT_ID}, LOCATION={config.LOCATION}")
    
    if config.PROJECT_ID and config.LOCATION:
        print(f"Initializing Vertex AI with project={config.PROJECT_ID}, location={config.LOCATION}")
        
        # Try direct initialization without relying on default credentials
        import google.auth
        credentials, project = google.auth.default()
        print(f"DEBUG: Google auth project={project}, credentials type={type(credentials)}")
        
        vertexai.init(project=config.PROJECT_ID, location=config.LOCATION, credentials=credentials)
        print("Vertex AI initialization successful")
    else:
        print(
            f"Missing Vertex AI configuration. PROJECT_ID={config.PROJECT_ID}, LOCATION={config.LOCATION}. "
            f"Tools requiring Vertex AI may not work properly."
        )
except Exception as e:
    print(f"Failed to initialize Vertex AI: {str(e)}")
    print(f"Exception type: {type(e)}")
    import traceback
    print(f"Traceback: {traceback.format_exc()}")
    print("Please check your Google Cloud credentials and project settings.")

# Import agent after initialization is complete
from . import agent
