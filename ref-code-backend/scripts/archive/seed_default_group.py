#!/usr/bin/env python3
"""
Seed script to create default group, roles, and corpus entries.
"""

import sys
import os
import logging

# Add backend/src to path
backend_src = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, backend_src)

# Import after path setup
from database.migrations.run_migrations import main as run_migrations
from services.group_service import GroupService
from services.corpus_service import CorpusService
from models.group import GroupCreate, RoleCreate
from models.corpus import CorpusCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default groups
GROUPS = [
    {
        "name": "default-users",
        "description": "Default group for all users"
    },
    {
        "name": "admin-users",
        "description": "Administrative users with elevated privileges"
    },
    {
        "name": "develom-group",
        "description": "Develom organization users"
    }
]

# Default roles
ROLES = [
    {
        "name": "user",
        "description": "Standard user role",
        "permissions": [
            "read:own_profile",
            "update:own_profile",
            "read:own_corpora",
            "chat:own_agents",
            "read:agents",
            "switch:agents"
        ]
    },
    {
        "name": "corpus_admin",
        "description": "Corpus administrator",
        "permissions": [
            "create:corpus",
            "update:corpus",
            "delete:corpus",
            "manage:corpus_access",
            "read:all_corpora"
        ]
    },
    {
        "name": "system_admin",
        "description": "System administrator with full access",
        "permissions": ["*"]
    }
]

# Default corpora
# Note: Only reference existing corpora. Available: test-corpus, ai-books
CORPORA = [
    {
        "name": "ai-books",
        "display_name": "AI Books Collection",
        "gcs_bucket": "ipad-book-collection",
        "description": "Collection of AI and technology books"
    },
    {
        "name": "test-corpus",
        "display_name": "Test Corpus",
        "gcs_bucket": "test-bucket",
        "description": "Test corpus for development"
    }
]


def seed_default_data():
    """Seed default groups, roles, and corpora."""
    logger.info("Starting default data seeding...")
    
    # Run migrations first
    logger.info("Running database migrations...")
    run_migrations()
    
    # Seed groups
    logger.info("\n--- Seeding Groups ---")
    group_ids = {}
    for group_data in GROUPS:
        try:
            existing = GroupService.get_group_by_name(group_data["name"])
            if existing:
                logger.info(f"⏭️  Group '{group_data['name']}' already exists (ID: {existing.id})")
                group_ids[group_data["name"]] = existing.id
                continue
            
            group_create = GroupCreate(**group_data)
            group = GroupService.create_group(group_create)
            logger.info(f"✅ Created group: {group.name} (ID: {group.id})")
            group_ids[group_data["name"]] = group.id
            
        except Exception as e:
            logger.error(f"❌ Failed to create group '{group_data['name']}': {e}")
    
    # Seed roles
    logger.info("\n--- Seeding Roles ---")
    role_ids = {}
    for role_data in ROLES:
        try:
            existing = GroupService.get_role_by_name(role_data["name"])
            if existing:
                logger.info(f"⏭️  Role '{role_data['name']}' already exists (ID: {existing.id})")
                role_ids[role_data["name"]] = existing.id
                continue
            
            role_create = RoleCreate(**role_data)
            role = GroupService.create_role(role_create)
            logger.info(f"✅ Created role: {role.name} (ID: {role.id})")
            role_ids[role_data["name"]] = role.id
            
        except Exception as e:
            logger.error(f"❌ Failed to create role '{role_data['name']}': {e}")
    
    # Assign roles to groups
    logger.info("\n--- Assigning Roles to Groups ---")
    role_assignments = [
        ("default-users", "user"),
        ("admin-users", "system_admin"),
        ("develom-group", "user")
    ]
    
    for group_name, role_name in role_assignments:
        if group_name in group_ids and role_name in role_ids:
            try:
                success = GroupService.assign_role_to_group(
                    group_ids[group_name],
                    role_ids[role_name]
                )
                if success:
                    logger.info(f"✅ Assigned role '{role_name}' to group '{group_name}'")
            except Exception as e:
                logger.info(f"⏭️  Role assignment already exists or failed: {e}")
    
    # Seed corpora
    logger.info("\n--- Seeding Corpora ---")
    corpus_ids = {}
    for corpus_data in CORPORA:
        try:
            existing = CorpusService.get_corpus_by_name(corpus_data["name"])
            if existing:
                logger.info(f"⏭️  Corpus '{corpus_data['name']}' already exists (ID: {existing.id})")
                corpus_ids[corpus_data["name"]] = existing.id
                continue
            
            corpus_create = CorpusCreate(**corpus_data)
            corpus = CorpusService.create_corpus(corpus_create)
            logger.info(f"✅ Created corpus: {corpus.name} (ID: {corpus.id})")
            corpus_ids[corpus_data["name"]] = corpus.id
            
        except Exception as e:
            logger.error(f"❌ Failed to create corpus '{corpus_data['name']}': {e}")
    
    # Grant corpus access to groups
    logger.info("\n--- Granting Corpus Access ---")
    corpus_assignments = [
        ("default-users", "ai-books", "read"),
        ("develom-group", "ai-books", "write"),
        ("develom-group", "test-corpus", "read"),
        ("admin-users", "ai-books", "admin"),
        ("admin-users", "test-corpus", "admin")
    ]
    
    for group_name, corpus_name, permission in corpus_assignments:
        if group_name in group_ids and corpus_name in corpus_ids:
            try:
                success = CorpusService.grant_group_access(
                    group_ids[group_name],
                    corpus_ids[corpus_name],
                    permission
                )
                if success:
                    logger.info(f"✅ Granted {permission} access to '{corpus_name}' for group '{group_name}'")
            except Exception as e:
                logger.info(f"⏭️  Corpus access already exists or failed: {e}")
    
    logger.info(f"\n{'='*60}")
    logger.info("Default Data Seeding Complete!")
    logger.info(f"{'='*60}\n")


if __name__ == "__main__":
    seed_default_data()
