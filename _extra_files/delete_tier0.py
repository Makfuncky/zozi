"""Delete Tier 0 safe-delete service files identified by migration_tracker."""
import sys
import shutil
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\scripts\system_trackers")
from migration_tracker import run_full_audit, BACKEND

def main():
    report = run_full_audit()
    sc = report.service_consolidation
    
    tier0_files = [f.file_a for f in sc.tier0_safe_deletes if f.action == "DELETE"]
    tier0_review = [f.file_a for f in sc.tier0_safe_deletes if f.action == "REVIEW"]
    
    print(f"\nTier 0 safe deletes (DELETE): {len(tier0_files)}")
    for f in tier0_files:
        print(f"  {f}")
    
    print(f"\nTier 0 REVIEW (have importers, do NOT delete): {len(tier0_review)}")
    for f in tier0_review:
        print(f"  {f}")
    
    if not tier0_files:
        print("\nNo files to delete.")
        return
    
    deleted = []
    for rel in tier0_files:
        target = BACKEND / rel
        if target.exists():
            target.unlink()
            deleted.append(rel)
            print(f"  Deleted: {rel}")
        else:
            print(f"  Missing: {rel}")
    
    print(f"\nDeleted {len(deleted)} files.")
    
    # Write a log
    log_path = BACKEND.parent / "_extra_files" / "deletion_log.txt"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n=== Deletion run {datetime.now(timezone.utc).isoformat()} ===\n")
        for rel in deleted:
            f.write(f"DELETED {rel}\n")
        for rel in tier0_review:
            f.write(f"REVIEW {rel}\n")
    print(f"Log written to {log_path}")

if __name__ == "__main__":
    main()
