"""Fix __table_args__ by removing inline schema dicts and adding them at end of tuple."""
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

    # Find all __tablename__ assignments and their __table_args__
    # Pattern: __tablename__ = "table_name" followed by __table_args__ = (...)
    # We need to fix each class

    # First, fix inline schema dicts in Index/UniqueConstraint calls
    # Remove {"schema": "X"} from inside Index(...) and UniqueConstraint(...)
    def remove_inline_schema(m):
        block = m.group(1)
        # Remove all {"schema": "X"} patterns from inside Index/UniqueConstraint
        block = re.sub(r',\s*\{\s*"schema"\s*:\s*"[^"]+"\s*\}', '', block)
        return '__table_args__ = (' + block + m.group(2)

    # Fix patterns like: Index("...", "field", {"schema": "X"})
    content = re.sub(
        r'(Index\("[^"]*",\s*[^)]*)\{\s*"schema"\s*:\s*"[^"]+"\s*\}',
        r'\1',
        content
    )
    content = re.sub(
        r'(UniqueConstraint\("[^"]*",\s*[^)]*)\{\s*"schema"\s*:\s*"[^"]+"\s*\}',
        r'\1',
        content
    )

    # Now add schema dict at end of __table_args__ tuples that don't have it
    # Pattern: __table_args__ = (...) where ) is not followed by another ) or ;
    def add_schema_at_end(m):
        block = m.group(1)
        # Check if schema dict already exists at the end
        if re.search(r'\{\s*"schema"\s*:\s*"[^"]+"\s*\}\s*$', block):
            return m.group(0)
        # Add schema dict at the end
        block = block.rstrip().rstrip(',')
        if not block.endswith('('):
            block += ','
        block += ' {"schema": "' + m.group(2) + '"}'
        return '__table_args__ = (' + block + ')'

    # Match __table_args__ = ( ... ) and extract schema from first Index/UniqueConstraint
    # Actually, we need to know the schema for each table. Let's use the mapping.
    
    # Better approach: for each __table_args__ = (...), check if it ends with a schema dict
    # If not, and we can determine the schema, add it.
    
    # Since we have the schema mapping, let's do a two-pass:
    # 1. Find all __tablename__ = "name" followed by __table_args__ = (...)
    # 2. For each, check if schema is missing, and add it
    
    lines = content.splitlines()
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Check if this is a __tablename__ line
        m = re.match(r'(\s*)__tablename__\s*=\s*"([^"]+)"', line)
        if m:
            indent = m.group(1)
            tablename = m.group(2)
            schema = SCHEMA_MAPPING.get(tablename)
            
            # Look ahead for __table_args__
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith('__table_args__'):
                new_lines.append(lines[j])
                j += 1
            
            if j < len(lines) and '=' in lines[j]:
                # Found __table_args__
                table_args_line = lines[j]
                new_lines.append(table_args_line)
                
                # Check if it's a single-line tuple
                if table_args_line.strip().endswith(')'):
                    # Single-line: __table_args__ = (...,)
                    if schema and schema != "public":
                        # Check if schema dict already present
                        if '"schema"' not in table_args_line:
                            # Add schema dict at end
                            table_args_line = table_args_line.rstrip().rstrip(',')
                            if not table_args_line.endswith('('):
                                table_args_line += ','
                            table_args_line += ' {"schema": "' + schema + '"},)'
                            new_lines[-1] = table_args_line
                    i = j + 1
                    continue
                else:
                    # Multi-line: collect until closing )
                    block_lines = [table_args_line]
                    depth = 1
                    j += 1
                    while j < len(lines) and depth > 0:
                        block_lines.append(lines[j])
                        depth += lines[j].count('(') - lines[j].count(')')
                        j += 1
                    
                    # Check if schema dict already present in block
                    block_text = '\n'.join(block_lines)
                    has_schema = '"schema"' in block_text.lower()
                    
                    if schema and schema != "public" and not has_schema:
                        # Add schema dict before closing )
                        # Find the last line with )
                        for k in range(len(block_lines) - 1, -1, -1):
                            if ')' in block_lines[k]:
                                # Add schema dict before )
                                block_lines[k] = block_lines[k].replace(')', ' {"schema": "' + schema + '"},)')
                                break
                    
                    new_lines.extend(block_lines)
                    i = j
                    continue
        
        new_lines.append(line)
        i += 1

    content = '\n'.join(new_lines)
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
    
    print(f"Fixed {len(modified)} files:")
    for name in sorted(modified):
        print(f"  {name}")


if __name__ == "__main__":
    main()
