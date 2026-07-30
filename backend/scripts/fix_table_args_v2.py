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

    # Find all __table_args__ = (...) patterns and add schema if missing
    # Pattern 1: Single-line: __table_args__ = (Index(...),)
    # Pattern 2: Multi-line: __table_args__ = (\n  Index(...),\n  Index(...),\n)
    
    def fix_single_line(m):
        block = m.group(1)
        schema = m.group(2)
        # Check if schema is already present
        if '"schema"' in block.lower():
            return m.group(0)
        # Add schema dict at end
        block = block.rstrip().rstrip(',')
        if not block.endswith('('):
            block += ','
        block += ' {"schema": "' + schema + '"},)'
        return '__table_args__ = (' + block
    
    def fix_multi_line(m):
        block = m.group(1)
        schema = m.group(2)
        # Check if schema is already present
        if '"schema"' in block.lower():
            return m.group(0)
        # Add schema dict at end, before closing )
        # The block ends with ) on its own line or at end of last element
        # Find the last ) in the block
        last_paren = block.rfind(')')
        if last_paren == -1:
            return m.group(0)
        # Insert schema dict before )
        before = block[:last_paren].rstrip().rstrip(',')
        after = block[last_paren:]
        if not before.endswith('('):
            before += ','
        before += ' {"schema": "' + schema + '"}'
        return '__table_args__ = (' + before + after
    
    # First, fix single-line patterns
    # Match: __table_args__ = ( ... ) where ... doesn't contain schema
    # We need to match __tablename__ = "X" followed by __table_args__ = (...)
    
    # Use a simpler approach: find __table_args__ = (...) and add schema
    # Pattern: __table_args__ = (content) where content doesn't have schema
    
    # Single-line pattern
    content = re.sub(
        r'__table_args__\s*=\s*\(\s*([^)]*)\s*\)(?!\s*\{)',
        lambda m: fix_single_line(m) if '"schema"' not in m.group(1).lower() else m.group(0),
        content
    )
    
    # Multi-line pattern
    content = re.sub(
        r'__table_args__\s*=\s*\(\s*\n(.*?)\n\s*\)(?!\s*\{)',
        lambda m: fix_multi_line(m) if '"schema"' not in m.group(1).lower() else m.group(0),
        content,
        flags=re.DOTALL
    )

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
