import os
from pathlib import Path

def combine_files_to_markdown():
    # ==========================================
    # CONFIGURATION: Write your file names here
    # ==========================================
    
    # Option 1: List specific files you want to combine
    # Leave this empty [] if you want to use Option 2
    specific_files = [
        "br_05.py",
        "br_06.py",
        "br_08.py",
        "br_11.py",
        "br_12.py",
        "br_13.py",
    ]

    # Option 2: Automatically grab ALL .py files from a specific folder
    # Set this to True if you want to scan a folder instead of listing files
    scan_folder = False 
    folder_to_scan = "./"  # The folder to scan (e.g., "./", "./src/", etc.)

    # Output file name
    output_md_file = "combined_code.md"

    # ==========================================
    # LOGIC
    # ==========================================
    
    files_to_process = []

    if specific_files:
        # Use the manually listed files
        files_to_process = specific_files
    elif scan_folder:
        # Scan the folder for all .py files
        folder_path = Path(folder_to_scan)
        files_to_process = sorted([str(f) for f in folder_path.glob("*.py")])
        if not files_to_process:
            print(f"❌ No .py files found in {folder_to_scan}")
            return
    else:
        print("❌ Please provide specific files or enable scan_folder.")
        return

    print(f"📄 Found {len(files_to_process)} Python file(s) to process...")

    # Write to Markdown file
    with open(output_md_file, "w", encoding="utf-8") as md_file:
        md_file.write("# Combined Python Code\n\n")
        md_file.write("This file contains the combined source code from the project.\n\n")
        md_file.write("---\n\n")

        for file_name in files_to_process:
            file_path = Path(file_name)
            
            if not file_path.exists():
                print(f"⚠️  Warning: File '{file_name}' not found. Skipping.")
                continue

            print(f"  ✅ Reading: {file_name}")
            
            # Read the Python file content
            with open(file_path, "r", encoding="utf-8") as py_file:
                content = py_file.read()

            # Write to Markdown with syntax highlighting
            md_file.write(f"## 📄 {file_name}\n\n")
            md_file.write("```python\n")
            md_file.write(content)
            md_file.write("\n```\n\n")
            md_file.write("---\n\n")

    print(f"\n Success! All files combined into '{output_md_file}'")

if __name__ == "__main__":
    combine_files_to_markdown()