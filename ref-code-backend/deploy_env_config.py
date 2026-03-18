#!/usr/bin/env python3
"""
Environment Configuration Generator for Multi-Client Deployments
================================================================

Reads a client environment YAML file and generates all necessary
configuration files for deployment:

1. deployment.config — used by infrastructure/deploy-all.sh
2. backend/.env.local — local development environment variables
3. backend/config/<account>/config.py — account-specific Python config

Features:
- Validates all required values before writing
- Backs up existing files before overwriting
- Supports dry-run mode to preview changes
- Can generate configs for any client from a single YAML source

Usage:
    # Generate all configs for a client
    python deploy_env_config.py --env environments/develom.yaml

    # Dry run — preview what would be generated
    python deploy_env_config.py --env environments/develom.yaml --dry-run

    # Generate only deployment.config
    python deploy_env_config.py --env environments/develom.yaml --only deployment

    # Generate only .env.local
    python deploy_env_config.py --env environments/develom.yaml --only env-local

    # Generate only account config.py
    python deploy_env_config.py --env environments/develom.yaml --only account-config

Author: ADK RAG Agent Team
Date: 2026-02-08
"""

import argparse
import logging
import os
import shutil
import sys
from datetime import datetime
from typing import Optional

import yaml

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("deploy_env_config")

# Colors
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BLUE = "\033[0;34m"
BOLD = "\033[1m"
NC = "\033[0m"


def c_green(t): return f"{GREEN}{t}{NC}"
def c_yellow(t): return f"{YELLOW}{t}{NC}"
def c_red(t): return f"{RED}{t}{NC}"
def c_blue(t): return f"{BLUE}{t}{NC}"
def c_bold(t): return f"{BOLD}{t}{NC}"


# ---------------------------------------------------------------------------
# Project root detection
# ---------------------------------------------------------------------------

