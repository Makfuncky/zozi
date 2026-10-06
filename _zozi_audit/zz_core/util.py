"""ZOZI Forensic Audit — Core utilities."""

from __future__ import annotations

import ast
import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generator, Iterator, Optional


def walk_files(
    root: Path,
    include: set[str] | None = None,
    exclude: set[str] | None = None,
) -> Generator[Path, None, None]:
    """Bounded recursive walk, symlink-safe, ignore directories."""
    exclude = exclude or {
        ".git", ".kilo", "node_modules", "__pycache__", ".pytest_cache",
        ".hypothesis", ".next", "dist", "build", "venv", ".venv",
        "_extra_files", "_legacy.bak", "test-results", "playwright-report",
        "logs", "var",
    }
    include = include or {".py", ".ts", ".tsx", ".js", ".json", ".yaml", ".yml", ".toml", ".md", ".ini", ".txt", ".csv", ".sql"}
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in exclude and not d.startswith(".")]
        for fname in filenames:
            fpath = Path(dirpath) / fname
            if fpath.suffix.lower() in include and not fname.endswith((".min.js", ".map")):
                yield fpath


def is_generated(path: Path) -> bool:
    """Detect minified/generated/pyc/binary."""
    return path.suffix.lower() in {".pyc", ".min.js", ".map", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2", ".ttf", ".eot"}


def read_text(path: Path, max_bytes: int = 2_000_000) -> tuple[str, bool]:
    """Tolerant UTF-8/UTF-16 read, returns (text, truncated).

    `utf-8-sig`, not `utf-8`: 19 source files in this repo start with a UTF-8
    BOM. CPython accepts those (and `compileall` exits 0), so they are valid
    Python -- but decoding with plain `utf-8` leaves U+FEFF as the first
    character and `ast.parse` then rejects it. Since every AST-based check skips
    files whose parse fails, those 19 files were silently excluded from the whole
    suite while appearing to pass.
    """
    try:
        raw = path.read_bytes()[:max_bytes]
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw.decode("utf-16", errors="replace")
        return text, len(raw) >= max_bytes
    except Exception:
        return "", False


def line_of(text: str, needle: str, start: int = 0) -> int:
    """1-based line for a substring."""
    idx = text.find(needle, start)
    if idx == -1:
        return 0
    return text[:idx].count("\n") + 1


def snippet(text: str, line: int, pad: int = 2, width: int = 400) -> str:
    """Quoted evidence window."""
    lines = text.splitlines()
    lo = max(0, line - 1 - pad)
    hi = min(len(lines), line + pad)
    selected = "\n".join(lines[lo:hi])
    if len(selected) > width:
        selected = selected[:width] + "..."
    return selected


def sha1_file(path: Path) -> str:
    """SHA1 of file contents."""
    h = hashlib.sha1()
    try:
        h.update(path.read_bytes())
    except Exception:
        pass
    return h.hexdigest()


def sha1_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="replace")).hexdigest()


def iter_python(paths: list[Path]) -> Generator[tuple[Path, str, ast.AST | None, str | None], None, None]:
    """Yields (path, text, ast_tree|None, parse_error|None)."""
    for p in paths:
        if p.suffix != ".py":
            continue
        text, truncated = read_text(p)
        err = None
        tree = None
        try:
            tree = ast.parse(text, filename=str(p))
        except SyntaxError as e:
            err = str(e)
        yield p, text, tree, err


