"""Find down_revision references to corrupted migration revision IDs."""
import pathlib, re

versions = pathlib.Path("alembic/versions")
corrupt_revs = {
    "18afc076b757", "2f07459e835f", "48c2a8404b0e",
    "97126a91bc8e", "c2d3e4f5a6b7", "d5477adebb01", "e3f4a5b6c7d8"
}

# Extract all revision info from good files
for f in sorted(versions.glob("*.py")):
    data = f.read_bytes()
    if b"\x00" in data:
        continue
    text = data.decode("utf-8", errors="replace")
    
    # Find references to corrupt revisions
    for crev in corrupt_revs:
        if crev in text:
            rev_match = re.search(r'revision\s*=\s*["\']([^"\']+)', text)
            down_match = re.search(r'down_revision\s*=\s*["\']([^"\']+)', text)
            down_tuple = re.search(r'down_revision\s*=\s*\(([^)]+)\)', text)
            rev = rev_match.group(1) if rev_match else "?"
            if down_match:
                down = down_match.group(1)
            elif down_tuple:
                down = down_tuple.group(1)
            else:
                down = "None"
            print(f"File {f.name} (rev={rev}, down={down}) references corrupt rev {crev}")