def find_project_root() -> str:
    """Find the project root directory (contains infrastructure/ and backend/)."""
    # Start from this script's location and walk up
    current = os.path.dirname(os.path.abspath(__file__))
    for _ in range(5):
        if os.path.isdir(os.path.join(current, "infrastructure")) and os.path.isdir(os.path.join(current, "backend")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent

    # Fallback: assume script is in backend/
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def load_env_config(env_path: str) -> dict:
    """Load and validate client environment YAML."""
    abs_path = os.path.abspath(env_path)
    if not os.path.exists(abs_path):
        logger.error(f"Environment file not found: {abs_path}")
        sys.exit(1)

    with open(abs_path, "r") as f:
        config = yaml.safe_load(f)

    # Validate required fields
    required = {
        "client_name": "Client name identifier",
        "account_env": "Account environment name",
        "project_id": "Google Cloud Project ID",
        "region": "Google Cloud region",
        "organization_domain": "Organization domain",
        "database": "Database configuration section",
    }

    errors = []
    for key, desc in required.items():
        val = config.get(key)
        if not val:
            errors.append(f"  Missing: {key} ({desc})")
        elif isinstance(val, str) and val.startswith("CHANGE_ME"):
            errors.append(f"  Not configured: {key} — still has template value")

    if errors:
        logger.error(f"Validation errors in {abs_path}:")
        for e in errors:
            logger.error(e)
        sys.exit(1)

    return config


# ---------------------------------------------------------------------------
# Backup helper
# ---------------------------------------------------------------------------

def backup_file(filepath: str) -> Optional[str]:
    """Create a timestamped backup of a file if it exists."""
    if not os.path.exists(filepath):
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{filepath}.bak.{timestamp}"
    shutil.copy2(filepath, backup_path)
    logger.info(f"  Backed up: {os.path.basename(filepath)} → {os.path.basename(backup_path)}")
    return backup_path


# ---------------------------------------------------------------------------
# Generator: deployment.config
# ---------------------------------------------------------------------------

def generate_deployment_config(config: dict, project_root: str, dry_run: bool = False) -> str:
    """Generate deployment.config file content."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    content = f"""# Deployment Configuration
# Generated by deploy_env_config.py on {timestamp}
# Client: {config['client_name']}
# DO NOT EDIT MANUALLY — regenerate with:
#   python backend/deploy_env_config.py --env environments/{config['client_name']}.yaml

PROJECT_ID="{config['project_id']}"
PROJECT_NUMBER="{config.get('project_number', '')}"
REGION="{config['region']}"
ORGANIZATION_DOMAIN="{config['organization_domain']}"
IAP_ADMIN_USER="{config.get('iap_admin_user', '')}"
REPO="{config.get('repo', 'cloud-run-repo1')}"
ACCOUNT_ENV="{config['account_env']}"

# Database
DB_NAME="{config['database']['name']}"
DB_USER="{config['database']['user']}"
CLOUD_SQL_INSTANCE="{config['database']['cloud_sql_instance']}"
CLOUD_SQL_CONNECTION="{config['database'].get('cloud_sql_connection', '')}"

# Container images (auto-derived)
BACKEND_IMAGE="{config['region']}-docker.pkg.dev/{config['project_id']}/{config.get('repo', 'cloud-run-repo1')}/backend:latest"
FRONTEND_IMAGE="{config['region']}-docker.pkg.dev/{config['project_id']}/{config.get('repo', 'cloud-run-repo1')}/frontend:latest"

# Service accounts (auto-derived if empty)
BACKEND_SA="{config.get('service_accounts', {}).get('backend_sa', '') or f'backend-sa@{config["project_id"]}.iam.gserviceaccount.com'}"
FRONTEND_SA="{config.get('service_accounts', {}).get('frontend_sa', '') or f'frontend-sa@{config["project_id"]}.iam.gserviceaccount.com'}"
RAG_AGENT_SA="{config.get('service_accounts', {}).get('rag_agent_sa', '') or f'rag-agent-sa@{config["project_id"]}.iam.gserviceaccount.com'}"
"""

    filepath = os.path.join(project_root, "deployment.config")

    if dry_run:
        logger.info(f"\n{c_yellow('[DRY RUN]')} Would write: {filepath}")
        logger.info(f"  Content preview (first 10 lines):")
        for line in content.strip().split("\n")[:10]:
            logger.info(f"    {line}")
        return content

    backup_file(filepath)
    with open(filepath, "w") as f:
        f.write(content)
    logger.info(f"  {c_green('✓')} Generated: {filepath}")
    return content


# ---------------------------------------------------------------------------
# Generator: backend/.env.local
# ---------------------------------------------------------------------------

def generate_env_local(config: dict, project_root: str, dry_run: bool = False) -> str:
    """Generate backend/.env.local file content."""
    db = config["database"]
    local_db = db.get("local", {})
    vertex = config.get("vertex_ai", {})
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    content = f"""# Local Development Environment Variables
# Generated by deploy_env_config.py on {timestamp}
# Client: {config['client_name']}
# DO NOT EDIT MANUALLY — regenerate with:
#   python backend/deploy_env_config.py --env environments/{config['client_name']}.yaml

# PostgreSQL Local Database
DB_HOST={local_db.get('host', 'localhost')}
DB_PORT={local_db.get('port', 5433)}
DB_NAME={local_db.get('name', 'adk_agents_db_dev')}
DB_USER={local_db.get('user', 'adk_dev_user')}
DB_PASSWORD={local_db.get('password', 'dev_password_123')}

# Google Cloud / Vertex AI
PROJECT_ID={config['project_id']}
GOOGLE_CLOUD_LOCATION={vertex.get('location', config['region'])}
VERTEXAI_PROJECT={config['project_id']}
VERTEXAI_LOCATION={vertex.get('location', config['region'])}

# Account Environment
ACCOUNT_ENV={config['account_env']}

# Application
LOG_LEVEL=DEBUG
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Cloud Database (for sync tool — requires Cloud SQL Proxy running)
CLOUD_DB_HOST=localhost
CLOUD_DB_PORT=5434
CLOUD_DB_NAME={db.get('name', 'adk_agents_db')}
CLOUD_DB_USER={db.get('user', 'adk_app_user')}
CLOUD_DB_PASSWORD={db.get('password', '')}
"""

    # Add project number if available
    if config.get("project_number"):
        content += f"""
# IAP Configuration
PROJECT_NUMBER={config['project_number']}
"""

    filepath = os.path.join(project_root, "backend", ".env.local")

    if dry_run:
        logger.info(f"\n{c_yellow('[DRY RUN]')} Would write: {filepath}")
        logger.info(f"  Content preview (first 10 lines):")
        for line in content.strip().split("\n")[:10]:
            logger.info(f"    {line}")
        return content

    backup_file(filepath)
    with open(filepath, "w") as f:
        f.write(content)
    logger.info(f"  {c_green('✓')} Generated: {filepath}")
    return content


# ---------------------------------------------------------------------------
# Generator: backend/config/<account>/config.py
# ---------------------------------------------------------------------------

def generate_account_config(config: dict, project_root: str, dry_run: bool = False) -> str:
    """Generate backend/config/<account>/config.py file content."""
    account = config["account_env"]
    vertex = config.get("vertex_ai", {})
    rag = config.get("rag", {})
    corpus_mapping = config.get("corpus_to_bucket_mapping", {})
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Format corpus mapping as Python dict
    mapping_lines = []
    for corpus_name, bucket_name in corpus_mapping.items():
        mapping_lines.append(f'    "{corpus_name}": "{bucket_name}",')
    mapping_str = "\n".join(mapping_lines) if mapping_lines else '    # No mappings configured'

    content = f'''"""
Configuration settings for the RAG Agent - {config['client_name'].upper()} Account
Account: {account}
Project: {config['project_id']}
Region: {config['region']}

Generated by deploy_env_config.py on {timestamp}
DO NOT EDIT MANUALLY — regenerate with:
  python backend/deploy_env_config.py --env environments/{config['client_name']}.yaml
"""

import os

# Account identifier
ACCOUNT_NAME = "{account}"
ACCOUNT_DESCRIPTION = "{config['client_name'].title()} Account"

# Vertex AI settings
PROJECT_ID = os.environ.get("PROJECT_ID", "{config['project_id']}")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "{vertex.get('location', config['region'])}")

# RAG settings
DEFAULT_CHUNK_SIZE = {rag.get('default_chunk_size', 512)}
DEFAULT_CHUNK_OVERLAP = {rag.get('default_chunk_overlap', 100)}
DEFAULT_TOP_K = {rag.get('default_top_k', 3)}
DEFAULT_DISTANCE_THRESHOLD = {rag.get('default_distance_threshold', 0.5)}
DEFAULT_EMBEDDING_MODEL = "{vertex.get('embedding_model', 'publishers/google/models/text-embedding-005')}"
DEFAULT_EMBEDDING_REQUESTS_PER_MIN = {vertex.get('embedding_requests_per_min', 1000)}

# Corpus to GCS Bucket Mapping
CORPUS_TO_BUCKET_MAPPING = {{
{mapping_str}
}}

# Account-specific settings
ORGANIZATION_DOMAIN = "{config['organization_domain']}"
DEFAULT_CORPUS_NAME = "{config.get('default_corpus_name', '')}"
'''

    config_dir = os.path.join(project_root, "backend", "config", account)
    filepath = os.path.join(config_dir, "config.py")

    if dry_run:
        logger.info(f"\n{c_yellow('[DRY RUN]')} Would write: {filepath}")
        logger.info(f"  Content preview (first 10 lines):")
        for line in content.strip().split("\n")[:10]:
            logger.info(f"    {line}")
        return content

    # Create directory if needed
    os.makedirs(config_dir, exist_ok=True)

    # Create __init__.py if it doesn't exist
    init_path = os.path.join(config_dir, "__init__.py")
    if not os.path.exists(init_path):
        with open(init_path, "w") as f:
            f.write(f'"""Configuration for {config["client_name"]} account."""\n')
        logger.info(f"  {c_green('✓')} Created: {init_path}")

    backup_file(filepath)
    with open(filepath, "w") as f:
        f.write(content)
    logger.info(f"  {c_green('✓')} Generated: {filepath}")
    return content


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate deployment configuration files from client environment YAML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all configs
  python deploy_env_config.py --env environments/develom.yaml

  # Dry run
  python deploy_env_config.py --env environments/develom.yaml --dry-run

  # Generate only deployment.config
  python deploy_env_config.py --env environments/develom.yaml --only deployment

  # Generate only .env.local
  python deploy_env_config.py --env environments/develom.yaml --only env-local

  # Generate only account config.py
  python deploy_env_config.py --env environments/develom.yaml --only account-config
        """,
    )

    parser.add_argument("--env", required=True, help="Path to client environment YAML file")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files")
    parser.add_argument(
        "--only",
        choices=["deployment", "env-local", "account-config"],
        help="Generate only a specific config file",
    )

    args = parser.parse_args()

    # Load config
    config = load_env_config(args.env)
    project_root = find_project_root()

    logger.info(f"\n{'='*60}")
    logger.info(f"  {c_bold('Environment Configuration Generator')}")
    logger.info(f"  Client:  {c_blue(config['client_name'])}")
    logger.info(f"  Account: {config['account_env']}")
    logger.info(f"  Project: {config['project_id']}")
    logger.info(f"  Region:  {config['region']}")
    logger.info(f"  Root:    {project_root}")
    logger.info(f"{'='*60}\n")

    generated = []

    if args.only is None or args.only == "deployment":
        logger.info(f"{c_blue('━' * 50)}")
        logger.info(f"  Generating: deployment.config")
        logger.info(f"{c_blue('━' * 50)}")
        generate_deployment_config(config, project_root, dry_run=args.dry_run)
        generated.append("deployment.config")

    if args.only is None or args.only == "env-local":
        logger.info(f"\n{c_blue('━' * 50)}")
        logger.info(f"  Generating: backend/.env.local")
        logger.info(f"{c_blue('━' * 50)}")
        generate_env_local(config, project_root, dry_run=args.dry_run)
        generated.append("backend/.env.local")

    if args.only is None or args.only == "account-config":
        logger.info(f"\n{c_blue('━' * 50)}")
        logger.info(f"  Generating: backend/config/{config['account_env']}/config.py")
        logger.info(f"{c_blue('━' * 50)}")
        generate_account_config(config, project_root, dry_run=args.dry_run)
        generated.append(f"backend/config/{config['account_env']}/config.py")

    # Summary
    mode = c_yellow("[DRY RUN]") if args.dry_run else c_green("[COMPLETE]")
    logger.info(f"\n{'='*60}")
    logger.info(f"  Configuration Generation {mode}")
    logger.info(f"  Files generated: {', '.join(generated)}")
    logger.info(f"{'='*60}\n")


if __name__ == "__main__":
    main()
