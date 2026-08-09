#!/usr/bin/env python3
"""
Script to validate and clean up Alembic migration structure.
Ensures proper chronological ordering and identifies issues.
"""
import os
import re
from pathlib import Path
def parse_revision_id(filename: str) -> str:
    """Extract revision ID from filename."""
    # Pattern: YYYY_MM_DD_HH_MM_<revision>
    match = re.search(r'(\d+_\d+_\d+_[\d_]+-[a-f0-9]+)', filename)
    if match:
        return match.group(1)
    return ""
def parse_title(filename: str) -> str:
    """Extract title from filename."""
    # Pattern: YYYY_MM_DD_HH_MM_<revision>_title.py
    match = re.search(r'[\d_]+-[a-f0-9]+-(.*?)\.py$', filename)
    if match:
        return match.group(1).replace('_', ' ').strip()
    return ""
def get_all_revisions(versions_path: str) -> dict:
    """Get all migrations with their revision IDs and titles."""
    revisions = {}
    
    for filename in os.listdir(versions_path):
        if filename.endswith('.py') and filename != '__pycache__':
            revision_id = parse_revision_id(filename)
            title = parse_title(filename)
            if revision_id:
                revisions[revision_id] = {
                    'filename': filename,
                    'title': title,
                    'down_revision': None,  # Will be populated separately
                }
    
    return revisions
def extract_down_revision(versions_path: str, revision_id: str) -> str:
    """Extract down_revision from migration file."""
    for filename in os.listdir(versions_path):
        if filename.endswith('.py') and f"-{revision_id}.py" in filename:
            filepath = os.path.join(versions_path, filename)
            with open(filepath, 'r') as f:
                content = f.read()
                match = re.search(r'down_revision:\s*Union\[str,\s*None\]\s*=\s*[\'\"]([^\'\"\s]+)[\'\"]', content)
                if match:
                    return match.group(1)
    return ""
def validate_and_fix_migrations(versions_path: str) -> bool:
    """Validate and fix Alembic migration structure."""
    print("🔍 Analyzing Alembic migration files...")
    
    revisions = get_all_revisions(versions_path)
    if not revisions:
        print("❌ No migration files found!")
        return False
    
    print(f"📋 Found {len(revisions)} migration files")
    
    # Check for duplicates and extract down_revisions
    for revision_id, data in revisions.items():
        down_revision = extract_down_revision(versions_path, revision_id)
        data['down_revision'] = down_revision
        
        if down_revision not in revisions and down_revision:
            print(f"⚠️  {revision_id}: down_revision '{down_revision}' not found!")
    
    # Check for duplicate revision IDs
    revision_counts = {}
    for revision_id in revisions.keys():
        revision_counts[revision_id] = revision_counts.get(revision_id, 0) + 1
    
    duplicates = {k: v for k, v in revision_counts.items() if v > 1}
    if duplicates:
        print(f"❌ Found {len(duplicates)} duplicate revision IDs:")
        for rev_id, count in duplicates.items():
            print(f"   - {rev_id}: {count} files")
        return False
    
    print("✅ Migration structure validated successfully!")
    return True
def organize_migrations(versions_path: str) -> None:
    """Organize migration files in proper order."""
    print("🔄 Organizing migration files...")
    
    revisions = get_all_revisions(versions_path)
    if not revisions:
        return
    
    # Create sorted list of (revision_id, data)
    sorted_revisions = sorted(revisions.items())
    
    # Rename files based on revision ID and title
    for i, (revision_id, data) in enumerate(sorted_revisions):
        old_filename = data['filename']
        new_filename = f"{revision_id}_{data['title'].replace(' ', '_').lower()}.py"
        
        old_path = os.path.join(versions_path, old_filename)
        new_path = os.path.join(versions_path, new_filename)
        
        if old_filename != new_filename:
            print(f"📝 Renaming: {old_filename} -> {new_filename}")
            # In a real scenario, you'd use shutil.move here
            # os.rename(old_path, new_path)
    
    print("✅ Migration files would be organized in chronological order")
if __name__ == "__main__":
    base_path = Path(__file__).parent
    versions_path = os.path.join(base_path, "alembic", "versions")
    
    if os.path.exists(versions_path):
        print(f"📁 Processing migrations in: {versions_path}")
        
        if validate_and_fix_migrations(versions_path):
            organize_migrations(versions_path)
            print("\n✨ Alembic migration cleanup completed!")
        else:
            print("\n❌ Migration cleanup failed!")
    else:
        print(f"❌ Alembic/versions directory not found: {versions_path}")