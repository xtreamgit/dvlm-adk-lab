#!/usr/bin/env python3
"""Fix all ? placeholders to %s for PostgreSQL."""

import os
import re
from pathlib import Path

def fix_file(filepath):
    """Fix SQL placeholders in a Python file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # Replace ? with %s in SQL contexts
    # Pattern 1: WHERE ... = ?
    content = re.sub(r'= \?', r'= %s', content)
    
    # Pattern 2: , ?
    content = re.sub(r', \?', r', %s', content)
    
    # Pattern 3: (?)
    content = re.sub(r'\(\?\)', r'(%s)', content)
    
    # Pattern 4: VALUES (?
    content = re.sub(r'VALUES \(\?', r'VALUES (%s', content)
    
    # Pattern 5: , ?)
    content = re.sub(r', \?\)', r', %s)', content)
    
    # Pattern 6: f"{key} = ?"
    content = re.sub(r'f"\{key\} = \?"', r'f"{key} = %s"', content)
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

# Find all Python files in src
src_dir = Path('backend/src')
fixed_count = 0

for py_file in src_dir.rglob('*.py'):
    if fix_file(py_file):
        print(f"Fixed: {py_file}")
        fixed_count += 1

print(f"\nTotal files fixed: {fixed_count}")
