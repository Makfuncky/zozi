"""Fix __table_args__ by adding schema dict at end of tuple."""
import re
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BACKEND_DIR / "models"
SCHEMA_MAPPING_PATH = BACKEND_DIR / "docs" / "schema_mapping.json"


def load_schema_mapping() -> dict[str, str]:
    import json
    with SCHEMA_MAPPING_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


SCHEMA_MAPPING = load_schema_mapping()


def fix_file(path: Path) -> bool:
    content = path.read_text(encoding="utf-8")
    original = content

    # Process each line to find __tablename__ and __table_args__
    lines = content.splitlines()
    new_lines = []
    i = 0
    modified = False
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Check if this is a __tablename__ line
        m = re.match(r'(\s*)__tablename__\s*=\s*"([^"]+)"', line)
        if m:
            indent = m.group(1)
            tablename = m.group(2)
            schema = SCHEMA_MAPPING.get(tablename)
            
            new_lines.append(line)
            i += 1
            
            # Skip blank lines
            while i < len(lines) and not lines[i].strip():
                new_lines.append(lines[i])
                i += 1
            
            # Check if next line is __table_args__
            if i < len(lines) and '__table_args__' in lines[i]:
                table_args_start = i
                table_args_lines = []
                
                # Collect all lines of __table_args__
                while i < len(lines):
                    table_args_lines.append(lines[i])
                    if lines[i].strip().endswith(')'):
                        break
                    i += 1
                
                # Check if schema is already present
                table_args_text = '\n'.join(table_args_lines)
                if schema and schema != "public" and '"schema"' not in table_args_text.lower():
                    # Add schema dict at the end
                    # Find the last line that ends with )
                    for j in range(len(table_args_lines) - 1, -1, -1):
                        if ')' in table_args_lines[j]:
                            # Insert schema dict before )
                            table_args_lines[j] = table_args_lines[j].replace(')', ' {"schema": "' + schema + '"},)')
                            modified = True
                            break
                
                new_lines.extend(table_args_lines)
                continue
        
        new_lines.append(line)
        i += 1

    content = '\n'.join(new_lines)
    if modified:
        path.write_text(content, encoding="utf-8")
        return True
    return False


def main():
    modified = []
    for py in sorted(MODELS_DIR.glob("*.py")):
        if py.name.startswith("_"):
            continue
        if fix_file(py):
            modified.append(py.name)
    
    print(f"Modified {len(modified)} files:")
    for name in sorted(modified):
        print(f"  {name}")


if __name__ == "__main__":
    main()
