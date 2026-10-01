import re
from pathlib import Path

# Skip these directories
SKIP = {".venv", "__pycache__", "node_modules", ".git"}

count = 0
for py in Path(".").rglob("*.py"):
    if any(s in str(py) for s in SKIP):
        continue
    text = py.read_text(encoding="utf-8", errors="ignore")
    original = text

    # Rename variable names: redis (as a local variable) -> valkey
    # But be careful: don't rename in string literals, comments, or identifiers that aren't standalone
    # Pattern: word boundary "redis" that's not part of "valkey_hit_ratio" or "valkey_url" (we'll handle those separately)
    # First, handle compound names
    text = re.sub(r"\bredis_url\b", "valkey_url", text)
    text = re.sub(r"\bredis_hit_ratio\b", "valkey_hit_ratio", text)
    text = re.sub(r"\bredis_client\b", "valkey_client", text)
    text = re.sub(r"\bget_redis\b", "get_valkey", text)
    text = re.sub(r"\bget_redis_client\b", "get_valkey_client", text)
    text = re.sub(r"\bget_redis_health_status\b", "get_valkey_health_status", text)
    text = re.sub(r"\bNoOpRedis\b", "NoOpValkey", text)
    text = re.sub(r"\bNoOpPipeline\b", "NoOpValkeyPipeline", text)
    text = re.sub(r"\b_redis_client\b", "_valkey_client", text)
    text = re.sub(r"\b_redis_service\b", "_valkey_service", text)
    text = re.sub(r"\b_redis_snapshot\b", "_valkey_snapshot", text)
    text = re.sub(r"\bredis_replay\b", "valkey_replay", text)

    # Rename "Redis" in comments/docstrings (case-insensitive)
    text = re.sub(r"Valkey cache", "Valkey cache", text)
    text = re.sub(r"Valkey client", "Valkey client", text)
    text = re.sub(r"Valkey session", "Valkey session", text)
    text = re.sub(r"Valkey-backed", "Valkey-backed", text)
    text = re.sub(r"Valkey key", "Valkey key", text)
    text = re.sub(r"Valkey lookup", "Valkey lookup", text)
    text = re.sub(r"Valkey response cache", "Valkey response cache", text)
    text = re.sub(r"Valkey polling", "Valkey polling", text)
    text = re.sub(r"Valkey polling", "Valkey polling", text)
    text = re.sub(r"in Valkey", "in Valkey", text)
    text = re.sub(r"from Valkey", "from Valkey", text)
    text = re.sub(r"to Valkey", "to Valkey", text)
    text = re.sub(r"the Valkey", "the Valkey", text)
    text = re.sub(r"a Valkey", "a Valkey", text)
    text = re.sub(r"is Valkey", "is Valkey", text)
    text = re.sub(r"VALKEY_TTL", "VALKEY_TTL", text)
    text = re.sub(r"VALKEY_URL", "VALKEY_URL", text)

    if text != original:
        py.write_text(text, encoding="utf-8")
        count += 1
print(f"Updated {count} files")
