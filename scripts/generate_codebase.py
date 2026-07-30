#!/usr/bin/env python3
"""
generate_codebase.py
Scans the project directory and generates a single markdown file containing
the directory tree and all relevant source/config files for AI context injection.
"""
import os
import fnmatch
from pathlib import Path

import mcp

PROJECT_ROOT = Path(__file__).parent.resolve()
OUTPUT_FILE = PROJECT_ROOT / "codebase.md"

# ✅ Only include these file types
# ALLOWED_EXTENSIONS = {'.py', '.yaml', '.yml', '.md', '.txt', '.json', '.cfg', '.ini', '.toml', '.ts', '.tsx', '.js'}
ALLOWED_EXTENSIONS = {'.py', '.yaml', '.yml', '.json', '.txt','.cfg', '.ini', '.toml', '.ts', '.tsx', '.js', '.log', '.md', '.bat', '.ps1', '.sh'}

# ❌ Skip these directories entirely (UNLESS overridden by ALLOWED_FORCED_ADDED)
# Note: 'tests' and 'scripts' are excluded to keep the generated snapshot lean for AI context;
# their exclusion reduces token count. Add specific test/script files to ALLOWED_FORCED_ADDED if needed.
EXCLUDE_DIRS = {
    '.git', '__pycache__', '.venv', 'venv', 'node_modules', 'data', 'logs', '.idea',
    '.vscode', 'dist', 'build', '.pytest_cache', 'tests', 'scripts', 'documents', 
    'document', 'docs', '__tests__', 'test_outputs',
    '.kilo', '.playwright-mcp', '.vscode', 'browser-tests', 

    '_trash', '.freebuff', '.git', '.github', '.hypothesis', '.kilo', '.kilocode', '.next', 
    '.playwright-mcp', '.pytest_cache', '.ruff_cache', '__pycache__', 'browser-tests',
    '.github', '.maestro', 'artifacts', 'recovery_file', '.next',
    'node_modules', 'nginx',
    'scripts', 'uploads',
    # Android / React Native build artifacts
    '.cxx', '.gradle', 'CMakeFiles', 'RelWithDebInfo', 'Debug', 'Release',
    'x86', 'x86_64', 'arm64-v8a', 'armeabi-v7a',
    'Working_API'
}

# ❌ Skip these file patterns (including the binary .txt files you encountered)
EXCLUDE_PATTERNS = [
    '*.log', '*.csv', '*.db', '*.pyc', '*.tmp', '*.exe', '*.dll', '*.lock',
    'run_zozi.bat', 'start_zozi.bat', 'start_zozi.ps1', 'test_zozi.bat', 'troubleshoot_zozi.bat',
    '*.egg-info', 'codebase.md', 'generate_codebase.py', 'zozi.db',
    # Binary or encoding-problematic .txt files
    'SECURITY.md','AGENTS.md', 'AUDIT_REPORT.md', 'codebase.md', 'COUNTRY_DETAILS.md', 
    'Employee_Chat_Video_Email_System.md', 'FEATURE_MATRIX.md', 'Features_List.md', 
    'Multi_Country_System.md', 'Payment_Gateway_System.md', 'README.md', 'AUDIT_REPORT_2026-07-28.md',
    'token.txt', 'Background_remove_AI_of photo.txt', 'Banner_Promotion_Discount..txt', 
    'Database_Management_System.txt', 'Error_Handling_System.txt', 'Finance_Treasury_System.txt', 
    'Fraud_Detection_System.txt', 'Mobile_App_Features_List.txt', 'problems.txt', 'Search_Filter_Supplier_Video_scrolling.txt', 
    'Security_System.txt', 'Single_Window_Dashboard_System.txt'
    'mobile_app.html'   
]

# ✅ EXCEPTIONS: Force-include specific files even if their parent is in EXCLUDE_DIRS
# 🔹 USE FORWARD SLASHES and paths relative to the project root.
ALLOWED_FORCED_ADDED = {
    # Example: 'data/some_config.json',
}


def is_forced_allowed(rel_path: Path) -> bool:
    """Check if a relative path is explicitly allowed to bypass directory exclusions."""
    return rel_path.as_posix() in ALLOWED_FORCED_ADDED


def is_path_in_excluded_dir(rel_path: Path) -> bool:
    """Check if ANY parent directory of the file is in EXCLUDE_DIRS."""
    return any(part in EXCLUDE_DIRS for part in rel_path.parts[:-1])


