#!/usr/bin/env python3
"""DOM7 Migration: country/ -> geography/ across controllers, models, services, providers."""
import os
import shutil

BACKEND = "D:/Projects/10- E-COMMERCE WEBSITE/zozi/backend"
os.chdir(BACKEND)

DIRS = [
    ("controllers/country", "controllers/geography"),
    ("models/country", "models/geography"),
    ("services/country", "services/geography"),
    ("providers/country", "providers/geography"),
]

moved_files = []
print("=" * 60)
print("DOM7 MIGRATION: country/ -> geography/")
print("=" * 60)

# Step 1: Create geography/ directories and copy files
for src_dir, dst_dir in DIRS:
    print("\n--- %s -> %s ---" % (src_dir, dst_dir))
    os.makedirs(dst_dir, exist_ok=True)
    init_path = os.path.join(dst_dir, "__init__.py")
    if not os.path.exists(init_path):
        with open(init_path, "w", encoding="utf-8") as f:
            f.write('"""Geography domain package."""\n')
        print("  Created %s/__init__.py" % dst_dir)

    if os.path.exists(src_dir):
        for fname in os.listdir(src_dir):
            if fname.endswith(".py") and fname != "__init__.py":
                src_file = os.path.join(src_dir, fname)
                dst_file = os.path.join(dst_dir, fname)
                with open(src_file, "r", encoding="utf-8") as f:
                    content = f.read()
                with open(dst_file, "w", encoding="utf-8") as f:
                    f.write(content)
                moved_files.append((src_dir, dst_dir, fname))
                print("  Moved %s" % fname)

print("\nTotal files moved: %d" % len(moved_files))

# Step 2: Update all imports
print("\n" + "=" * 60)
print("UPDATING IMPORTS")
print("=" * 60)

import_patterns = [
    ("from controllers.country.", "from controllers.geography."),
    ("import controllers.country", "import controllers.geography"),
    ("from models.country.", "from models.geography."),
    ("from models.country ", "from models.geography "),
    ("import models.country", "import models.geography"),
    ("from services.country.", "from services.geography."),
    ("from services.country ", "from services.geography "),
    ("import services.country", "import services.geography"),
    ("from providers.country.", "from providers.geography."),
    ("from providers.country ", "from providers.geography "),
    ("import providers.country", "import providers.geography"),
]

updated_files = []
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in ("venv", "__pycache__", ".git", "node_modules", "_extra_files")]
    for fname in files:
        if not fname.endswith(".py"):
            continue
        fpath = os.path.join(root, fname)
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            original = content
            for old, new in import_patterns:
                content = content.replace(old, new)
            if content != original:
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(content)
                updated_files.append(fpath)
        except Exception as e:
            print("  ERROR processing %s: %s" % (fpath, e))

print("Files with updated imports: %d" % len(updated_files))
for f in updated_files:
    print("  Updated: %s" % f)

# Step 3: Create backward-compat shims
print("\n" + "=" * 60)
print("CREATING BACKWARD-COMPAT SHIMS")
print("=" * 60)

shim_count = 0
for src_dir, dst_dir in DIRS:
    os.makedirs(src_dir, exist_ok=True)
    shim_init = os.path.join(src_dir, "__init__.py")
    dst_module = dst_dir.replace(os.sep, ".")
    shim_content = '"""Backward-compat shim: re-export from %s"""\n' % dst_module
    shim_content += "from %s import *  # noqa: F401,F403\n" % dst_module
    with open(shim_init, "w", encoding="utf-8") as f:
        f.write(shim_content)
    shim_count += 1
    print("  Created shim: %s" % shim_init)

    for src, dst, fname in moved_files:
        if src == src_dir:
            shim_path = os.path.join(src_dir, fname)
            new_module = dst.replace(os.sep, ".")
            base = fname[:-3]
            shim_content2 = '"""Backward-compat shim: re-export from %s.%s"""\n' % (new_module, base)
            shim_content2 += "from %s.%s import *  # noqa: F401,F403\n" % (new_module, base)
            with open(shim_path, "w", encoding="utf-8") as f:
                f.write(shim_content2)
            shim_count += 1
            print("  Created shim: %s" % shim_path)

# Step 4: Verify
print("\n" + "=" * 60)
print("VERIFICATION")
print("=" * 60)
for src_dir, dst_dir in DIRS:
    if os.path.exists(dst_dir):
        py_files = [f for f in os.listdir(dst_dir) if f.endswith(".py")]
        print("  %s: %d .py files" % (dst_dir, len(py_files)))
    else:
        print("  %s: MISSING!" % dst_dir)

print("\nMigration complete!")
print("Files moved: %d" % len(moved_files))
print("Files with updated imports: %d" % len(updated_files))
print("Shims created: %d" % shim_count)
