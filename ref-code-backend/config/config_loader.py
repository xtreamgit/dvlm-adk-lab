"""
Configuration Loader Utility

This module provides functions to load account-specific configurations
based on the ACCOUNT_ENV environment variable.

Usage:
    import os
    from config.config_loader import load_config, load_agent
    
    account_env = os.environ.get("ACCOUNT_ENV", "develom")
    config = load_config(account_env)
    agent = load_agent(account_env)
"""

import os
import sys
import importlib.util
from pathlib import Path
from typing import Any

# Valid account identifiers
# NOTE: This list is intentionally simple to extend; to add a new agent,
# create backend/config/<agent>/ and add the identifier here.
VALID_ACCOUNTS = [
    "develom",
    "usfs",
    "tt",
    "agent1",
    "agent2",
    "agent3",
]

# Get the config directory path
CONFIG_DIR = Path(__file__).parent


def get_account_env() -> str:
    """
    Get the current account environment from ACCOUNT_ENV variable.
    
    Returns:
        str: Account identifier (develom, usfs, or tt)
    
    Raises:
        ValueError: If ACCOUNT_ENV is set to an invalid account
    """
    account = os.environ.get("ACCOUNT_ENV", "develom")
    
    if account not in VALID_ACCOUNTS:
        raise ValueError(
            f"Invalid ACCOUNT_ENV: {account}. "
            f"Valid options are: {', '.join(VALID_ACCOUNTS)}"
        )
    
    return account


def load_config(account: str = None) -> Any:
    """
    Load account-specific configuration module.
    
    Args:
        account: Account identifier. If None, uses ACCOUNT_ENV environment variable.
    
    Returns:
        Loaded config module with account-specific settings
    
    Raises:
        ValueError: If account is invalid
        FileNotFoundError: If config file doesn't exist for account
        
    Example:
        >>> config = load_config("usfs")
        >>> print(config.PROJECT_ID)
        usfs-rag-agent
        >>> print(config.ACCOUNT_NAME)
        usfs
    """
    if account is None:
        account = get_account_env()
    
    if account not in VALID_ACCOUNTS:
        raise ValueError(
            f"Invalid account: {account}. "
            f"Valid options are: {', '.join(VALID_ACCOUNTS)}"
        )
    
    config_path = CONFIG_DIR / account / "config.py"
    
    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            f"Expected location: backend/config/{account}/config.py"
        )
    
    # Load the module dynamically
    spec = importlib.util.spec_from_file_location(
        f"config.{account}.config",
        config_path
    )
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)
    
    return config_module


def load_agent(account: str = None) -> Any:
    """
    Load account-specific agent configuration module.
    
    Args:
        account: Account identifier. If None, uses ACCOUNT_ENV environment variable.
    
    Returns:
        Loaded agent module with account-specific agent configuration
    
    Raises:
        ValueError: If account is invalid
        FileNotFoundError: If agent file doesn't exist for account
        
    Example:
        >>> agent_module = load_agent("usfs")
        >>> print(agent_module.root_agent.name)
        USFSRagAgent
    """
    if account is None:
        account = get_account_env()
    
    if account not in VALID_ACCOUNTS:
        raise ValueError(
            f"Invalid account: {account}. "
            f"Valid options are: {', '.join(VALID_ACCOUNTS)}"
        )
    
    agent_path = CONFIG_DIR / account / "agent.py"
    
    if not agent_path.exists():
        raise FileNotFoundError(
            f"Agent file not found: {agent_path}\n"
            f"Expected location: backend/config/{account}/agent.py"
        )
    
    # Load the module dynamically
    spec = importlib.util.spec_from_file_location(
        f"config.{account}.agent",
        agent_path
    )
    agent_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(agent_module)
    
    return agent_module


def get_account_info(account: str = None) -> dict:
    """
    Get information about an account configuration.
    
    Args:
        account: Account identifier. If None, uses ACCOUNT_ENV environment variable.
    
    Returns:
        Dictionary with account information
        
    Example:
        >>> info = get_account_info("usfs")
        >>> print(info["account_name"])
        usfs
        >>> print(info["project_id"])
        usfs-rag-agent
    """
    config = load_config(account)
    
    return {
        "account_name": config.ACCOUNT_NAME,
        "account_description": config.ACCOUNT_DESCRIPTION,
        "project_id": config.PROJECT_ID,
        "location": config.LOCATION,
        "organization_domain": getattr(config, "ORGANIZATION_DOMAIN", None),
        "default_corpus_name": getattr(config, "DEFAULT_CORPUS_NAME", None),
    }


def list_available_accounts() -> list:
    """
    List all available account configurations.
    
    Returns:
        List of available account identifiers
        
    Example:
        >>> accounts = list_available_accounts()
        >>> print(accounts)
        ['develom', 'usfs', 'tt']
    """
    return VALID_ACCOUNTS.copy()


def validate_account_config(account: str = None) -> tuple[bool, str]:
    """
    Validate that an account configuration is properly set up.
    
    Args:
        account: Account identifier. If None, uses ACCOUNT_ENV environment variable.
    
    Returns:
        Tuple of (is_valid, message)
        
    Example:
        >>> is_valid, message = validate_account_config("usfs")
        >>> if is_valid:
        ...     print("Configuration is valid")
        ... else:
        ...     print(f"Error: {message}")
    """
    if account is None:
        try:
            account = get_account_env()
        except ValueError as e:
            return False, str(e)
    
    if account not in VALID_ACCOUNTS:
        return False, f"Invalid account: {account}. Valid: {', '.join(VALID_ACCOUNTS)}"
    
    # Check if config.py exists
    config_path = CONFIG_DIR / account / "config.py"
    if not config_path.exists():
        return False, f"Missing config.py for account: {account}"
    
    # Check if agent.py exists
    agent_path = CONFIG_DIR / account / "agent.py"
    if not agent_path.exists():
        return False, f"Missing agent.py for account: {account}"
    
    # Check if __init__.py exists
    init_path = CONFIG_DIR / account / "__init__.py"
    if not init_path.exists():
        return False, f"Missing __init__.py for account: {account}"
    
    # Try loading config
    try:
        config = load_config(account)
    except Exception as e:
        return False, f"Error loading config: {str(e)}"
    
    # Validate required config attributes
    required_attrs = ["PROJECT_ID", "LOCATION", "ACCOUNT_NAME"]
    missing_attrs = [attr for attr in required_attrs if not hasattr(config, attr)]
    
    if missing_attrs:
        return False, f"Missing required config attributes: {', '.join(missing_attrs)}"
    
    # Try loading agent
    try:
        agent_module = load_agent(account)
    except Exception as e:
        return False, f"Error loading agent: {str(e)}"
    
    # Validate agent has root_agent
    if not hasattr(agent_module, "root_agent"):
        return False, "Agent module missing 'root_agent' attribute"
    
    return True, f"Account '{account}' configuration is valid"


# Convenience function for scripts
def print_current_config():
    """
    Print current account configuration details.
    Useful for debugging and verification.
    """
    try:
        account = get_account_env()
        info = get_account_info(account)
        
        print("=" * 60)
        print("Current Account Configuration")
        print("=" * 60)
        print(f"Account:        {info['account_name']}")
        print(f"Description:    {info['account_description']}")
        print(f"Project ID:     {info['project_id']}")
        print(f"Location:       {info['location']}")
        print(f"Domain:         {info['organization_domain']}")
        print(f"Default Corpus: {info['default_corpus_name']}")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # When run directly, print current configuration
    print_current_config()