def is_included(file_path: Path, rel_path: Path) -> bool:
    # 1. Force-allow check (bypasses ALL other filters)
    if is_forced_allowed(rel_path):
        return True
    # 2. STRICT PARENT FILTER: If inside an excluded dir, reject immediately
    if is_path_in_excluded_dir(rel_path):
        return False
    # 3. Extension check
    if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        return False
    # 4. Pattern exclusion
    for pattern in EXCLUDE_PATTERNS:
        if fnmatch.fnmatch(file_path.name, pattern):
            return False
    return True


def should_prune_dir(dir_path: Path) -> bool:
    """
    Determines if a directory should be pruned from traversal.

    Logic:
    1. If the directory is NOT in an excluded context (itself or parent in EXCLUDE_DIRS), keep it.
    2. If the directory IS in an excluded context, ONLY keep it if it contains a forced file.
    """
    try:
        rel_path = dir_path.relative_to(PROJECT_ROOT)
    except ValueError:
        return False

    parts = rel_path.parts
    in_excluded_context = any(part in EXCLUDE_DIRS for part in parts)

    if not in_excluded_context:
        return False

    rel_dir_str = rel_path.as_posix()
    if not rel_dir_str.endswith('/'):
        rel_dir_str += '/'

    has_forced_descendant = any(fp.startswith(rel_dir_str) for fp in ALLOWED_FORCED_ADDED)
    return not has_forced_descendant


def get_language_tag(file_path: Path) -> str:
    ext = file_path.suffix.lower()
    mapping = {
        '.py': 'python', '.yaml': 'yaml', '.yml': 'yaml',
        '.md': 'markdown', '.json': 'json', '.txt': 'text',
        '.cfg': 'ini', '.ini': 'ini', '.toml': 'toml',
    }
    return mapping.get(ext, 'text')


def get_project_tree(root: Path) -> str:
    """Generates a clean ASCII tree of included files/folders."""
    tree_lines = ["zozi/"]

    def _walk(current_path: Path, prefix: str):
        try:
            try:
                items = sorted(current_path.iterdir(), key=lambda p: p.name)
            except (FileNotFoundError, PermissionError, OSError) as e:
                print(f"⚠️  Skipping inaccessible directory: {current_path} ({e})")
                return

            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                connector = "└── " if is_last else "├── "

                if item.is_symlink():
                    continue

                if item.is_dir():
                    if not should_prune_dir(item):
                        tree_lines.append(f"{prefix}{connector}{item.name}/")
                        extension = "    " if is_last else "│   "
                        _walk(item, prefix + extension)
                else:
                    rel_path = item.relative_to(PROJECT_ROOT)
                    if is_included(item, rel_path):
                        tree_lines.append(f"{prefix}{connector}{item.name}")
        except RecursionError:
            print(f"⚠️  Recursion limit exceeded while walking {current_path} – skipping")
            return

    _walk(root, "")
    return "\n".join(tree_lines)


def main():
    print(f"🔍 Scanning project at: {PROJECT_ROOT}")
    print(f"📝 Generating codebase.md...")
    if ALLOWED_FORCED_ADDED:
        print(f"⚡ Forced inclusions active: {ALLOWED_FORCED_ADDED}")

    md_content = "# Knowledge Base\n\n## Project Structure\n\n```text\n"
    md_content += get_project_tree(PROJECT_ROOT)
    md_content += "\n```\n\n## File Contents\n\n"

    files_found = 0
    for root_dir, dirs, files in os.walk(PROJECT_ROOT):
        # Prune excluded directories intelligently
        dirs[:] = sorted([d for d in dirs if not should_prune_dir(Path(root_dir) / d)])

        for file_name in sorted(files):
            file_path = Path(root_dir) / file_name
            rel_path = file_path.relative_to(PROJECT_ROOT)

            if not is_included(file_path, rel_path):
                continue

            try:
                content = file_path.read_text(encoding='utf-8')
                lang = get_language_tag(file_path)
                md_content += f"### `{rel_path}`\n\n```{lang}\n{content}\n```\n\n"
                files_found += 1

                if is_forced_allowed(rel_path):
                    print(f"  ✅ Forced-included: {rel_path}")

            except UnicodeDecodeError:
                # Silently skip binary files – you can uncomment the next line if you want warnings
                # print(f"⚠️  Skipped binary file: {rel_path}")
                pass
            except Exception as e:
                print(f"⚠️  Could not read {rel_path}: {e}")

    OUTPUT_FILE.write_text(md_content, encoding='utf-8')
    print(f"\n✅ Successfully wrote {files_found} files to {OUTPUT_FILE.name}")
    print(f"📦 Output size: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")
    print(f"💡 Paste the contents of {OUTPUT_FILE.name} into your AI prompt or upload it as a file.")


if __name__ == "__main__":
    main()