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

    # Find all __tablename__ = "X" followed by __table_args__ = (...)
    # For each, add schema dict at end of tuple if missing
    
    def add_schema_to_tuple(m):
        tablename = m.group(1)
        block = m.group(2)
        schema = SCHEMA_MAPPING.get(tablename)
        
        if not schema or schema == "public":
            return m.group(0)
        
        # Check if schema is already present
        if '"schema"' in block.lower():
            return m.group(0)
        
        # Add schema dict at end
        # The block is the content inside the parentheses
        block = block.rstrip().rstrip(',')
        if not block.endswith('('):
            block += ','
        block += ' {"schema": "' + schema + '"}'
        return '__table_args__ = (' + block + ')'
    
    # Match __tablename__ = "X" followed by __table_args__ = (...)
    # This handles both single-line and multi-line cases
    pattern = re.compile(
        r'(__tablename__\s*=\s*"([^"]+)"\s*\n\s*__table_args__\s*=\s*\()(.*?)(\s*)\)(?!\s*\{)',
        re.DOTALL
    )
    
    def replacer(m):
        tablename = m.group(2)
        block = m.group(3)
        schema = SCHEMA_MAPPING.get(tablename)
        
        if not schema or schema == "public":
            return m.group(0)
        
        # Check if schema is already present
        if '"schema"' in block.lower():
            return m.group(0)
        
        # Add schema dict at end
        block = block.rstrip().rstrip(',')
        if not block.endswith('('):
            block += ','
        block += ' {"schema": "' + schema + '"}'
        return m.group(1) + block + m.group(4) + ')'
    
    content = pattern.sub(replacer, content)

    if content != original:
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
