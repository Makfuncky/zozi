#!/usr/bin/env python3
"""
ZOZI Backend — Architecture Audit Section Laws 51-100
Detection logic for database, code quality, testing, infrastructure,
config, observability, and wiring laws.

Uses ASTAnalyzer, ImportGraph, and pre-indexed file lists from
full_system_audit.py. Each finding is recorded via f(lid, cat, sev, file, line, desc, fix).
"""

from __future__ import annotations

import ast
import re
from collections import defaultdict
from pathlib import Path


# ══════════════════════════════════════════════════════════════
# LOCAL HELPERS (self-contained to avoid cross-file dependencies)
# ══════════════════════════════════════════════════════════════

def _parse_ast(content: str):
    """Parse Python source into AST, returning None on failure."""
    try:
        return ast.parse(content)
    except Exception:
        return None


def _get_call_name(node: ast.Call) -> str:
    """Get dotted name of a function call node."""
    if isinstance(node.func, ast.Attribute):
        if isinstance(node.func.value, ast.Name):
            return f"{node.func.value.id}.{node.func.attr}"
        if isinstance(node.func.value, ast.Attribute):
            if isinstance(node.func.value.value, ast.Name):
                return f"{node.func.value.value.id}.{node.func.value.attr}.{node.func.attr}"
    elif isinstance(node.func, ast.Name):
        return node.func.id
    return ""


