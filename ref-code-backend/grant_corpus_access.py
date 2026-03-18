#!/usr/bin/env python3
"""
Grant admin-users group access to all active corpora.
"""

import os
import sys

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.repositories.corpus_repository import CorpusRepository
from database.repositories.group_repository import GroupRepository

def grant_admin_access():
    """Grant admin-users group access to all active corpora."""
    print("🔐 Granting admin-users group access to all corpora...")
    
    # Get admin-users group
    admin_group = GroupRepository.get_group_by_name('admin-users')
    if not admin_group:
        print("❌ admin-users group not found!")
        return False
    
    admin_group_id = admin_group['id']
    print(f"✅ Found admin-users group (ID: {admin_group_id})")
    
    # Get all active corpora
    all_corpora = CorpusRepository.get_all(active_only=True)
    print(f"\n📚 Found {len(all_corpora)} active corpora")
    
    # Grant access to each corpus
    granted_count = 0
    skipped_count = 0
    for corpus in all_corpora:
        try:
            # Check if group already has access
            existing_groups = CorpusRepository.get_groups_for_corpus(corpus['id'])
            existing_group_ids = [g.get('id') or g.get('group_id') for g in existing_groups]
            
            if admin_group_id in existing_group_ids:
                print(f"   ⏭️  Already has access: {corpus['name']}")
                skipped_count += 1
                continue
            
            # Grant access (note: parameters are group_id, corpus_id)
            success = CorpusRepository.grant_group_access(admin_group_id, corpus['id'])
            if success:
                print(f"   ✅ Granted access: {corpus['name']}")
                granted_count += 1
            else:
                print(f"   ⚠️  Failed to grant access: {corpus['name']}")
        except Exception as e:
            print(f"   ❌ Error granting access to {corpus['name']}: {e}")
    
    print(f"\n✅ Granted access to {granted_count} corpora")
    print(f"✅ admin-users group now has access to all {len(all_corpora)} active corpora")
    return True

if __name__ == "__main__":
    grant_admin_access()
