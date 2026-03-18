#!/usr/bin/env python3
"""
Create Vertex AI Search & Conversation data store and import documents.

This script uses the newer Vertex AI Search API instead of the deprecated RAG API.
"""

import os
import sys
import asyncio
import asyncpg
from datetime import datetime
from google.cloud import discoveryengine_v1 as discoveryengine
from google.api_core import operation
from google.api_core import exceptions

# Configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "dvlm-adk-lab")
LOCATION = "global"  # Vertex AI Search uses global location
DATA_STORE_ID = "default-corpus-datastore"
DATA_STORE_DISPLAY_NAME = "Default Corpus Data Store"
BUCKET_NAME = "adk-rag-default-corpus-bucket-dvlm-adk-lab"
CORPUS_NAME = "default-corpus"

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "adk_rag_production")
DB_USER = os.getenv("DB_USER", os.getenv("USER", "postgres"))
DB_PASSWORD = os.getenv("DB_PASSWORD", "")


def create_data_store(project_id: str, location: str, data_store_id: str, display_name: str):
    """Create a Vertex AI Search data store."""
    print(f"\n📚 Creating Vertex AI Search data store: {data_store_id}")
    
    client = discoveryengine.DataStoreServiceClient()
    
    # Check if data store already exists
    data_store_name = f"projects/{project_id}/locations/{location}/collections/default_collection/dataStores/{data_store_id}"
    
    try:
        existing_store = client.get_data_store(name=data_store_name)
        print(f"✅ Data store already exists: {existing_store.name}")
        return existing_store.name
    except exceptions.NotFound:
        pass
    
    # Create new data store
    parent = f"projects/{project_id}/locations/{location}/collections/default_collection"
    
    data_store = discoveryengine.DataStore(
        display_name=display_name,
        industry_vertical=discoveryengine.IndustryVertical.GENERIC,
        solution_types=[discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH],
        content_config=discoveryengine.DataStore.ContentConfig.CONTENT_REQUIRED,
    )
    
    request = discoveryengine.CreateDataStoreRequest(
        parent=parent,
        data_store=data_store,
        data_store_id=data_store_id,
    )
    
    try:
        operation_result = client.create_data_store(request=request)
        print("⏳ Waiting for data store creation to complete...")
        response = operation_result.result(timeout=300)
        print(f"✅ Created data store: {response.name}")
        return response.name
    except Exception as e:
        print(f"❌ Error creating data store: {e}")
        raise


def import_documents(project_id: str, location: str, data_store_id: str, bucket_name: str):
    """Import documents from GCS into the data store."""
    print(f"\n📥 Importing documents from gs://{bucket_name}/documents/")
    
    client = discoveryengine.DocumentServiceClient()
    
    parent = f"projects/{project_id}/locations/{location}/collections/default_collection/dataStores/{data_store_id}/branches/default_branch"
    
    gcs_source = discoveryengine.GcsSource(
        input_uris=[f"gs://{bucket_name}/documents/*.pdf"],
        data_schema="document",
    )
    
    request = discoveryengine.ImportDocumentsRequest(
        parent=parent,
        gcs_source=gcs_source,
        reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
    )
    
    try:
        operation_result = client.import_documents(request=request)
        print("⏳ Waiting for document import to complete (this may take several minutes)...")
        response = operation_result.result(timeout=1800)  # 30 minutes timeout
        
        print(f"✅ Document import completed")
        
        # Check if response has error_samples field
        if hasattr(response, 'error_samples') and response.error_samples:
            print(f"⚠️  Some documents may have failed to import. Error samples:")
            for error in response.error_samples[:5]:
                print(f"   - {error}")
        else:
            print(f"   All documents imported successfully")
        
        return response
        
    except Exception as e:
        print(f"❌ Error importing documents: {e}")
        raise


def create_search_engine(project_id: str, location: str, data_store_id: str):
    """Create a search engine (app) for the data store."""
    print(f"\n🔍 Creating search engine for data store")
    
    client = discoveryengine.EngineServiceClient()
    
    engine_id = f"{data_store_id}-engine"
    engine_name = f"projects/{project_id}/locations/{location}/collections/default_collection/engines/{engine_id}"
    
    # Check if engine already exists
    try:
        existing_engine = client.get_engine(name=engine_name)
        print(f"✅ Search engine already exists: {existing_engine.name}")
        return existing_engine.name
    except exceptions.NotFound:
        pass
    
    parent = f"projects/{project_id}/locations/{location}/collections/default_collection"
    data_store_name = f"projects/{project_id}/locations/{location}/collections/default_collection/dataStores/{data_store_id}"
    
    engine = discoveryengine.Engine(
        display_name=f"{DATA_STORE_DISPLAY_NAME} Engine",
        solution_type=discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH,
        search_engine_config=discoveryengine.Engine.SearchEngineConfig(
            search_tier=discoveryengine.SearchTier.SEARCH_TIER_STANDARD,
            search_add_ons=[discoveryengine.SearchAddOn.SEARCH_ADD_ON_LLM],
        ),
        data_store_ids=[data_store_id],
    )
    
    request = discoveryengine.CreateEngineRequest(
        parent=parent,
        engine=engine,
        engine_id=engine_id,
    )
    
    try:
        operation_result = client.create_engine(request=request)
        print("⏳ Waiting for search engine creation to complete...")
        response = operation_result.result(timeout=300)
        print(f"✅ Created search engine: {response.name}")
        return response.name
    except Exception as e:
        print(f"❌ Error creating search engine: {e}")
        raise


async def update_database(corpus_id: str, vertex_search_id: str):
    """Update the database with the Vertex AI Search data store ID."""
    print(f"\n💾 Updating database with Vertex AI Search information")
    
    conn = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    
    try:
        await conn.execute(
            """
            UPDATE corpora 
            SET vertex_rag_corpus_id = $1, updated_at = $2
            WHERE corpus_name = $3
            """,
            vertex_search_id,
            datetime.utcnow(),
            CORPUS_NAME
        )
        print(f"✅ Updated database with Vertex AI Search data store ID")
        
    finally:
        await conn.close()


async def main():
    """Main setup function."""
    print("=" * 80)
    print("Vertex AI Search & Conversation Setup")
    print("=" * 80)
    
    print(f"\nConfiguration:")
    print(f"  Project ID: {PROJECT_ID}")
    print(f"  Location: {LOCATION}")
    print(f"  Data Store ID: {DATA_STORE_ID}")
    print(f"  Bucket: gs://{BUCKET_NAME}")
    
    try:
        # Step 1: Create data store
        data_store_name = create_data_store(
            PROJECT_ID, LOCATION, DATA_STORE_ID, DATA_STORE_DISPLAY_NAME
        )
        
        # Step 2: Import documents
        import_result = import_documents(
            PROJECT_ID, LOCATION, DATA_STORE_ID, BUCKET_NAME
        )
        
        # Step 3: Create search engine
        engine_name = create_search_engine(
            PROJECT_ID, LOCATION, DATA_STORE_ID
        )
        
        # Step 4: Update database
        await update_database("ada80efa-0d46-4e80-8f8a-17647eafa311", data_store_name)
        
        print("\n" + "=" * 80)
        print("✅ Vertex AI Search Setup Complete!")
        print("=" * 80)
        print(f"\nData Store: {data_store_name}")
        print(f"Search Engine: {engine_name}")
        print(f"\nYou can now query documents through the Vertex AI Search API")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