def _get_function_source(content: str, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Extract source lines of a function node."""
    lines = content.split("\n")
    end = getattr(node, 'end_lineno', None)
    if end is None:
        end = node.lineno + 100
    return "\n".join(lines[node.lineno - 1:end])


def _extract_model_classes(content: str) -> list[tuple[str, str, int]]:
    """Extract ORM model class definitions with body and line number."""
    results = []
    lines = content.split("\n")
    tree = _parse_ast(content)
    if not tree:
        return results
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            body = _get_class_body(lines, node)
            results.append((node.name, body, node.lineno))
    return results


def _get_class_body(lines: list[str], node: ast.ClassDef) -> str:
    """Extract class body source from lines."""
    if hasattr(node, 'end_lineno') and node.end_lineno:
        return "\n".join(lines[node.lineno - 1:node.end_lineno])
    start = node.lineno - 1
    end = min(start + 100, len(lines))
    return "\n".join(lines[start:end])


def _is_orm_model(cls_body: str) -> bool:
    """Check if a class body represents an ORM model."""
    return "__tablename__" in cls_body or "Base" in cls_body


def _extract_tablename(cls_body: str) -> str | None:
    """Extract __tablename__ value from class body."""
    m = re.search(r'__tablename__\s*=\s*["\']([^"\']+)["\']', cls_body)
    return m.group(1) if m else None


def _is_silent_except(body: list[ast.stmt]) -> bool:
    """Check if an except handler body is silent (pass, ellipsis, or comments only)."""
    if not body:
        return True
    for stmt in body:
        if isinstance(stmt, ast.Pass):
            continue
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value is ...:
            continue
        if isinstance(stmt, ast.Raise):
            return False
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            func = stmt.value.func
            if isinstance(func, ast.Attribute) and func.attr in ("debug", "info", "warning", "error", "exception", "log"):
                return False
            if isinstance(func, ast.Name) and func.id in ("logger", "log"):
                return False
        if isinstance(stmt, ast.Assign):
            continue
        if isinstance(stmt, (ast.Continue, ast.Break)):
            continue
        return False
    return True


def _has_import_from(content: str, prefix: str) -> bool:
    """Check if content contains a from-import from the given prefix."""
    return bool(re.search(rf'from\s+{re.escape(prefix)}', content))


# ══════════════════════════════════════════════════════════════
# LAW 47: Connection pool sizing
# ══════════════════════════════════════════════════════════════

def _law47_connection_pool_sizing():
    """Law 47: pool_size >= 10, max_overflow >= 20 for 100K+ users."""
    for p in INFRA:
        content = read(p)
        if not content:
            continue
        if "create_async_engine" not in content and "create_engine" not in content:
            continue
        # Check for pool_size parameter
        pool_size_match = re.search(r'pool_size\s*=\s*(\d+)', content)
        max_overflow_match = re.search(r'max_overflow\s*=\s*(\d+)', content)
        if pool_size_match:
            pool_size = int(pool_size_match.group(1))
            if pool_size < 10:
                f(47, "database", "high", rel(p), 0,
                  f"pool_size={pool_size} is below minimum of 10 for 100K+ user scale",
                  "Set pool_size=20, max_overflow=40 to handle production load")
        else:
            f(47, "database", "medium", rel(p), 0,
              "create_engine call missing explicit pool_size parameter",
              "Add pool_size=20, max_overflow=40 to engine configuration")
        if max_overflow_match:
            max_overflow = int(max_overflow_match.group(1))
            if max_overflow < 20:
                f(47, "database", "high", rel(p), 0,
                  f"max_overflow={max_overflow} is below minimum of 20",
                  "Set max_overflow=40 to handle connection spikes")
        else:
            f(47, "database", "medium", rel(p), 0,
              "create_engine call missing explicit max_overflow parameter",
              "Add max_overflow=40 to engine configuration")


# ══════════════════════════════════════════════════════════════
# LAW 48: Read replica separation
# ══════════════════════════════════════════════════════════════

def _law48_read_replica_separation():
    """Law 48: Read queries use get_read_db() or replica engine."""
    has_read_db = False
    has_replica_config = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if "get_read_db" in content:
            has_read_db = True
        if "read_replica" in content.lower() or "replica_url" in content.lower():
            has_replica_config = True
    if not has_read_db:
        f(48, "database", "medium", "infrastructure/database/", 0,
          "No get_read_db() function found — read queries should use replica",
          "Create get_read_db() dependency that routes to read replica engine")
    if not has_replica_config:
        f(48, "database", "low", "infrastructure/database/", 0,
          "No read replica configuration found",
          "Add DATABASE_REPLICA_URL config and create separate engine for reads")


# ══════════════════════════════════════════════════════════════
# LAW 49: Linear migration history
# ══════════════════════════════════════════════════════════════

def _law49_linear_migration_history():
    """Law 49: Alembic history must have no divergent heads."""
    alembic_dir = ROOT / "alembic" / "versions"
    if not alembic_dir.exists():
        return
    migration_files = list(alembic_dir.glob("*.py"))
    if not migration_files:
        return
    # Check for multiple heads by looking at down_revision
    heads = []
    for p in migration_files:
        content = read(p)
        if not content:
            continue
        if "down_revision = None" in content or "down_revision=None" in content:
            heads.append(p)
    if len(heads) > 1:
        for h in heads:
            f(49, "database", "high", rel(h), 0,
              f"Multiple alembic heads detected — migration history is branched",
              "Run 'alembic merge heads' to create a merge migration and linearize history")


# ══════════════════════════════════════════════════════════════
# LAW 50: Explicit transactions
# ══════════════════════════════════════════════════════════════

def _law50_explicit_transactions():
    """Law 50: No autocommit patterns; explicit transaction management required."""
    for p in SERVICES:
        content = read(p)
        if not content:
            continue
        tree = _parse_ast(content)
        if not tree:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_source = _get_function_source(content, node)
                has_db_op = any(pat in func_source for pat in [
                    ".add(", ".delete(", ".merge(", ".flush(", ".commit("
                ])
                has_transaction = "begin_nested" in func_source or "begin()" in func_source or \
                                   "async with" in func_source or "@contextmanager" in func_source
                if has_db_op and not has_transaction and "get_db" not in func_source:
                    f(50, "database", "medium", rel(p), node.lineno,
                      f"Function '{node.name}' performs DB operations without explicit transaction management",
                      "Use 'async with session.begin()' or dependency-injected get_db for transaction boundaries")
                    break


# ══════════════════════════════════════════════════════════════
# LAW 51: Single table ownership
# ══════════════════════════════════════════════════════════════

def _law51_single_table_ownership():
    """Law 51: Each table defined in exactly one domain. Duplicate __tablename__ FORBIDDEN."""
    table_map: dict[str, list[tuple[Path, int]]] = defaultdict(list)
    for p in MODELS:
        content = read(p)
        if not content:
            continue
        for i, line in enumerate(content.split("\n"), 1):
            m = re.match(r'\s*__tablename__\s*=\s*["\']([^"\']+)["\']', line)
            if m:
                table_map[m.group(1)].append((p, i))

    for table_name, locations in table_map.items():
        domain_files: dict[str, list[tuple[Path, int]]] = defaultdict(list)
        for p, line in locations:
            parts = rel(p).split("/")
            domain = parts[1] if len(parts) > 1 else "unknown"
            domain_files[domain].append((p, line))

        if len(domain_files) > 1:
            for domain, locs in domain_files.items():
                for p, line in locs:
                    others = [d for d in domain_files if d != domain]
                    f(51, "database", "critical", rel(p), line,
                      f"Table '{table_name}' defined in multiple domains: {domain} and {others}",
                      f"Move '{table_name}' to a single domain. Use cross-domain reads via ports.py")


# ══════════════════════════════════════════════════════════════
# LAW 52: FK constraints
# ══════════════════════════════════════════════════════════════

def _law52_fk_constraints():
    """Law 52: All FK columns have explicit ForeignKey with ondelete."""
    fk_pattern = re.compile(r'^\s*(\w+)\s*=\s*Column\s*\(')
    for p in MODELS:
        content = read(p)
        if not content:
            continue
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            col_match = fk_pattern.match(line)
            if col_match:
                col_name = col_match.group(1)
                if col_name.endswith("_id") and col_name != "id":
                    block = "\n".join(lines[max(0, i - 1):min(len(lines), i + 5)])
                    if "ForeignKey" not in block:
                        f(52, "database", "high", rel(p), i,
                          f"Column '{col_name}' appears to be a FK but lacks ForeignKey constraint",
                          f"Add ForeignKey with ondelete: Column({col_name}, ForeignKey('schema.table.id', ondelete='RESTRICT'))")


# ══════════════════════════════════════════════════════════════
# LAW 53: Index FK columns
# ══════════════════════════════════════════════════════════════

def _law53_index_fk_columns():
    """Law 53: All FK columns have explicit index."""
    fk_col_pattern = re.compile(r'^\s*(\w+_id)\s*=\s*Column\s*\(')
    for p in MODELS:
        content = read(p)
        if not content:
            continue
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            col_match = fk_col_pattern.match(line)
            if col_match:
                col_name = col_match.group(1)
                block = "\n".join(lines[max(0, i - 1):min(len(lines), i + 3)])
                if "ForeignKey" in block and "index=True" not in block:
                    f(53, "database", "medium", rel(p), i,
                      f"FK column '{col_name}' lacks index=True",
                      f"Add index=True to FK column: Column({col_name}, ForeignKey(...), index=True)")


# ══════════════════════════════════════════════════════════════
# LAW 54: Soft delete
# ══════════════════════════════════════════════════════════════

def _law54_soft_delete():
    """Law 54: All user-facing tables use is_deleted."""
    user_facing_keywords = {"user", "order", "product", "customer", "supplier",
                            "employee", "payment", "shipment", "cart", "address",
                            "account", "session", "notification", "message", "campaign"}
    for p in MODELS:
        content = read(p)
        if not content:
            continue
        classes = _extract_model_classes(content)
        for cls_name, cls_body, line_no in classes:
            if not _is_orm_model(cls_body):
                continue
            table_name = _extract_tablename(cls_body)
            if table_name and any(kw in table_name.lower() for kw in user_facing_keywords):
                if "is_deleted" not in cls_body:
                    f(54, "database", "medium", rel(p), line_no,
                      f"User-facing table '{table_name}' ({cls_name}) lacks is_deleted column",
                      f"Add soft-delete: is_deleted = Column(Boolean, default=False, nullable=False, index=True)")


# ══════════════════════════════════════════════════════════════
# LAW 55: Schema-per-domain
# ══════════════════════════════════════════════════════════════

def _law55_schema_per_domain():
    """Law 55: Every model declares __table_args__ = {schema: <domain>}."""
    for p in MODELS:
        content = read(p)
        if not content:
            continue
        classes = _extract_model_classes(content)
        for cls_name, cls_body, line_no in classes:
            if not _is_orm_model(cls_body):
                continue
            if "__table_args__" not in cls_body:
                f(55, "database", "high", rel(p), line_no,
                  f"Model '{cls_name}' missing __table_args__ with schema declaration",
                  f"Add: __table_args__ = {{'schema': '<domain>'}} where <domain> matches the domain package")


# ══════════════════════════════════════════════════════════════
# LAW 56: No forbidden schemas
# ══════════════════════════════════════════════════════════════

def _law56_no_forbidden_schemas():
    """Law 56: core, platform, identity schemas FORBIDDEN."""
    forbidden = {"core", "platform", "identity"}
    for p in MODELS:
        content = read(p)
        if not content:
            continue
        for i, line in enumerate(content.split("\n"), 1):
            m = re.search(r'["\']schema["\']\s*:\s*["\']([^"\']+)["\']', line)
            if m and m.group(1).lower() in forbidden:
                f(56, "database", "high", rel(p), i,
                  f"Forbidden schema '{m.group(1)}' used — core/platform/identity are reserved",
                  f"Use domain-specific schema (e.g., 'orders', 'catalog', 'finance') instead of '{m.group(1)}'")


# ══════════════════════════════════════════════════════════════
# LAW 57: Migration safety
# ══════════════════════════════════════════════════════════════

def _law57_migration_safety():
    """Law 57: Destructive migrations include backward-compatible strategy."""
    alembic_dir = ROOT / "alembic" / "versions"
    if not alembic_dir.exists():
        return
    destructive_patterns = [
        (re.compile(r'op\.drop_table\s*\(', re.I), "drop_table"),
        (re.compile(r'op\.drop_column\s*\(', re.I), "drop_column"),
        (re.compile(r'op\.execute\s*\(\s*["\']DROP', re.I), "execute DROP"),
        (re.compile(r'op\.execute\s*\(\s*["\']DELETE\s+FROM', re.I), "execute DELETE"),
        (re.compile(r'op\.alter_column\s*\([^)]*nullable\s*=\s*False', re.I | re.S), "alter_column NOT NULL"),
    ]
    for p in alembic_dir.glob("*.py"):
        content = read(p)
        if not content:
            continue
        for pattern, desc in destructive_patterns:
            for i, line in enumerate(content.split("\n"), 1):
                if pattern.search(line):
                    block = "\n".join(content.split("\n")[max(0, i - 3):min(len(content.split("\n")), i + 3)])
                    if "step" not in block.lower() and "phase" not in block.lower():
                        f(57, "database", "medium", rel(p), i,
                          f"Destructive migration ({desc}) without documented backward-compatible strategy",
                          f"Add a multi-step migration strategy: 1) Add new column/table, 2) Backfill data, 3) Switch reads, 4) Drop old")


# ══════════════════════════════════════════════════════════════
# LAW 61: Bounded caches
# ══════════════════════════════════════════════════════════════

def _law61_bounded_caches():
    """Law 61: All in-memory caches have max size and/or TTL."""
    cache_patterns = [
        (re.compile(r'(\w+)\s*=\s*\{\s*\}'), "empty dict"),
        (re.compile(r'(\w+)\s*=\s*defaultdict\s*\('), "defaultdict"),
        (re.compile(r'(\w+)\s*=\s*dict\s*\(\s*\)'), "dict()"),
    ]
    bounded_indicators = {"maxsize", "max_size", "ttl", "TTL", "lru_cache", "cachetools", "TTLCache", "LRUCache"}
    for p in ALL_PY:
        r = rel(p)
        if "/tests/" in r:
            continue
        content = read(p)
        if not content:
            continue
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            for pattern, desc in cache_patterns:
                m = pattern.match(line.strip())
                if m:
                    var_name = m.group(1)
                    context = "\n".join(lines[max(0, i - 3):min(len(lines), i + 10)])
                    if not any(ind in context for ind in bounded_indicators):
                        f(61, "code_quality", "medium", rel(p), i,
                          f"Unbounded cache '{var_name}' ({desc}) without max size or TTL",
                          f"Use @lru_cache(maxsize=128) or cachetools.TTLCache(maxsize=1000, ttl=300)")


# ══════════════════════════════════════════════════════════════
# LAW 62: TODO/FIXME hygiene
# ══════════════════════════════════════════════════════════════

def _law62_todo_hygiene():
    """Law 62: TODO/FIXME must include ticket reference and expiration."""
    ticket_pattern = re.compile(r'(?:TODO|FIXME|HACK|XXX)\s*[:\-]?\s*(?:\[?[A-Z]+-\d+\]?|\d{4}-\d{2}-\d{2})')
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        for i, line in enumerate(content.split("\n"), 1):
            if re.search(r'\b(TODO|FIXME|HACK|XXX)\b', line) and not ticket_pattern.search(line):
                f(62, "code_quality", "low", rel(p), i,
                  f"TODO/FIXME without ticket reference or expiration date",
                  f"Format: TODO[ZOZI-123](expire:2026-09-01): description of what to do")


# ══════════════════════════════════════════════════════════════
# LAW 63: Type hints required
# ══════════════════════════════════════════════════════════════

def _law63_type_hints():
    """Law 63: All public function signatures MUST have type hints."""
    for p in ALL_PY:
        r = rel(p)
        if "/tests/" in r or r.startswith("scripts/"):
            continue
        content = read(p)
        if not content:
            continue
        tree = _parse_ast(content)
        if not tree:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_"):
                    continue
                if node.returns is None:
                    f(63, "code_quality", "low", rel(p), node.lineno,
                      f"Public function '{node.name}' missing return type hint",
                      f"Add return type: def {node.name}(...) -> <ReturnType>:")


# ══════════════════════════════════════════════════════════════
# LAW 64: Function length <= 50
# ══════════════════════════════════════════════════════════════

def _law64_function_length():
    """Law 64: Functions SHOULD NOT exceed 50 lines."""
    for p in ALL_PY:
        r = rel(p)
        if "/tests/" in r:
            continue
        content = read(p)
        if not content:
            continue
        tree = _parse_ast(content)
        if not tree:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end = getattr(node, 'end_lineno', None)
                if end and (end - node.lineno) > 50:
                    f(64, "code_quality", "low", rel(p), node.lineno,
                      f"Function '{node.name}' is {end - node.lineno} lines (max 50)",
                      f"Extract helper functions. Aim for single-responsibility functions under 30 lines.")


# ══════════════════════════════════════════════════════════════
# LAW 65: Indentation <= 4 levels
# ══════════════════════════════════════════════════════════════

def _law65_indentation_depth():
    """Law 65: Maximum 4 levels of indentation per function."""
    for p in ALL_PY:
        r = rel(p)
        if "/tests/" in r:
            continue
        content = read(p)
        if not content:
            continue
        lines = content.split("\n")
        tree = _parse_ast(content)
        if not tree:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end = getattr(node, 'end_lineno', node.lineno + 100)
                func_lines = lines[node.lineno - 1:end] if end else lines[node.lineno - 1:]
                for j, fline in enumerate(func_lines):
                    stripped = fline.lstrip()
                    if not stripped or stripped.startswith("#"):
                        continue
                    indent = len(fline) - len(stripped)
                    level = indent // 4
                    if level > 4:
                        f(65, "code_quality", "low", rel(p), node.lineno + j,
                          f"Function '{node.name}' has >4 indentation levels (level {level})",
                          f"Extract nested logic into helper functions. Use early returns to reduce nesting.")
                        break


# ══════════════════════════════════════════════════════════════
# LAW 66: No magic numbers
# ══════════════════════════════════════════════════════════════

def _law66_no_magic_numbers():
    """Law 66: Numeric constants MUST be named constants."""
    skip_contexts = {"index=True", "index=False", "primary_key=True", "nullable=True",
                     "nullable=False", "pool_size", "max_overflow", "max_length",
                     "precision", "scale", "server_default", "ForeignKey"}
    skip_values = {0, 1, -1, 2, 3, 4, 5, 10, 20, 50, 100, 0.0, 1.0, 100.0, 1000}
    for p in ALL_PY:
        r = rel(p)
        if "/tests/" in r:
            continue
        content = read(p)
        if not content:
            continue
        tree = _parse_ast(content)
        if not tree:
            continue
        lines = content.split("\n")
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in ast.walk(node):
                    if isinstance(child, ast.Constant) and isinstance(child.value, (int, float)):
                        if child.value in skip_values:
                            continue
                        if isinstance(child.value, float) and child.value < 0:
                            continue
                        line_content = lines[child.lineno - 1] if child.lineno <= len(lines) else ""
                        if any(sc in line_content for sc in skip_contexts):
                            continue
                        # Skip common patterns: range(N), [:N], [-N:]
                        if "range(" in line_content or "[" in line_content:
                            continue
                        f(66, "code_quality", "low", rel(p), child.lineno,
                          f"Magic number {child.value} in function '{node.name}'",
                          f"Extract to named constant: MAX_RETRIES = {child.value} at module level")


# ══════════════════════════════════════════════════════════════
# LAW 67: DRY principle
# ══════════════════════════════════════════════════════════════

def _law67_dry_principle():
    """Law 67: Duplicate code blocks (>5 lines) MUST be extracted."""
    file_blocks: dict[str, list[tuple[Path, int]]] = defaultdict(list)
    for p in ALL_PY:
        r = rel(p)
        if "/tests/" in r:
            continue
        content = read(p)
        if not content:
            continue
        lines = content.split("\n")
        for i in range(len(lines) - 10):
            block = "\n".join(lines[i:i + 11])
            stripped = "\n".join(l.strip() for l in block.split("\n") if l.strip() and not l.strip().startswith("#"))
            if len(stripped) > 200:
                file_blocks[stripped].append((p, i + 1))
    for block, locations in file_blocks.items():
        if len(locations) >= 3:
            for p, line in locations[:3]:
                f(67, "code_quality", "low", rel(p), line,
                  f"Duplicate code block found in {len(locations)} locations",
                  f"Extract repeated logic into a shared utility function in infrastructure/utils/")


# ══════════════════════════════════════════════════════════════
# LAW 68: Consistent errors
# ══════════════════════════════════════════════════════════════

def _law68_consistent_errors():
    """Law 68: All service functions use consistent error pattern."""
    error_patterns = {
        "http_exception": re.compile(r'raise\s+HTTPException'),
        "value_error": re.compile(r'raise\s+ValueError'),
        "custom_error": re.compile(r'raise\s+\w+Error'),
    }
    for p in SERVICES:
        content = read(p)
        if not content:
            continue
        found_patterns = set()
        for name, pattern in error_patterns.items():
            if pattern.search(content):
                found_patterns.add(name)
        if len(found_patterns) > 1:
            f(68, "code_quality", "medium", rel(p), 0,
              f"Mixed error handling patterns: {found_patterns}",
              f"Use consistent error pattern: raise HTTPException(status_code=..., detail=...) for all service-layer errors")


# ══════════════════════════════════════════════════════════════
# LAW 69: Domain smoke tests
# ══════════════════════════════════════════════════════════════

def _law69_domain_smoke_tests():
    """Law 69: Every domain MUST have at least one smoke test."""
    tested_domains = set()
    for p in TESTS:
        r = rel(p)
        parts = r.split("/")
        for part in parts:
            if part in DOMAINS:
                tested_domains.add(part)
    for domain in DOMAINS:
        if domain not in tested_domains:
            f(69, "testing", "high", f"domains/{domain}/", 0,
              f"Domain '{domain}' has no smoke tests",
              f"Create tests/test_{domain}_smoke.py with at least one test verifying the domain's core service can be instantiated")


# ══════════════════════════════════════════════════════════════
# LAW 70: Architecture law tests
# ══════════════════════════════════════════════════════════════

def _law70_architecture_law_tests():
    """Law 70: Every statically checkable law MUST have a test."""
    arch_test = ROOT / "tests" / "architecture"
    if not arch_test.exists():
        f(70, "testing", "high", "tests/architecture/", 0,
          f"No tests/architecture/ directory — architecture law tests missing",
          f"Create tests/architecture/test_import_laws.py with tests for each statically checkable law")
        return
    test_content = ""
    for p in arch_test.glob("*.py"):
        test_content += read(p)
    if "import" not in test_content.lower() or "law" not in test_content.lower():
        f(70, "testing", "medium", "tests/architecture/", 0,
          f"Architecture law tests may not cover import laws",
          f"Add tests that verify import direction laws (modules→domains→infrastructure→kernel)")


# ══════════════════════════════════════════════════════════════
# LAW 71: No broken tests in CI
# ══════════════════════════════════════════════════════════════

def _law71_no_broken_tests_in_ci():
    """Law 71: Collection-time failures MUST block CI."""
    github_dir = ROOT.parent / ".github"
    ci_files = list(github_dir.glob("*.yml")) if github_dir.exists() else []
    ci_files += list(github_dir.glob("*.yaml")) if github_dir.exists() else []
    if not ci_files:
        f(71, "testing", "medium", ".github/workflows/", 0,
          f"No CI workflow files found",
          f"Create .github/workflows/ci.yml with 'pytest -x --timeout=30' to block CI on test failures")
        return
    for p in ci_files:
        content = read(p)
        if "pytest" in content and "--continue-on-error" in content:
            f(71, "testing", "high", rel(p, ROOT.parent), 0,
              f"CI config has --continue-on-error which allows broken tests to pass",
              f"Remove --continue-on-error from pytest invocation in CI")


# ══════════════════════════════════════════════════════════════
# LAW 72: Cross-domain integration
# ══════════════════════════════════════════════════════════════

def _law72_cross_domain_integration():
    """Law 72: Cross-domain flows MUST have integration tests."""
    cross_domain_tests = ["integration", "e2e", "cross_domain"]
    has_cross = False
    for p in TESTS:
        r = rel(p).lower()
        if any(cd in r for cd in cross_domain_tests):
            has_cross = True
            break
    if not has_cross:
        f(72, "testing", "medium", "tests/", 0,
          f"No cross-domain integration tests found",
          f"Create tests/integration/test_cross_domain_flows.py testing order→payment→fulfillment flow")


# ══════════════════════════════════════════════════════════════
# LAW 73: Performance regression
# ══════════════════════════════════════════════════════════════

def _law73_performance_regression():
    """Law 73: Critical paths MUST have perf regression tests."""
    perf_tests = False
    for p in TESTS:
        r = rel(p).lower()
        if "perf" in r or "benchmark" in r or "performance" in r:
            perf_tests = True
            break
    if not perf_tests:
        f(73, "testing", "low", "tests/", 0,
          f"No performance regression tests found",
          f"Create tests/performance/test_critical_paths.py with timing assertions for order creation, catalog listing")


# ══════════════════════════════════════════════════════════════
# LAW 74: Test isolation
# ══════════════════════════════════════════════════════════════

def _law74_test_isolation():
    """Law 74: All tests use transaction-rolled-back sessions."""
    conftest = ROOT / "tests" / "conftest.py"
    if not conftest.exists():
        f(74, "testing", "high", "tests/conftest.py", 0,
          f"No conftest.py found — test isolation not guaranteed",
          f"Create tests/conftest.py with db_session fixture using transaction rollback")
        return
    content = read(conftest)
    if "rollback" not in content.lower():
        f(74, "testing", "high", "tests/conftest.py", 0,
          f"conftest.py does not implement transaction rollback for test isolation",
          f"Add: yield session in a transaction that rolls back after each test")


# ══════════════════════════════════════════════════════════════
# LAW 75: Graceful degradation
# ══════════════════════════════════════════════════════════════

def _law75_graceful_degradation():
    """Law 75: External failures MUST degrade gracefully AND log WARNING."""
    external_call_patterns = [
        "requests.", "stripe.", "send_email", "httpx.", "boto3.",
        "twilio.", "sendgrid.", "s3_client", "urllib"
    ]
    for p in SERVICES:
        content = read(p)
        if not content:
            continue
        tree = _parse_ast(content)
        if not tree:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        call_name = _get_call_name(child)
                        if any(call_name.startswith(pat) or pat in call_name for pat in external_call_patterns):
                            func_source = _get_function_source(content, node)
                            if "try:" not in func_source or "logger.warning" not in func_source:
                                f(75, "infrastructure", "high", rel(p), child.lineno,
                                  f"External call '{call_name}' without graceful degradation (try/except + warning)",
                                  f"Wrap in try/except with logger.warning('External call failed', exc_info=True) and fallback value")


# ══════════════════════════════════════════════════════════════
# LAW 76: Session lifecycle
# ══════════════════════════════════════════════════════════════

def _law76_session_lifecycle():
    """Law 76: Sessions managed via FastAPI dependency injection only."""
    for p in ALL_PY:
        r = rel(p)
        if "/tests/" in r or r.startswith("scripts/"):
            continue
        content = read(p)
        if not content:
            continue
        if "SessionLocal()" in content and "get_db" not in content:
            for i, line in enumerate(content.split("\n"), 1):
                if "SessionLocal()" in line and "def " not in line:
                    f(76, "infrastructure", "high", rel(p), i,
                      f"Manual session creation (SessionLocal()) outside get_db dependency",
                      f"Use FastAPI dependency injection: db: Session = Depends(get_db)")


# ══════════════════════════════════════════════════════════════
# LAW 77: Async resource safety
# ══════════════════════════════════════════════════════════════

def _law77_async_resource_safety():
    """Law 77: Async resources use asyncio.Lock for init/disposal."""
    for p in ALL_PY:
        r = rel(p)
        if "/tests/" in r:
            continue
        content = read(p)
        if not content:
            continue
        if "async def __aenter__" in content or "async def __aexit__" in content:
            if "asyncio.Lock" not in content and "asyncio.Semaphore" not in content:
                f(77, "infrastructure", "medium", rel(p), 0,
                  f"Async context manager without asyncio.Lock for thread-safe init/disposal",
                  f"Add: self._lock = asyncio.Lock() and use async with self._lock: in __aenter__/__aexit__")


# ══════════════════════════════════════════════════════════════
# LAW 78: Middleware ordering
# ══════════════════════════════════════════════════════════════

def _law78_middleware_ordering():
    """Law 78: Pipeline order FIXED."""
    orchestrator = ROOT / "middleware" / "orchestrator.py"
    if not orchestrator.exists():
        f(78, "infrastructure", "high", "middleware/orchestrator.py", 0,
          f"Middleware orchestrator not found",
          f"Create middleware/orchestrator.py with fixed pipeline order: Foundation→Security→Rate→Geo→Compliance")
        return
    content = read(orchestrator)
    expected_order = ["GZipMiddleware", "CORSMiddleware", "IPExtractionMiddleware",
                      "SecurityHeadersMiddleware", "RateLimitMiddleware"]
    last_pos = -1
    for mw in expected_order:
        pos = content.find(mw)
        if pos == -1:
            f(78, "infrastructure", "medium", "middleware/orchestrator.py", 0,
              f"Expected middleware '{mw}' not found in orchestrator",
              f"Ensure all standard middleware are registered in the correct order")
        elif pos < last_pos:
            f(78, "infrastructure", "high", "middleware/orchestrator.py", 0,
              f"Middleware '{mw}' appears out of expected order",
              f"Fix pipeline order: Foundation→Security→Rate Limiting→Geo→Compliance")
        last_pos = pos


# ══════════════════════════════════════════════════════════════
# LAW 79: Global exception handler
# ══════════════════════════════════════════════════════════════

def _law79_global_exception_handler():
    """Law 79: Global exception handler catches all uncaught exceptions."""
    main_py = ROOT / "main.py"
    if not main_py.exists():
        return
    content = read(main_py)
    if "exception_handler" not in content and "Exception" not in content:
        f(79, "infrastructure", "high", "main.py", 0,
          f"No global exception handler found in main.py",
          f"Add: @app.exception_handler(Exception) async def general_exception_handler(request, exc)")


# ══════════════════════════════════════════════════════════════
# LAW 80: Graceful shutdown
# ══════════════════════════════════════════════════════════════

def _law80_graceful_shutdown():
    """Law 80: Shutdown disposes DB engine, Redis, workers."""
    lifespan = ROOT / "lifespan.py"
    if not lifespan.exists():
        f(80, "infrastructure", "high", "lifespan.py", 0,
          f"No lifespan.py found — graceful shutdown not implemented",
          f"Create lifespan.py with shutdown logic that disposes DB engine, Redis connections, and stops workers")
        return
    content = read(lifespan)
    shutdown_section = content[content.find("yield"):] if "yield" in content else ""
    if "engine.dispose" not in content and "engine.dispose" not in shutdown_section:
        f(80, "infrastructure", "medium", "lifespan.py", 0,
          f"Shutdown does not dispose DB engine",
          f"Add: engine.dispose() in the shutdown section after yield")


# ══════════════════════════════════════════════════════════════
# LAW 81: Health checks
# ══════════════════════════════════════════════════════════════

def _law81_health_checks():
    """Law 81: /health, /health/deps, /health/ready verify dependencies."""
    main_py = ROOT / "main.py"
    if not main_py.exists():
        return
    content = read(main_py)
    required_endpoints = ["/health", "/health/deps", "/health/ready"]
    for endpoint in required_endpoints:
        if endpoint not in content:
            f(81, "infrastructure", "high", "main.py", 0,
              f"Missing health endpoint '{endpoint}'",
              f"Add @{app}.get('{endpoint}') endpoint that verifies dependency health")


# ══════════════════════════════════════════════════════════════
# LAW 82: No default credentials
# ══════════════════════════════════════════════════════════════

def _law82_no_default_credentials():
    """Law 82: Config fallbacks MUST NOT contain real credentials."""
    credential_patterns = [
        (re.compile(r'os\.getenv\s*\(\s*["\'](?:PASSWORD|SECRET|TOKEN|KEY|API_KEY)["\']\s*,\s*["\'][^"\']{8,}["\']'), "default password/secret"),
        (re.compile(r'["\'](?:password|secret|token|api_key)\s*[:=]\s*["\'][^"\']{8,}["\']', re.I), "hardcoded credential"),
    ]
    for p in ALL_PY:
        r = rel(p)
        if "/tests/" in r:
            continue
        content = read(p)
        if not content:
            continue
        for i, line in enumerate(content.split("\n"), 1):
            for pattern, desc in credential_patterns:
                if pattern.search(line):
                    f(82, "config", "critical", rel(p), i,
                      f"Potential hardcoded credential in config: {desc}",
                      f"Remove default value. Use os.getenv('SECRET_KEY') with no fallback, and fail fast if unset.")


# ══════════════════════════════════════════════════════════════
# LAW 83: Environment validation
# ══════════════════════════════════════════════════════════════

def _law83_environment_validation():
    """Law 83: Required env vars validated at startup."""
    config_file = ROOT / "infrastructure" / "utils" / "config.py"
    if not config_file.exists():
        return
    content = read(config_file)
    if "validate" not in content.lower() and "raise" not in content.lower():
        f(83, "config", "medium", "infrastructure/utils/config.py", 0,
          f"No startup validation of required environment variables",
          f"Add validation in Settings.__init__ that raises ValueError for missing required vars")


# ══════════════════════════════════════════════════════════════
# LAW 84: Typed feature flags
# ══════════════════════════════════════════════════════════════

def _law84_typed_feature_flags():
    """Law 84: Flags use pydantic-settings. Raw os.getenv() FORBIDDEN."""
    for p in ALL_PY:
        r = rel(p)
        if r == "infrastructure/utils/config.py" or "/tests/" in r:
            continue
        content = read(p)
        if not content:
            continue
        if "from infrastructure.utils.config import" in content:
            continue
        for i, line in enumerate(content.split("\n"), 1):
            if re.search(r'os\.getenv\s*\(', line) and "settings." not in line:
                f(84, "config", "medium", rel(p), i,
                  f"Raw os.getenv() usage — use pydantic-settings instead",
                  f"Import settings from infrastructure.utils.config and access settings.<attr> instead of os.getenv()")


# ══════════════════════════════════════════════════════════════
# LAW 85: Secret rotation
# ══════════════════════════════════════════════════════════════

def _law85_secret_rotation():
    """Law 85: Secrets rotatable without deployment."""
    config_file = ROOT / "infrastructure" / "utils" / "config.py"
    if not config_file.exists():
        return
    content = read(config_file)
    if "os.getenv" in content and "SECRET" in content:
        f(85, "config", "low", "infrastructure/utils/config.py", 0,
          f"Secrets loaded from env vars — ensure rotation strategy exists",
          f"Document secret rotation procedure: update env var, restart workers. Consider adding versioned secret support.")


# ══════════════════════════════════════════════════════════════
# LAW 86: Env-specific configs
# ══════════════════════════════════════════════════════════════

def _law86_env_specific_configs():
    """Law 86: Prod, staging, dev have separate config profiles."""
    config_file = ROOT / "infrastructure" / "utils" / "config.py"
    if not config_file.exists():
        return
    content = read(config_file)
    envs = ["production", "staging", "development"]
    found_envs = [env for env in envs if env in content]
    if len(found_envs) < 2:
        f(86, "config", "low", "infrastructure/utils/config.py", 0,
          f"Config does not distinguish between environments (found: {found_envs})",
          f"Add environment-specific settings: if settings.app_env == 'production': ...")


# ══════════════════════════════════════════════════════════════
# LAW 92: Structured logging
# ══════════════════════════════════════════════════════════════

def _law92_structured_logging():
    """Law 92: All logs use structlog with context."""
    for p in ALL_PY:
        r = rel(p)
        if "/tests/" in r or r.startswith("scripts/"):
            continue
        content = read(p)
        if not content:
            continue
        if "import logging" in content and "structlog" not in content:
            for i, line in enumerate(content.split("\n"), 1):
                if "logging.getLogger" in line and "structlog" not in line:
                    f(92, "observability", "medium", rel(p), i,
                      f"Using stdlib logging instead of structlog",
                      f"Replace: logger = structlog.get_logger(__name__) for structured JSON logging with context")
                    break


# ══════════════════════════════════════════════════════════════
# LAW 93: Request tracing
# ══════════════════════════════════════════════════════════════

def _law93_request_tracing():
    """Law 93: All requests carry request_id propagated through service calls."""
    main_py = ROOT / "main.py"
    if not main_py.exists():
        return
    content = read(main_py)
    if "request_id" not in content.lower() and "X-Request-ID" not in content:
        f(93, "observability", "medium", "main.py", 0,
          f"No request_id propagation found",
          f"Add RequestIDMiddleware and propagate request_id through service calls via structlog context")


# ══════════════════════════════════════════════════════════════
# LAW 94: Metrics emission
# ══════════════════════════════════════════════════════════════

def _law94_metrics_emission():
    """Law 94: Critical paths emit Prometheus metrics."""
    has_prometheus = False
    for p in ALL_PY:
        r = rel(p)
        if "/tests/" in r:
            continue
        content = read(p)
        if "prometheus" in content.lower():
            has_prometheus = True
            break
    if not has_prometheus:
        f(94, "observability", "medium", "infrastructure/", 0,
          f"No Prometheus metrics instrumentation found",
          f"Add prometheus-fastapi-instrumentator and emit counters/histograms for critical paths")


# ══════════════════════════════════════════════════════════════
# LAW 95: Error tracking
# ══════════════════════════════════════════════════════════════

def _law95_error_tracking():
    """Law 95: Unhandled exceptions reported to Sentry."""
    has_sentry = False
    for p in ALL_PY:
        r = rel(p)
        if "/tests/" in r:
            continue
        content = read(p)
        if "sentry" in content.lower():
            has_sentry = True
            break
    if not has_sentry:
        f(95, "observability", "medium", "infrastructure/", 0,
          f"No Sentry error tracking integration found",
          f"Add: import sentry_sdk; sentry_sdk.init(dsn=settings.sentry_dsn) in main.py")


# ══════════════════════════════════════════════════════════════
# LAW 96: Audit trail
# ══════════════════════════════════════════════════════════════

def _law96_audit_trail():
    """Law 96: State-changing operations write to domains/audit/."""
    audit_domain = ROOT / "domains" / "audit"
    if not audit_domain.exists():
        f(96, "observability", "high", "domains/audit/", 0,
          f"No domains/audit/ directory — audit trail not implemented",
          f"Create domains/audit/ with service that records state-changing operations")
        return
    audit_services = list((audit_domain / "services").glob("*.py")) if (audit_domain / "services").exists() else []
    if len(audit_services) <= 1:
        f(96, "observability", "medium", "domains/audit/services/", 0,
          f"Audit domain has no service implementations",
          f"Add audit service that records: actor, action, target, timestamp, before/after state")


# ══════════════════════════════════════════════════════════════
# LAW 97: Import direction
# ══════════════════════════════════════════════════════════════

def _law97_import_direction():
    """Law 97: Imports MUST follow modules → domains → infrastructure → kernel."""
    for p in ALL_PY:
        r = rel(p)
        content = read(p)
        if not content:
            continue
        parts = r.split("/")
        if len(parts) < 2:
            continue
        source_layer = parts[0]
        for i, line in enumerate(content.split("\n"), 1):
            if not line.strip().startswith("from ") and not line.strip().startswith("import "):
                continue
            if _is_reverse_import(source_layer, line):
                f(97, "wiring", "high", rel(p), i,
                  f"Reverse import: {source_layer} imports from a higher layer",
                  f"Fix import direction: modules→domains→infrastructure→kernel. Use ports.py for cross-domain reads.")


def _is_reverse_import(source_layer: str, line: str) -> bool:
    """Check if an import violates the layer ordering."""
    layer_order = {"modules": 0, "domains": 1, "infrastructure": 2, "kernel": 3, "providers": 4, "rbac": 5}
    source_order = layer_order.get(source_layer, -1)
    if source_order == -1:
        return False
    m = re.match(r'\s*from\s+([\w.]+)', line)
    if not m:
        return False
    import_path = m.group(1)
    import_parts = import_path.split(".")
    import_layer = import_parts[0] if import_parts else ""
    if source_layer == "domains" and import_layer == "modules":
        return True
    if source_layer == "infrastructure" and import_layer in ("modules", "domains"):
        return True
    if source_layer == "kernel" and import_layer in ("modules", "domains", "infrastructure"):
        return True
    return False


# ══════════════════════════════════════════════════════════════
# LAW 98: No circular imports
# ══════════════════════════════════════════════════════════════

def _law98_no_circular_imports():
    """Law 98: Circular chains between any two packages FORBIDDEN."""
    import_map: dict[str, set[str]] = defaultdict(set)
    for p in ALL_PY:
        r = rel(p)
        parts = r.split("/")
        if len(parts) < 3:
            continue
        source_pkg = "/".join(parts[:3])
        content = read(p)
        if not content:
            continue
        for line in content.split("\n"):
            m = re.match(r'\s*from\s+([\w.]+)', line)
            if m:
                import_map[source_pkg].add(m.group(1))
    for pkg, imports in import_map.items():
        for imp in imports:
            if imp in import_map and pkg in import_map[imp]:
                f(98, "wiring", "high", pkg, 0,
                  f"Circular import between '{pkg}' and '{imp}'",
                  f"Break circular dependency: extract shared code to a third module, use TYPE_CHECKING, or lazy imports")


# ══════════════════════════════════════════════════════════════
# LAW 99: No layer crossing
# ══════════════════════════════════════════════════════════════

def _law99_no_layer_crossing():
    """Law 99: Modules don't import infrastructure directly."""
    for p in ALL_PY:
        r = rel(p)
        if not r.startswith("modules/"):
            continue
        content = read(p)
        if not content:
            continue
        for i, line in enumerate(content.split("\n"), 1):
            if re.match(r'\s*from\s+infrastructure\.', line):
                f(99, "wiring", "high", rel(p), i,
                  f"Module directly imports from infrastructure — must go through domain service",
                  f"Move infrastructure call to a domain service, then call the service from the module router")


# ══════════════════════════════════════════════════════════════
# LAW 100: Provider isolation
# ══════════════════════════════════════════════════════════════

def _law100_provider_isolation():
    """Law 100: Providers don't import from domains/modules/rbac/jobs/middleware."""
    forbidden_prefixes = ["domains.", "modules.", "rbac.", "jobs.", "middleware."]
    for p in PROVIDERS:
        content = read(p)
        if not content:
            continue
        for i, line in enumerate(content.split("\n"), 1):
            m = re.match(r'\s*from\s+([\w.]+)', line)
            if m:
                import_path = m.group(1)
                if any(import_path.startswith(fp) for fp in forbidden_prefixes):
                    f(100, "wiring", "critical", rel(p), i,
                      f"Provider imports from forbidden layer: {import_path}",
                      f"Providers must only wrap external SDKs. Move business logic to a domain service.")


# ══════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════

def run_checks():
    """Run all law checks for laws 51-100."""
    # Database laws (47-57)
    _law47_connection_pool_sizing()
    _law48_read_replica_separation()
    _law49_linear_migration_history()
    _law50_explicit_transactions()
    _law51_single_table_ownership()
    _law52_fk_constraints()
    _law53_index_fk_columns()
    _law54_soft_delete()
    _law55_schema_per_domain()
    _law56_no_forbidden_schemas()
    _law57_migration_safety()

    # Code quality laws (61-68)
    _law61_bounded_caches()
    _law62_todo_hygiene()
    _law63_type_hints()
    _law64_function_length()
    _law65_indentation_depth()
    _law66_no_magic_numbers()
    _law67_dry_principle()
    _law68_consistent_errors()

    # Testing laws (69-74)
    _law69_domain_smoke_tests()
    _law70_architecture_law_tests()
    _law71_no_broken_tests_in_ci()
    _law72_cross_domain_integration()
    _law73_performance_regression()
    _law74_test_isolation()

    # Infrastructure laws (75-81)
    _law75_graceful_degradation()
    _law76_session_lifecycle()
    _law77_async_resource_safety()
    _law78_middleware_ordering()
    _law79_global_exception_handler()
    _law80_graceful_shutdown()
    _law81_health_checks()

    # Config laws (82-86)
    _law82_no_default_credentials()
    _law83_environment_validation()
    _law84_typed_feature_flags()
    _law85_secret_rotation()
    _law86_env_specific_configs()

    # Observability laws (92-96)
    _law92_structured_logging()
    _law93_request_tracing()
    _law94_metrics_emission()
    _law95_error_tracking()
    _law96_audit_trail()

    # Wiring laws (97-100)
    _law97_import_direction()
    _law98_no_circular_imports()
    _law99_no_layer_crossing()
    _law100_provider_isolation()
