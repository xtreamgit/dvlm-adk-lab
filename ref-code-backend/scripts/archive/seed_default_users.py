"""
Seed default users for development/testing.
This runs automatically on server startup if no users exist.
Also syncs corpora from Vertex AI.

Note: Legacy groups/user_groups/roles tables have been removed.
Group membership is now managed via Google Groups Bridge → chatbot_groups.
"""

import logging
from database.repositories.user_repository import UserRepository
from database.repositories.corpus_repository import CorpusRepository
from database.connection import get_db_connection
from services.auth_service import AuthService

logger = logging.getLogger(__name__)


def _ensure_chatbot_admin_group() -> int:
    """Ensure the admin-group exists in chatbot_groups. Returns its ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM chatbot_groups WHERE name = 'admin-group'"
        )
        row = cursor.fetchone()
        if row:
            return row['id']
        cursor.execute(
            "INSERT INTO chatbot_groups (name, description) "
            "VALUES ('admin-group', 'Administrative group with full corpus and document control') "
            "ON CONFLICT (name) DO UPDATE SET updated_at = CURRENT_TIMESTAMP "
            "RETURNING id"
        )
        conn.commit()
        return cursor.fetchone()['id']


def _ensure_chatbot_user(user_dict: dict, admin_group_id: int):
    """Ensure a chatbot_users record exists and is assigned to admin-group."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chatbot_users (username, email, full_name, is_active) "
            "VALUES (%s, %s, %s, TRUE) "
            "ON CONFLICT (email) DO UPDATE SET updated_at = CURRENT_TIMESTAMP "
            "RETURNING id",
            (user_dict['email'].split('@')[0], user_dict['email'], user_dict['full_name']),
        )
        chatbot_user_id = cursor.fetchone()['id']
        cursor.execute(
            "INSERT INTO chatbot_user_groups (chatbot_user_id, chatbot_group_id) "
            "VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (chatbot_user_id, admin_group_id),
        )
        conn.commit()


def seed_default_users():
    """Create default users if none exist."""
    try:
        # Check if any users exist
        all_users = UserRepository.get_all()
        if all_users:
            logger.info(f"Users already exist ({len(all_users)} users), skipping seed")
            return
        
        logger.info("🌱 Seeding default users...")
        
        # Ensure admin chatbot group exists
        admin_group_id = _ensure_chatbot_admin_group()
        logger.info(f"✅ Admin chatbot group ready (ID: {admin_group_id})")
        
        # Create default users
        default_users = [
            {
                'username': 'hector',
                'email': 'hector@develom.com',
                'password': 'hector123',
                'full_name': 'Hector DeJesus'
            },
        ]
        
        for user_data in default_users:
            # Hash password
            hashed_password = AuthService.hash_password(user_data['password'])
            
            # Create user in users table
            user = UserRepository.create(
                username=user_data['username'],
                email=user_data['email'],
                full_name=user_data['full_name'],
                hashed_password=hashed_password
            )
            
            logger.info(f"✅ Created user: {user_data['username']} (ID: {user['id']})")
            
            # Also create chatbot_users record and assign to admin group
            _ensure_chatbot_user(user, admin_group_id)
            logger.info(f"   Added {user_data['username']} to admin-group (chatbot)")
        
        logger.info("✅ Default users seeded successfully")
        
        # Sync corpora from Vertex AI
        try:
            sync_corpora_from_vertex_ai()
        except Exception as e:
            logger.warning(f"⚠️  Failed to sync corpora (non-critical): {e}")
        
    except Exception as e:
        logger.error(f"❌ Failed to seed default users: {e}")
        raise


def sync_corpora_from_vertex_ai():
    """Sync corpora from Vertex AI into the local database."""
    try:
        import vertexai
        from vertexai import rag
        from rag_agent.config import PROJECT_ID, LOCATION
        
        logger.info("🔄 Syncing corpora from Vertex AI...")
        
        # Initialize Vertex AI
        import google.auth
        credentials, _ = google.auth.default()
        vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)
        
        # Fetch corpora from Vertex AI
        vertex_corpora = list(rag.list_corpora())
        logger.info(f"📚 Found {len(vertex_corpora)} corpora in Vertex AI")
        
        # Get existing corpora from database
        db_corpora = CorpusRepository.get_all(active_only=False)
        db_corpus_names = {c['name']: c for c in db_corpora}
        
        # Add new corpora from Vertex AI
        added_count = 0
        for vertex_corpus in vertex_corpora:
            corpus_name = vertex_corpus.display_name
            
            if corpus_name not in db_corpus_names:
                # Create corpus in database
                CorpusRepository.create(
                    name=corpus_name,
                    display_name=corpus_name,
                    gcs_bucket=f"gs://adk-rag-ma-{corpus_name}",
                    description=f"Synced from Vertex AI",
                    vertex_corpus_id=vertex_corpus.name
                )
                logger.info(f"   ✅ Added corpus: {corpus_name}")
                added_count += 1
        
        logger.info(f"✅ Corpus sync complete: {added_count} new corpora added")
        
    except Exception as e:
        logger.warning(f"⚠️  Corpus sync failed (non-critical): {e}")
        # Don't raise - this is non-critical for startup