def ast_imports(tree: ast.AST) -> list[tuple[str, str, int, str]]:
    """List of (module, name, lineno, kind)."""
    imports: list[tuple[str, str, int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((alias.name, alias.asname or alias.name, node.lineno, "import"))
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for alias in node.names:
                imports.append((mod, alias.asname or alias.name, node.lineno, "from"))
    return imports


def ast_calls(tree: ast.AST, names: set[str]) -> list[tuple[str, int]]:
    """Call-site extraction with line numbers."""
    calls: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                if func.id in names:
                    calls.append((func.id, node.lineno))
            elif isinstance(func, ast.Attribute):
                if func.attr in names:
                    calls.append((func.attr, node.lineno))
    return calls


def module_of(path: Path, root: Path) -> str:
    """Canonical dotted module name."""
    try:
        rel = path.relative_to(root)
        parts = list(rel.parts)
        if parts[-1] == "__init__.py":
            parts.pop()
        elif parts[-1].endswith(".py"):
            parts[-1] = parts[-1][:-3]
        return ".".join(parts)
    except ValueError:
        return path.stem


def is_async_function(node: ast.AST) -> bool:
    return isinstance(node, ast.AsyncFunctionDef)


def async_functions(tree: ast.AST) -> list[ast.AsyncFunctionDef]:
    return [n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef)]


def iter_functions(tree: ast.AST) -> Generator[tuple[str, ast.FunctionDef, int, int, int], None, None]:
    """(qualname, node, start, end, depth)."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            depth = 0
            parent = node
            while hasattr(parent, "parent"):
                parent = getattr(parent, "parent", parent)  # type: ignore
            yield node.name, node, node.lineno, node.end_lineno or node.lineno, depth


def complexity_of(node: ast.AST) -> int:
    """Branch count approximation."""
    branches = 0
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.With, ast.Assert)):
            branches += 1
    return branches


def normalized_hash(node: ast.AST) -> str:
    """AST-normalised body hash for DRY detection."""
    try:
        return hashlib.sha1(ast.dump(node, annotate_fields=False).encode()).hexdigest()[:16]
    except Exception:
        return ""


def grep_files(paths: list[Path], pattern: str, flags: int = 0) -> list[tuple[Path, int, str]]:
    """Regex scan with line numbers, bounded results."""
    results: list[tuple[Path, int, str]] = []
    for p in paths:
        text, _ = read_text(p)
        try:
            matches = re.finditer(pattern, text, flags)
            for m in matches:
                line = text[:m.start()].count("\n") + 1
                results.append((p, line, m.group(0)))
        except re.error:
            continue
    return results


def find_endpoints(paths: list[Path]) -> list[tuple[Path, str, str, int]]:
    """FastAPI decorator extraction."""
    endpoints: list[tuple[Path, str, str, int]] = []
    for p in paths:
        text, _ = read_text(p)
        for m in re.finditer(r'@(?:router|app)\.(get|post|put|delete|patch|options|head|websocket)\s*\(\s*["\']([^"\']+)["\']', text):
            line = text[:m.start()].count("\n") + 1
            endpoints.append((p, m.group(1).upper(), m.group(2), line))
    return endpoints


def feature_gate_literals(paths: list[Path]) -> dict[str, int]:
    r"""`require_feature("...")` string constants, extracted from the AST.

    Two regexes used to answer this question and they disagreed:
    `s12_features` used `[^"']+`, which spans newlines, so a docstring or test
    that merely *mentions* `require_feature()` produced a garbage "literal"
    (the captured text began with `)` and ran into the next quoted string);
    `measurements.m_dead_feature_gate` used `[^"'\s]+` and never matched it.
    The detector therefore reported a ghost atom the measurement could not see,
    and the verifier resolved the disagreement by *deleting* the aggregated
    finding. A regex cannot distinguish code from prose; the AST can.

    Only a `Call` whose function is named `require_feature` (or an attribute
    ending in `.require_feature`) with a string-literal first argument counts.
    Comments, docstrings, and assertions that merely name the helper are
    invisible here, which is the point.
    """
    found: dict[str, int] = {}
    for path in paths:
        tree = parse_python(path).tree
        if tree is None:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
            if name != "require_feature" or not node.args:
                continue
            arg = node.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and arg.value:
                found[arg.value] = found.get(arg.value, 0) + 1
    return found


def parse_requirements(path: Path) -> dict[str, str]:
    """PEP-508 tolerant requirement parser -> ``{package_name: pinned_version}``.

    Extras are stripped (``uvicorn[standard]`` -> ``uvicorn``). A requirement
    with no version (``starlette``) maps to ``""`` so callers can distinguish
    "declared, unpinned" from "not declared". The first entry for a name wins.
    """
    deps: dict[str, str] = {}
    try:
        text = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return deps
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        m = re.match(r"^([A-Za-z0-9_.-]+)(?:\[[^\]]*\])?\s*([=<>!~]=?|[<>])\s*([^\s,;]+)", line)
        if m:
            deps.setdefault(m.group(1), m.group(3).strip())
            continue
        m2 = re.match(r"^([A-Za-z0-9_.-]+)(?:\[[^\]]*\])?", line)
        if m2:
            deps.setdefault(m2.group(1), "")
    return deps


def parse_package_json(path: Path) -> dict[str, Any]:
    """Tolerant JSON/JSONC read."""
    try:
        import json
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        # Strip comments (JSONC)
        text = re.sub(r'//.*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        return json.loads(text)
    except Exception:
        return {}


def parse_yaml_lite(path: Path) -> dict[str, Any]:
    """Minimal YAML subset parser (workflows/docker-compose) — no PyYAML dependency."""
    result: dict[str, Any] = {}
    try:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        current_list: list[str] = []
        current_key = ""
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if ":" in stripped:
                key, _, val = stripped.partition(":")
                key = key.strip()
                val = val.strip()
                if val:
                    result[key] = val
                else:
                    current_key = key
                    current_list = []
                    result[key] = current_list
            elif stripped.startswith("- ") and current_key:
                current_list.append(stripped[2:].strip())
    except Exception:
        pass
    return result


def parse_markdown_tables(text: str) -> list[list[list[str]]]:
    """Extract markdown tables as ``[table][row][cell]``.

    Separator rows (``|---|---|``) are dropped. Every consumer indexes cells
    (``row[0]``, ``for cell in row``), so rows must stay cell lists.
    """
    tables: list[list[list[str]]] = []
    current: list[list[str]] = []
    for line in (text or "").splitlines():
        if "|" in line:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not cells or all(set(c) <= set("-: ") and c for c in cells):
                continue
            current.append(cells)
        elif current:
            tables.append(current)
            current = []
    if current:
        tables.append(current)
    return tables


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * (p / 100.0)
    f = int(k)
    c = f + 1 if f + 1 < len(s) else f
    d = k - f
    return s[f] + d * (s[c] - s[f])


def fmt_seconds(s: float) -> str:
    if s < 60:
        return f"{s:.1f}s"
    if s < 3600:
        return f"{s/60:.1f}m"
    return f"{s/3600:.1f}h"


def truncate(text: str, limit: int) -> str:
    """Clamp captured output to ``limit`` chars, keeping BOTH ends.

    Tool summaries ("3 failed, 780 passed", the final traceback line) live at
    the end of the stream, so a head-only clip silently destroys the evidence
    the audit needs to classify a run.
    """
    text = text or ""
    if len(text) <= limit:
        return text
    head = limit // 2
    tail = limit - head
    return (text[:head]
            + f"\n... [{len(text) - limit} chars elided] ...\n"
            + text[-tail:])


def fmt_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


# --------------------------------------------------------------------------- #
# Walking / parsing helpers used by the scanners
# --------------------------------------------------------------------------- #

#: Top-level trees the audit must never descend into (audit output, vendored,
#: build artefacts). ``.kilo`` is an Agent Manager worktree, not project code.
#:
#: ``_audit`` and ``_browser_test`` are the *harness* trees. They are not project
#: code, and leaving them in scope meant 614 files of audit output and Playwright
#: specs were scanned as if they were the product: 3 findings this run, 2 of them
#: P0, all of them artefacts of the previous audit rather than defects in ZOZI.
EXCLUDED_DIRS: set[str] = {
    ".git", ".kilo", ".freebuff", "node_modules", "__pycache__", ".pytest_cache",
    ".hypothesis", ".next", "dist", "build", "venv", ".venv", "_extra_files",
    "_legacy.bak", "test-results", "playwright-report", "logs", "var",
    "_zozi_audit", "_audit", "_browser_test", "egg-info", ".turbo", ".cache",
    # pytest's per-run temp trees. They are written *inside* the repo, contain
    # deliberately-broken fixture files (`test_unparseable_file_is_repor0/
    # kernel/broken.py`), and grew to four copies during this work. Scanned as
    # project code they produced 4 bogus "invalid syntax" parse failures.
    # Matched by exact name, so this must be the literal directory name.
    "pytest-of-user",
}

AUDITED_SUFFIXES: set[str] = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".json", ".jsonc",
    ".yaml", ".yml", ".toml", ".md", ".ini", ".cfg", ".txt", ".csv", ".sql",
    ".env", ".example", ".sh", ".ps1", ".lock", ".prisma",
}


def walk_all(root: Path, exclude: set[str] | None = None) -> list[Path]:
    """Every auditable file under ``root``, sorted, exclusions applied."""
    root = Path(root)
    skip = EXCLUDED_DIRS | (exclude or set())
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        keep = []
        for d in sorted(dirnames):
            if d in skip or d.startswith(".") or d.endswith(".egg-info"):
                continue
            keep.append(d)
        dirnames[:] = keep
        for fname in sorted(filenames):
            fpath = Path(dirpath) / fname
            if fname.endswith((".min.js", ".map")) or is_generated(fpath):
                continue
            name = fname.lower()
            suffix = fpath.suffix.lower()
            if suffix in AUDITED_SUFFIXES or name in (
                    ".env", ".env.example", ".nvmrc", ".dockerignore", ".editorconfig"):
                out.append(fpath)
    return out


def iter_files(root: Path, suffixes: tuple[str, ...] = (".py",),
               exclude: set[str] | None = None) -> Generator[Path, None, None]:
    """Yield files under ``root`` whose suffix is in ``suffixes``."""
    root = Path(root)
    if not root.exists():
        return
    skip = EXCLUDED_DIRS | (exclude or set())
    wanted = {s.lower() for s in suffixes}
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        keep = []
        for d in sorted(dirnames):
            if d in skip or d.startswith("."):
                continue
            keep.append(d)
        dirnames[:] = keep
        for fname in sorted(filenames):
            fpath = Path(dirpath) / fname
            if fpath.suffix.lower() in wanted and not is_generated(fpath):
                yield fpath


@dataclass(slots=True)
class ParsedPython:
    """Result of :func:`parse_python` — always returned, never raises."""

    path: str = ""
    text: str = ""
    tree: Optional[ast.AST] = None
    error: str = ""


_PY_CACHE: dict[tuple[str, int, int], ParsedPython] = {}


def parse_python(path: Path) -> ParsedPython:
    """Parse a Python file once and memoise it (single AST snapshot per file).

    A syntax error is reported as ``error`` — never as a finding about the
    file's content, and never as a raised exception.
    """
    p = Path(path)
    try:
        stat = p.stat()
        key = (str(p), int(stat.st_mtime), int(stat.st_size))
    except OSError:
        return ParsedPython(path=str(p), error="unreadable")
    hit = _PY_CACHE.get(key)
    if hit is not None:
        return hit
    text, _ = read_text(p)
    if not text.strip():
        # An empty file parses to an empty module and is perfectly legal -- most
        # `__init__.py` in this repo are empty. Reporting it as
        # "empty-or-unreadable" made 92 healthy files look broken to every
        # scanner that skips on `error`, so their contents went unexamined.
        result = ParsedPython(path=str(p), text=text, tree=ast.parse(""))
    else:
        try:
            result = ParsedPython(path=str(p), text=text, tree=ast.parse(text))
        except SyntaxError as exc:
            result = ParsedPython(path=str(p), text=text,
                                  error=f"SyntaxError line {exc.lineno}: {exc.msg}")
        except Exception as exc:  # pragma: no cover - defensive
            result = ParsedPython(path=str(p), text=text, error=f"{type(exc).__name__}: {exc}")
    _PY_CACHE[key] = result
    return result


_NESTING_NODES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With,
                  ast.AsyncWith, ast.Try, ast.ExceptHandler, ast.Match)


def max_nesting(node: ast.AST, _depth: int = 0) -> int:
    """Maximum control-flow nesting depth inside ``node``."""
    best = _depth
    for child in ast.iter_child_nodes(node):
        step = _depth + 1 if isinstance(child, _NESTING_NODES) else _depth
        best = max(best, max_nesting(child, step))
    return best


def md_escape(value: object) -> str:
    """Escape a value for a markdown table cell."""
    text = "" if value is None else str(value)
    return (text.replace("\\", "\\\\")
                .replace("|", "\\|")
                .replace("\r\n", " ")
                .replace("\n", " ")
                .replace("\r", " "))


class SimpleYaml:
    """Tiny YAML-subset reader (no PyYAML dependency).

    Handles the shapes this repository actually uses in workflows and compose
    files: scalars, nested maps by indentation, and ``- item`` lists.
    """

    def __init__(self, text: str = ""):
        self.text = text or ""
        self.data: dict[str, Any] = {}
        if self.text:
            self.data = self._parse(self.text)

    @classmethod
    def from_path(cls, path: Path) -> "SimpleYaml":
        text, _ = read_text(Path(path))
        return cls(text)

    @classmethod
    def load(cls, path: Path) -> "SimpleYaml":
        return cls.from_path(path)

    @staticmethod
    def _scalar(raw: str) -> Any:
        v = raw.strip().strip("'\"")
        if v.lower() in ("true", "yes"):
            return True
        if v.lower() in ("false", "no"):
            return False
        if v.lower() in ("null", "~", ""):
            return None
        if re.fullmatch(r"-?\d+", v):
            return int(v)
        if re.fullmatch(r"-?\d+\.\d+", v):
            return float(v)
        return v

    def _parse(self, text: str) -> dict[str, Any]:
        root: dict[str, Any] = {}
        stack: list[tuple[int, Any]] = [(-1, root)]
        for raw in text.splitlines():
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            indent = len(raw) - len(raw.lstrip(" "))
            line = raw.strip()
            while stack and indent <= stack[-1][0]:
                stack.pop()
            if not stack:
                stack = [(-1, root)]
            parent = stack[-1][1]
            if line.startswith("- "):
                item = self._scalar(line[2:])
                if isinstance(parent, list):
                    parent.append(item)
                continue
            key, _, val = line.partition(":")
            key = key.strip()
            if not key:
                continue
            if val.strip():
                if isinstance(parent, dict):
                    parent[key] = self._scalar(val)
            else:
                child: Any = {}
                if isinstance(parent, dict):
                    parent[key] = child
                stack.append((indent, child))
        return root

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __contains__(self, key: str) -> bool:
        return key in self.data

    def __iter__(self):
        return iter(self.data)

    def items(self):
        return self.data.items()

    def keys(self):
        return self.data.keys()

    def values(self):
        return self.data.values()
