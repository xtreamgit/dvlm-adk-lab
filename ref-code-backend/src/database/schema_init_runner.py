#!/usr/bin/env python3
"""
Standalone runner for schema initialization.
Used by Cloud Run job to create database schema on first deploy.
"""
import sys
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

sys.path.insert(0, '/app/src')

from database.schema_init import initialize_schema

logger.info("Starting schema initialization...")
try:
    initialize_schema()
    logger.info("Schema initialization complete.")
    sys.exit(0)
except Exception as e:
    logger.error(f"Schema initialization failed: {e}")
    sys.exit(1)
