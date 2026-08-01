import os
from pathlib import Path

def generate_project_scaffolding(root_dir=".", output_file="./PROJECT_SCAFFOLDING.md"):
    """
    Generates a Markdown file containing the tree structure of the project.
    """
    
    # Directories to ignore (Crucial for ZOZI to avoid massive node_modules/android/ios folders)
    IGNORE_DIRS = {
        'node_modules', '.git', '__pycache__', '.venv', 'venv', '.next', 
        '.expo', 'dist', 'build', '.playwright-artifacts-0', 'web-dist',
        'android', 'ios', '.kotlin', 'gradle', 'test-results', '.idea', 
        '.vscode', 'static-tmp', '.web-build-test', 'playwright-out',
        'artifacts', 'uploads' # Optional: ignore large upload folders
    }
    
    # Files to ignore (Lock files, OS files, etc.)
    IGNORE_FILES = {
        '.DS_Store', 'Thumbs.db', 'pnpm-lock.yaml', 'package-lock.json', 
        'yarn.lock', 'zozi.db' # Ignore dev SQLite DB
    }

    root_path = Path(root_dir).resolve()
    
    print(f"🔍 Scanning project structure at: {root_path}")
    print("⏳ This may take a few seconds...")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# 📂 ZOZI Project Scaffolding Structure\n\n")
        f.write(f"**Root Directory:** `{root_path}`\n\n")
        f.write("```text\n")
        
        # Write root folder name
        f.write(f"{root_path.name}/\n")
        
        # Recursive function to build the tree
        def build_tree(dir_path, prefix=""):
            try:
                # Get all entries, sort them (folders first, then files, alphabetically)
                entries = sorted(os.listdir(dir_path))
                
                dirs = []
                files = []
                
                for entry in entries:
                    if entry in IGNORE_DIRS or entry in IGNORE_FILES:
                        continue
                    if entry.startswith('.'): # Ignore hidden files/folders except specific ones if needed
                        continue
                        
                    full_path = os.path.join(dir_path, entry)
                    if os.path.isdir(full_path):
                        dirs.append(entry)
                    else:
                        files.append(entry)
                        
                # Combine dirs and files for iteration, but keep them grouped
                all_items = dirs + files
                is_dir_map = [True] * len(dirs) + [False] * len(files)
                
                for i, (item, is_dir) in enumerate(zip(all_items, is_dir_map)):
                    is_last = (i == len(all_items) - 1)
                    connector = "└── " if is_last else "├── "
                    extension = "    " if is_last else "│   "
                    
                    full_item_path = os.path.join(dir_path, item)
                    
                    # Handle symlinks to prevent infinite loops
                    if os.path.islink(full_item_path):
                        continue
                        
                    if is_dir:
                        f.write(f"{prefix}{connector}{item}/\n")
                        # Recurse into directory
                        build_tree(full_item_path, prefix + extension)
                    else:
                        f.write(f"{prefix}{connector}{item}\n")
                        
            except PermissionError:
                f.write(f"{prefix}└── [Permission Denied]\n")
            except Exception as e:
                f.write(f"{prefix}└── [Error: {e}]\n")

        # Start building from the root directory
        build_tree(root_path)
        
        f.write("```\n")
        
    print(f"✅ Success! Scaffolding saved to: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    # Run the script
    generate_project_scaffolding()