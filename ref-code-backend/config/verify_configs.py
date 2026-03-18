#!/usr/bin/env python3
"""
Configuration Verification Script

This script verifies that all account configurations are properly set up.
Run this after creating or modifying account configurations.

Usage:
    python backend/config/verify_configs.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config_loader import (
    list_available_accounts,
    validate_account_config,
    get_account_info,
    load_config,
    load_agent,
)


def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_section(text):
    """Print formatted section."""
    print(f"\n{text}")
    print("-" * 70)


def verify_all_configs():
    """Verify all account configurations."""
    print_header("Account Configuration Verification")
    
    accounts = list_available_accounts()
    print(f"\nAvailable accounts: {', '.join(accounts)}")
    
    all_valid = True
    results = {}
    
    # Validate each account
    print_section("Validating Account Configurations")
    
    for account in accounts:
        print(f"\n🔍 Validating account: {account}")
        
        is_valid, message = validate_account_config(account)
        results[account] = (is_valid, message)
        
        if is_valid:
            print(f"   ✅ {message}")
        else:
            print(f"   ❌ {message}")
            all_valid = False
    
    # Display detailed information for valid accounts
    print_section("Account Details")
    
    for account in accounts:
        if results[account][0]:  # If valid
            try:
                print(f"\n📋 Account: {account.upper()}")
                info = get_account_info(account)
                
                for key, value in info.items():
                    print(f"   {key.replace('_', ' ').title():20}: {value}")
                
                # Load and check config
                config = load_config(account)
                print(f"   {'Corpus Mappings':20}: {len(config.CORPUS_TO_BUCKET_MAPPING)} configured")
                
                # Load and check agent
                agent_module = load_agent(account)
                print(f"   {'Agent Name':20}: {agent_module.root_agent.name}")
                print(f"   {'Agent Tools':20}: {len(agent_module.root_agent.tools)} tools")
                
            except Exception as e:
                print(f"   ⚠️  Error loading details: {e}")
    
    # Display corpus mappings
    print_section("Corpus to Bucket Mappings")
    
    for account in accounts:
        if results[account][0]:  # If valid
            try:
                config = load_config(account)
                print(f"\n📦 {account.upper()} Corpus Mappings:")
                
                if config.CORPUS_TO_BUCKET_MAPPING:
                    for corpus, bucket in config.CORPUS_TO_BUCKET_MAPPING.items():
                        print(f"   {corpus:30} → {bucket}")
                else:
                    print("   No corpus mappings configured")
                    
            except Exception as e:
                print(f"   ⚠️  Error: {e}")
    
    # Summary
    print_section("Summary")
    
    valid_count = sum(1 for v in results.values() if v[0])
    total_count = len(results)
    
    print(f"\n✅ Valid configurations: {valid_count}/{total_count}")
    
    if all_valid:
        print("\n🎉 All account configurations are valid!")
        print("\nNext steps:")
        print("  1. Update USFS and TechTrend with actual project IDs/regions")
        print("  2. Integrate config loader with existing application code")
        print("  3. Update deployment scripts to set ACCOUNT_ENV")
        print("  4. Test deployment for each account")
        return 0
    else:
        print("\n⚠️  Some configurations have errors. Please fix them before proceeding.")
        return 1


def test_config_loading():
    """Test configuration loading functionality."""
    print_section("Testing Configuration Loading")
    
    accounts = list_available_accounts()
    
    for account in accounts:
        print(f"\n🧪 Testing {account}...")
        
        try:
            # Test config loading
            config = load_config(account)
            print(f"   ✅ Config loaded: PROJECT_ID={config.PROJECT_ID}")
            
            # Test agent loading
            agent_module = load_agent(account)
            print(f"   ✅ Agent loaded: {agent_module.root_agent.name}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return 1
    
    print("\n✅ All loading tests passed!")
    return 0


def main():
    """Main verification function."""
    try:
        # Run verification
        result = verify_all_configs()
        
        # Run loading tests
        test_result = test_config_loading()
        
        # Exit with appropriate code
        sys.exit(max(result, test_result))
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
