#!/usr/bin/env python3
"""
Database Migration Runner
Note: PostgreSQL schema is managed by schema_init.py.
This file is kept for backward compatibility.
"""

import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use local path for development, Cloud Run path in production
if os.path.exists("/app/data"):
    DEFAULT_DB_PATH = "/app/data/users.db"
else:
    # Local development - use ./data relative to backend directory
    backend_dir = Path(__file__).parent.parent.parent.parent
    DEFAULT_DB_PATH = str(backend_dir / "data" / "users.db")

DATABASE_PATH = os.getenv("DATABASE_PATH", DEFAULT_DB_PATH)


def run_all_migrations():
    """
    PostgreSQL schema is managed by schema_init.py.
    This function is kept for backward compatibility but does nothing.
    """
    logger.info("⏭️  Migrations skipped - PostgreSQL schema managed by schema_init.py")
    return True


if __name__ == "__main__":
    import sys
    success = run_all_migrations()
    sys.exit(0 if success else 1)
