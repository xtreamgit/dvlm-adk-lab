#!/usr/bin/env python3
"""
Script to create an admin user with full access.
"""

import sys
import os
import logging
import getpass

# Add backend/src to path
backend_src = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, backend_src)

# Import after path setup
from database.migrations.run_migrations import main as run_migrations
from services.user_service import UserService
from services.group_service import GroupService
from services.agent_service import AgentService
from models.user import UserCreate
from database.repositories.agent_repository import AgentRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_admin_user(username: str = None, email: str = None, password: str = None):
    """Create an admin user with access to all agents."""
    
    # Run migrations first
    logger.info("Running database migrations...")
    run_migrations()
    
    # Get admin user details
    if not username:
        username = input("Enter admin username: ").strip()
    if not email:
        email = input("Enter admin email: ").strip()
    if not password:
        password = getpass.getpass("Enter admin password: ")
        password_confirm = getpass.getpass("Confirm password: ")
        if password != password_confirm:
            logger.error("Passwords do not match!")
            return False
    
    try:
        # Check if user already exists
        existing = UserService.get_user_by_username(username)
        if existing:
            logger.error(f"User '{username}' already exists!")
            return False
        
        # Create user
        user_create = UserCreate(
            username=username,
            email=email,
            password=password,
            full_name=f"Admin User - {username}"
        )
        user = UserService.create_user(user_create)
        logger.info(f"✅ Created user: {user.username} (ID: {user.id})")
        
        # Add user to admin-users group
        admin_group = GroupService.get_group_by_name("admin-users")
        if admin_group:
            UserService.add_user_to_group(user.id, admin_group.id)
            logger.info(f"✅ Added user to 'admin-users' group")
        else:
            logger.warning("'admin-users' group not found. Run seed_default_group.py first.")
        
        # Add user to default-users group
        default_group = GroupService.get_group_by_name("default-users")
        if default_group:
            UserService.add_user_to_group(user.id, default_group.id)
            logger.info(f"✅ Added user to 'default-users' group")
        
        # Grant access to all agents
        agents = AgentService.get_all_agents()
        for agent in agents:
            AgentService.grant_user_access(user.id, agent.id)
            logger.info(f"✅ Granted access to agent: {agent.name}")
        
        # Set default agent to "default-agent"
        default_agent = AgentService.get_agent_by_name("default-agent")
        if default_agent:
            UserService.set_default_agent(user.id, default_agent.id)
            logger.info(f"✅ Set default agent to: {default_agent.name}")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Admin user created successfully!")
        logger.info(f"  Username: {user.username}")
        logger.info(f"  Email: {user.email}")
        logger.info(f"  User ID: {user.id}")
        logger.info(f"{'='*60}\n")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create admin user: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create an admin user")
    parser.add_argument("--username", help="Admin username")
    parser.add_argument("--email", help="Admin email")
    parser.add_argument("--password", help="Admin password (not recommended, use interactive mode)")
    
    args = parser.parse_args()
    
    create_admin_user(
        username=args.username,
        email=args.email,
        password=args.password
    )
