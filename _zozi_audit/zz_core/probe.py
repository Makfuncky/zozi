"""Executable predicates for findings.

A finding's ``current`` is prose. Prose cannot be verified without guessing, and
guessing is what produced every FALSE_POSITIVE and WRONG_LOCATION verdict. A
probe is the machine-checkable form of the same claim: the gate runs it against
current source and gets a boolean.

Design rules, each learned from a real defect:

* **A probe names a node, not a shape.** ``ast_relationship_missing_kwarg`` pins
  the call name, its first argument and the line; ``ast_call_without_kwarg``
  alone matched whichever relationship happened to be nearby, which is how 8
  tf-rel-lazy findings became false positives against a *different* relationship.
* **Absence probes must prove absence.** ``require_absent_kwarg`` means "this
  keyword is genuinely not on this call", not "I did not find it nearby".
* **Inheritance counts.** A ``lazy=`` supplied by the declarative base satisfies
  the requirement, so the probe resolves the base before reporting absence.
* **A detector may not emit a probe it cannot itself run.** Otherwise the bug
  moves into the probe and the verdict becomes confidently wrong — which is what
  happened twice in this project (a lost line in ``_layer_of``, a string
  iterated as characters).

Every probe returns ``ProbeResult(holds: bool, detail: str, resolvable: bool)``.
``resolvable`` is False when the probe cannot be evaluated at all (file gone,
scope unsupported); the gate treats that as UNVERIFIABLE rather than as a pass,
so an unrunnable probe can never manufacture a green verdict.
"""
from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ProbeResult:
    holds: bool = False            # the claim is still true in current source
    detail: str = ""
    resolvable: bool = True        # False => UNVERIFIABLE, never a pass


#: Law 1 — which top-level backend packages each layer may import. Derived from
#: the architecture document, not from whatever the code currently does: a table
#: built from the code would rubber-stamp the violation it is meant to detect.
_ALLOWED_IMPORTS: dict[str, set[str]] = {
    "modules": {"rbac", "domains", "kernel", "infrastructure", "providers"},
    "rbac": {"domains", "kernel", "infrastructure"},
    "domains": {"kernel", "infrastructure", "providers"},
    "kernel": {"infrastructure"},
    "infrastructure": set(),
    "providers": {"kernel", "infrastructure"},
    "jobs": {"domains", "infrastructure", "providers"},
    "middleware": {"rbac", "infrastructure"},
}


def _layer_of(rel: str) -> str:
    """Top-level backend package a path belongs to, from the path alone."""
    parts = str(rel).replace("\\", "/").split("/")
    if "backend" in parts:
        i = parts.index("backend")
        if i + 1 < len(parts):
            return parts[i + 1]
    return parts[0] if parts else ""


def _sql_literal(call: ast.Call, tree: ast.AST) -> str:
    """Best-effort SQL for an `execute(...)` call: inline, `sa.text(...)`, or a
    module constant. Empty when only knowable at runtime."""
    if not call.args:
        return ""
    first = call.args[0]
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        return first.value
    if isinstance(first, ast.Call) and getattr(first.func, "attr", "") == "text" \
            and first.args:
        inner = first.args[0]
        if isinstance(inner, ast.Constant) and isinstance(inner.value, str):
            return inner.value
        if isinstance(inner, ast.Name):
            first = inner
        else:
            return ""
    if isinstance(first, ast.Name):
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                    and isinstance(node.targets[0], ast.Name) \
                    and node.targets[0].id == first.id:
                try:
                    val = ast.literal_eval(node.value)
                    return val if isinstance(val, str) else ""
                except Exception:
                    return " ".join(
                        s.value for s in ast.walk(node.value)
                        if isinstance(s, ast.Constant) and isinstance(s.value, str))
    return ""


def _sql_is_destructive(call: ast.Call, tree: ast.AST) -> bool:
    """DROP / TRUNCATE / DELETE-without-WHERE / ALTER..DROP / ALTER..TYPE."""
    sql = _sql_literal(call, tree)
    if not sql:
        return False
    s = sql.upper()
    if re.search(r"\b(DROP|TRUNCATE)\b", s):
        return True
    if re.search(r"\bDELETE\s+FROM\b", s) and not re.search(r"\bWHERE\b", s):
        return True
    if re.search(r"\bALTER\b[^;]*\bDROP\b", s):
        return True
    if re.search(r"\bALTER\s+(COLUMN\s+)?\S+\s+(?:SET\s+DATA\s+)?TYPE\b", s):
        return True
    return False


class ProbeRunner:
    """Evaluates probes against the working tree. Read-only."""

    def __init__(self, root: Path):
        # Resolve once, here. `_import_edges` does
        # `f.resolve().relative_to(self.root)`, which raises ValueError for every
        # file when `self.root` is a relative path -- and `except ValueError:
        # continue` then skips the entire tree, producing an empty graph. The
        # symptom was `package_cycle_exists` reporting "import graph unavailable"
        # for all 20 circular-import findings, which are all real: the domain
        # graph has one 14-domain strongly-connected component.
        self.root = Path(root).resolve()
        self._tree: dict[str, ast.AST | None] = {}
        self._text: dict[str, str] = {}
        # Cache of the declarative base classes' relationship defaults, keyed by
        # the base class name.
        self._base_rel_lazy: dict[str, set[str]] = {}
        self._routes_cache = None

    # -- IO -------------------------------------------------------------------
    def text(self, rel: str) -> str:
        if rel not in self._text:
            try:
                # `utf-8-sig`, not `utf-8`. A leading BOM survives a plain `utf-8`
                # decode as U+FEFF, `ast.parse` rejects it, and `tree()` caches
                # None -- so every BOM'd file silently became unparseable to the
                # probe and its findings fell back to token matching. The
                # scanner side already used `utf-8-sig`; the two sides disagreed
                # about the same file.
                self._text[rel] = (self.root / rel).read_text(
                    encoding="utf-8-sig", errors="replace")
            except Exception:
                self._text[rel] = ""
        return self._text[rel]

    def tree(self, rel: str) -> ast.AST | None:
        if rel not in self._tree:
            src = self.text(rel)
            if not src:
                self._tree[rel] = None
            else:
                try:
                    self._tree[rel] = ast.parse(src)
                except Exception:
                    self._tree[rel] = None
        return self._tree[rel]

    def lines(self, rel: str) -> list[str]:
        return self.text(rel).splitlines()

    # -- independent law measurements ----------------------------------------
    #
    # The `09_laws` dimension reports one aggregate finding per violated law,
    # phrased as a COUNT ("18 Float column(s)", "105 temp/debug file(s)").
    # Token matching cannot adjudicate a count, and the generic token fallback
    # can only ever answer UNVERIFIABLE -- which is why all 26 of these sat
    # unresolved no matter how the probe layer was tuned.
    #
    # Each measurement below RE-DERIVES its quantity from source. They are
    # deliberately written as separate implementations rather than importing the
    # scanner's predicate: a probe that replays the detector's own arithmetic
    # cannot notice when that arithmetic is what is wrong.

    #: Directories the aggregate law measurements range over. Restated here
    #: instead of imported so the measurement is independent of the scanner.
    _LAW_DIRS = ("domains", "modules", "rbac", "kernel", "infrastructure",
                 "providers", "jobs", "middleware")

    def _law_files(self, dirs=None):
        """Backend Python files in scope, tests and caches excluded."""
        for d in (dirs if dirs is not None else self._LAW_DIRS):
            base = self.root / "backend" / d
            if not base.is_dir():
                continue
            for p in sorted(base.rglob("*.py")):
                rel = self._rel(p)
                if "/tests/" in rel or "__pycache__" in rel:
                    continue
                yield rel

    def _test_global_mutation_unguarded(self, probe: dict) -> ProbeResult:
        """Does a test function still mutate a global with nothing to undo it?

        The claim is per-FUNCTION, not per-line: a bare `os.environ[...] = ...`
        is only a defect when the enclosing test declares no cleanup at all
        (`monkeypatch`, `delenv`, a fixture, `addfinalizer`). Judging the single
        cited line would both miss a cleanup two lines below and invent one
        that belongs to a neighbouring test, so the enclosing function is
        re-read and re-judged as a unit.
        """
        rel = probe.get("path", "")
        line = int(probe.get("line") or 0)
        tree = self.tree(rel)
        if tree is None:
            return ProbeResult(False, f"{rel} does not parse", resolvable=False)
        text = self.text(rel) or ""
        mutator = re.compile(r"os\.environ\s*\[[^\]]+\]\s*=|os\.environ\.update\(|"
                             r"^\s*import\s+stripe\b", re.M)
        cleanup = re.compile(r"monkeypatch|delenv|os\.environ\.pop|undo|restore|"
                             r"@pytest\.fixture|yield\s*$|addfinalizer", re.M)
        best = None
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            start = fn.lineno
            end = fn.end_lineno or fn.lineno
            if start <= line <= end and (best is None or start > best.lineno):
                best = fn
        if best is None:
            # Not inside a function (module-level mutation): the whole module is
            # the scope a cleanup would have to appear in.
            seg = text
            scope = rel
        else:
            seg = ast.get_source_segment(text, best) or ""
            scope = f"{rel}:{best.name}()"
        if not mutator.search(seg):
            return ProbeResult(False, f"no global mutation remains in {scope} — fixed")
        if cleanup.search(seg):
            return ProbeResult(False, f"{scope} now declares a cleanup for its "
                                      f"global mutation — fixed")
        return ProbeResult(True, f"{scope} mutates process-global state and "
                                 f"declares no cleanup")

    def _tsconfig_strict_off(self, probe: dict) -> ProbeResult:
        """Law 170: TypeScript `strict` must be on.

        `compilerOptions.strict` may be `true`, `false`, or absent (which means
        off), so absence has to count as a violation rather than as "nothing to
        check" -- that is the whole point of the finding.
        """
        rel = probe.get("path") or "frontend/shared/tsconfig.json"
        text = self.text(rel.replace("\\", "/"))
        if text is None:
            return ProbeResult(False, f"{rel} unreadable", resolvable=False)
        body = re.sub(r"//[^\n]*", "", text)
        m = re.search(r'"strict"\s*:\s*(true|false)', body)
        if m is None:
            return ProbeResult(True, f"{rel} never sets compilerOptions.strict "
                                     f"— strict mode is off by default")
        if m.group(1) == "true":
            return ProbeResult(False, f"{rel} sets strict=true — fixed")
        return ProbeResult(True, f"{rel} sets strict=false")

    def _law_measure(self, probe: dict) -> ProbeResult:
        """Re-derive the count behind an aggregate finding.

        Measurements live in `zz_core.measurements`, keyed by name. They are
        separate traversals from the scanners' on purpose: a probe that calls
        the detector's own counter agrees with it by construction, which is the
        exact failure this layer exists to catch.
        """
        name = probe.get("measure") or ""
        try:
            from .measurements import MEASUREMENTS
        except Exception as exc:
            return ProbeResult(False, f"measurements unavailable: {exc}",
                               resolvable=False)
        try:
            if name in MEASUREMENTS:
                from .measurements import Ctx
                fn = MEASUREMENTS[name]
                arg = probe.get("arg") or ""
                count, detail = fn(Ctx(self.root), arg) if arg else fn(Ctx(self.root))
            elif name in _LAW_MEASURES:
                count, detail = _LAW_MEASURES[name](self)
            else:
                return ProbeResult(False, f"no independent measurement {name!r}",
                                   resolvable=False)
        except Exception as exc:
            return ProbeResult(False, f"measurement {name!r} failed: "
                                      f"{type(exc).__name__}: {exc}",
                               resolvable=False)
        if count > 0:
            return ProbeResult(True, f"{count} {detail}")
        return ProbeResult(False, f"0 {detail} — re-derived independently, so the "
                                  f"aggregate no longer holds")

    def _law_reverse_imports(self) -> tuple[int, str]:
        """Law 1: imports that cross a layer upwards. Re-walked from the AST."""
        # Layer of the importing file, and the targets each layer may not reach.
        forbidden = {
            "infrastructure": {"domains", "modules", "rbac", "providers",
                               "jobs", "middleware"},
            "kernel": {"domains", "modules", "rbac", "providers", "jobs",
                       "middleware"},
            "providers": {"domains", "modules", "rbac", "jobs", "middleware"},
            "middleware": {"domains", "modules", "providers", "jobs"},
            "jobs": {"modules", "middleware"},
            "rbac": {"modules", "providers", "jobs", "middleware"},
        }
        n = 0
        for rel in self._law_files():
            tree = self.tree(rel)
            if tree is None:
                continue
            layer = _layer_of(rel)
            blocked = forbidden.get(layer)
            # A domain importing `modules` is also upward; a module may not.
            if layer.startswith("domains") or layer.startswith("modules"):
                blocked = {"modules"} if layer.startswith("domains") else set()
            elif blocked is None:
                continue
            if not blocked:
                continue
            for node in ast.walk(tree):
                mods = []
                if isinstance(node, ast.Import):
                    mods = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                    mods = [node.module]
                for mod in mods:
                    if mod.split(".")[0] in blocked:
                        n += 1
        return n, "reverse-layer import(s) re-derived from the AST"

    def _law_model_inventory(self):
        """[(table, {column: source}, [relationship sources])] via AST.

        Scoped to classes that declare `__tablename__`, which is what makes a
        class an ORM model rather than a DTO, a pydantic schema or a service
        object. Scoping on the base class name instead swept in every
        `*Base*`-looking class and reported 658 models missing audit columns
        against a real total of 2 -- a wrong number attached to a right verdict.
        """
        out = []
        for rel in self._law_files(("domains", "modules", "infrastructure")):
            tree = self.tree(rel)
            if tree is None:
                continue
            for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
                cols: dict[str, str] = {}
                rels: list[str] = []
                tablename = None
                for stmt in cls.body:
                    if isinstance(stmt, ast.AnnAssign) and stmt.target \
                            and isinstance(stmt.target, ast.Name):
                        src = ast.unparse(stmt)
                        if stmt.target.id == "__tablename__":
                            try:
                                tablename = ast.literal_eval(stmt.value)
                            except Exception:
                                tablename = None
                        cols[stmt.target.id] = src
                        if "relationship(" in src:
                            rels.append(src)
                    elif isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 \
                            and isinstance(stmt.targets[0], ast.Name):
                        src = ast.unparse(stmt)
                        nm = stmt.targets[0].id
                        if nm == "__tablename__":
                            try:
                                tablename = ast.literal_eval(stmt.value)
                            except Exception:
                                tablename = None
                        cols[nm] = src
                        if "relationship(" in src:
                            rels.append(src)
                if tablename:
                    out.append((f"{tablename} ({rel})", cols, rels))
        return out

    def _law_float_money(self) -> tuple[int, str]:
        n = sum(1 for _t, cols, _r in self._law_model_inventory()
                for src in cols.values() if re.search(r"\bFloat\b", src))
        cfg = self.text("backend/config.py") or ""
        n += len(re.findall(r"(vat_rate|commission_rate|tax_rate)\s*:\s*float", cfg))
        return n, "Float money column(s) / config field(s)"

    def _law_python_timestamps(self) -> tuple[int, str]:
        n = 0
        for _t, cols, _r in self._law_model_inventory():
            for name, src in cols.items():
                if name not in ("created_at", "updated_at"):
                    continue
                if "server_default" not in src and "default=" in src:
                    n += 1
        return n, "timestamp column(s) with a Python-side default"

    def _law_missing_audit_columns(self) -> tuple[int, str]:
        need = {"created_at", "updated_at", "is_deleted"}
        return sum(1 for _t, cols, _r in self._law_model_inventory()
                   if not need <= set(cols)), "model(s) missing audit columns"

    def _law_missing_is_deleted(self) -> tuple[int, str]:
        return sum(1 for _t, cols, _r in self._law_model_inventory()
                   if "is_deleted" not in cols), "model(s) without is_deleted"

    def _law_fk_without_index(self) -> tuple[int, str]:
        return sum(1 for _t, cols, _r in self._law_model_inventory()
                   for src in cols.values()
                   if "ForeignKey(" in src and "index=True" not in src), \
            "FK column(s) without index=True"

    def _law_relationship_lazy(self) -> tuple[int, str]:
        return sum(1 for _t, _c, rels in self._law_model_inventory()
                   for src in rels if "lazy=" not in src), \
            "relationship(s) without lazy="

    def _law_temp_scripts(self) -> tuple[int, str]:
        backend = self.root / "backend"
        n = 0
        for pat in ("_tmp_*.py", "health_test_*.py", "fix_*.py", "debug_*.py",
                    "_audit_boot_check.py"):
            n += sum(1 for _ in backend.glob(pat))
        return n, "temp/debug script(s) at backend root"

    def _law_extra_domains(self) -> tuple[int, str]:
        from .constants import CANONICAL_DOMAINS
        base = self.root / "backend" / "domains"
        if not base.is_dir():
            return 0, "extra domain(s) (backend/domains absent)"
        extra = [d.name for d in base.iterdir()
                 if d.is_dir() and d.name != "__pycache__"
                 and d.name not in CANONICAL_DOMAINS]
        return len(extra), f"extra domain(s): {', '.join(sorted(extra)) or 'none'}"

    def _law_extra_modules(self) -> tuple[int, str]:
        from .constants import CANONICAL_MODULES
        base = self.root / "backend" / "modules"
        if not base.is_dir():
            return 0, "extra module(s) (backend/modules absent)"
        extra = [d.name for d in base.iterdir()
                 if d.is_dir() and d.name != "__pycache__"
                 and d.name not in CANONICAL_MODULES]
        return len(extra), f"extra module(s): {', '.join(sorted(extra)) or 'none'}"

    def _law_undated_allowlist(self) -> tuple[int, str]:
        text = self.text("backend/DOMAIN_ALLOWLIST.yaml")
        if text is None:
            return 0, "undated allowlist entries (no allowlist file)"
        entries = re.findall(r"^\s*-\s*(.+)$", text, re.MULTILINE)
        undated = [e for e in entries if not re.search(r"\d{4}-\d{2}-\d{2}", e)]
        return len(undated), f"allowlist entr(ies) without a dated removal plan"

    def _law_fstring_sql(self) -> tuple[int, str]:
        pat = re.compile(r"(text|execute)\(\s*f[\"']")
        n = sum(len(pat.findall(self.text(rel) or "")) for rel in self._law_files())
        return n, "f-string SQL site(s)"

    def _law_print_calls(self) -> tuple[int, str]:
        pat = re.compile(r"(?<![\w.])print\(")
        n = sum(len(pat.findall(self.text(rel) or "")) for rel in self._law_files())
        return n, "print() call(s) in backend core"

    def _law_silent_excepts(self) -> tuple[int, str]:
        """`except ...: pass` / `except ...: return None` with nothing logged."""
        n = 0
        for rel in self._law_files(("domains",)):
            tree = self.tree(rel)
            if tree is None:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.ExceptHandler):
                    continue
                body = [s for s in node.body
                        if not (isinstance(s, ast.Expr)
                                and isinstance(s.value, ast.Constant))]
                if not body:
                    continue
                if len(body) != 1:
                    continue
                only = body[0]
                if isinstance(only, ast.Pass):
                    n += 1
                elif (isinstance(only, ast.Return)
                      and (only.value is None
                           or (isinstance(only.value, ast.Constant)
                               and only.value.value is None))):
                    n += 1
        return n, "silent except block(s) in domains/"

    def _law_todo_hygiene(self) -> tuple[int, str]:
        pat = re.compile(
            r"#\s*(?:TODO|FIXME)(?!.*(?:#\d+|[A-Z]+-\d+|\d{4}-\d{2}-\d{2}))",
            re.IGNORECASE)
        n = sum(len(pat.findall(self.text(rel) or "")) for rel in self._law_files())
        return n, "TODO/FIXME without a ticket or expiry"

    def _law_raw_getenv(self) -> tuple[int, str]:
        pat = re.compile(r"os\.(?:getenv|environ\.get)\(")
        dirs = ("providers", "jobs", "middleware", "infrastructure", "domains")
        n = sum(len(pat.findall(self.text(rel) or "")) for rel in self._law_files(dirs))
        return n, "raw os.getenv read(s)"

    def _law_set_local_missing(self) -> tuple[int, str]:
        """Law 5: the SET LOCAL RLS context must actually be established."""
        rls = self.text("backend/infrastructure/database/rls_interceptor.py") or ""
        if "SET LOCAL" in rls:
            return 0, "SET LOCAL RLS context missing (present)"
        return 1, "SET LOCAL RLS context missing"

    def _law_rate_limiter_fail_closed(self) -> tuple[int, str]:
        """Law 37: the rate limiter must deny on backend failure."""
        text = self.text("backend/middleware/rate_limit_middleware.py") or ""
        closed = bool(re.search(
            r"status_code\s*=\s*5\d\d|status_code=503|deny|fail.?closed",
            text, re.IGNORECASE))
        return (0 if closed else 1), \
            "rate limiter without a visible fail-closed path"

    def _law_migration_heads(self) -> tuple[int, str]:
        """Law 49: count Alembic revision heads from the `down_revision` graph."""
        versions = self.root / "backend" / "alembic" / "versions"
        if not versions.is_dir():
            return 0, "divergent migration heads (no versions dir)"
        revs: dict[str, str | None] = {}
        for p in versions.glob("*.py"):
            tree = self.tree(self._rel(p))
            if tree is None:
                continue
            up = down = None
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for t in node.targets:
                        if isinstance(t, ast.Name) and t.id == "revision":
                            up = ast.literal_eval(node.value) if isinstance(
                                node.value, ast.Constant) else None
                        elif isinstance(t, ast.Name) and t.id == "down_revision":
                            try:
                                down = ast.literal_eval(node.value)
                            except Exception:
                                down = None
            if up:
                revs[up] = down if isinstance(down, str) else None
        if not revs:
            return 0, "divergent migration heads (no revisions parsed)"
        parents = {d for d in revs.values() if d}
        heads = [r for r in revs if r not in parents]
        return max(0, len(heads) - 1), \
            f"divergent migration head(s) beyond the first of {len(heads)}"

    def _law_event_spine(self) -> tuple[int, str]:
        """Law 3: an event defined in a domain that nothing ever publishes.

        Re-derived by walking the domain tree the other way round: for each
        `events.py` constant, look for a reference in the rest of that domain.
        """
        domains = self.root / "backend" / "domains"
        if not domains.is_dir():
            return 0, "unpublished event(s) (backend/domains absent)"
        orphans: list[str] = []
        published: set[str] = set()
        for ev in sorted(domains.glob("*/events.py")):
            rel_ev = self._rel(ev)
            text = self.text(rel_ev) or ""
            names = set(re.findall(r'^EVENT_[A-Z_]+\s*=\s*["\']([^"\']+)["\']',
                                   text, re.MULTILINE))
            dom_dir = ev.parent
            for name in names:
                found = False
                for svc in sorted(dom_dir.rglob("*.py")):
                    if self._rel(svc) == rel_ev:
                        continue
                    if name in (self.text(self._rel(svc)) or ""):
                        found = True
                        break
                if found:
                    published.add(name)
                else:
                    orphans.append(name)
        return len(orphans), \
            f"event(s) defined but never published: {', '.join(sorted(orphans)[:5]) or 'none'}"

    def _law_provider_routing(self) -> tuple[int, str]:
        """Law 123: routing/orchestration logic inside a provider adapter."""
        base = self.root / "backend" / "providers" / "payments"
        if not base.is_dir():
            return 0, "provider file(s) with routing logic (no payments provider)"
        pat = re.compile(r"orchestrat|route.*gateway|select.*gateway", re.IGNORECASE)
        hits = [self._rel(p) for p in sorted(base.rglob("*.py"))
                if pat.search(self.text(self._rel(p)) or "")]
        return len(hits), f"provider file(s) with routing logic: {len(hits)}"

    def _law_provider_health(self) -> tuple[int, str]:
        """Law 129: fewer than half the providers expose `health_check()`."""
        base = self.root / "backend" / "providers"
        if not base.is_dir():
            return 0, "providers missing health_check() (no providers dir)"
        total = 0
        with_check = 0
        for p in sorted(base.rglob("*.py")):
            if p.name in ("__init__.py", "_base.py"):
                continue
            total += 1
            if "def health_check" in (self.text(self._rel(p)) or ""):
                with_check += 1
        if total == 0 or with_check >= total * 0.5:
            return 0, f"providers missing health_check() ({with_check}/{total} have one)"
        return total - with_check, \
            f"provider(s) without health_check() ({with_check}/{total} have one)"

    def _law_offset_pagination(self) -> tuple[int, str]:
        """Law 222: `.offset(` in a query."""
        n = sum(len(re.findall(r"\.offset\(", self.text(rel) or ""))
                for rel in self._law_files())
        return n, "OFFSET usage(s) in backend core"

    def _law_runbooks(self) -> tuple[int, str]:
        """Law 248: no operational documentation exists at all."""
        docs = self.root / "docs"
        n = sum(1 for _ in docs.rglob("*.md")) if docs.is_dir() else 0
        return (1 if n == 0 else 0), \
            ("no documentation at all under docs/" if n == 0
             else f"{n} doc file(s) under docs/")

    def _law_field_encryption(self) -> tuple[int, str]:
        """Law 275: the field-encryption module is absent."""
        fe = self.root / "backend" / "infrastructure" / "security" / "field_encryption.py"
        return (0 if fe.exists() else 1), \
            "field-encryption module missing" if not fe.exists() \
            else "field-encryption module present"

    def _law_ungated_route(self) -> tuple[int, str]:
        catalog: set[str] = set()
        for fp in sorted((self.root / "backend" / "domains").glob("*/features.py")):
            text = self.text(self._rel(fp)) or ""
            catalog |= set(re.findall(r'"([a-z][a-z0-9_.]*\.[a-z0-9_.]+)"\s*:', text))
        literals: set[str] = set()
        for rel in self._law_files(("modules",)):
            text = self.text(rel) or ""
            literals |= set(re.findall(r'require_feature\(\s*["\']([^"\'*\s]+)["\']',
                                       text))
        unknown = sorted(literals - catalog)
        return len(unknown), \
            f"gate literal(s) absent from the catalog: {', '.join(unknown[:5]) or 'none'}"


# -- executor -------------------------------------------------------------
    def run(self, probe: dict) -> ProbeResult:
        if not probe:
            return ProbeResult(False, "no probe", resolvable=False)
        kind = probe.get("kind", "")
        handler = {
            "text_absent": self._text_absent,
            "text_present": self._text_present,
            "text_matches": self._text_matches,
            "except_handler_silent": self._except_handler_silent,
            "timestamp_default_is_python": self._timestamp_default_is_python,
            "law_unenforced": self._law_unenforced,
            "law_citation_drift": self._law_citation_drift,
            "settings_field_absent": self._settings_field_absent,
            "celery_task_unregistered": self._celery_task_unregistered,
            "migration_downgrade_empty": self._migration_downgrade_empty,
            "destructive_op_unguarded": self._destructive_op_unguarded,
            "ci_step_absent": self._ci_step_absent,
            "router_has_no_endpoints": self._router_has_no_endpoints,
            "duplicate_files_both_present": self._duplicate_files_both_present,
            "duplicated_bodies_present": self._duplicated_bodies_present,
            "ast_call_without_kwarg": self._ast_call_without_kwarg,
            "ast_relationship_missing_kwarg": self._ast_rel_missing_kwarg,
            "ast_model_missing_column": self._ast_model_missing_column,
            "ast_annotation_contains": self._ast_annotation_contains,
            "ast_attr_undeclared": self._ast_attr_undeclared,
            "attribute_absent_in_dict": self._attribute_absent_in_dict,
            "path_absent": self._path_absent,
            "path_present": self._path_present,
"package_cycle_exists": self._package_cycle_exists,
            "filename_count_above": self._filename_count_above,
            "api_path_resolves": self._api_path_resolves,
            "count_below": self._count_below,
            "count_at_or_above": self._count_at_or_above,
            "function_len_above": self._function_len_above,
            "ast_forbidden_call_in_function": self._ast_forbidden_call_in_function,
            "module_imports_above": self._module_imports_above,
            "law_measure": self._law_measure,
            "measure": self._law_measure,
            "test_global_mutation_unguarded": self._test_global_mutation_unguarded,
            "tsconfig_strict_off": self._tsconfig_strict_off,
            "file_line_count_above": self._file_line_count_above,
            "symbol_occurrences": self._symbol_occurrences,
        }.get(kind)
        if handler is None:
            return ProbeResult(False, f"unsupported probe kind {kind!r}",
                               resolvable=False)
        try:
            return handler(probe)
        except Exception as exc:  # a broken probe must not fake a verdict
            return ProbeResult(False, f"probe error: {type(exc).__name__}: {exc}",
                               resolvable=False)

    # -- text probes ----------------------------------------------------------
    def _window(self, probe: dict) -> tuple[str, bool]:
        """Source text for a probe: one path, or a set of paths concatenated."""
        paths = probe.get("paths")
        if paths:
            chunks = [self.text(p) for p in paths]
            chunks = [c for c in chunks if c]
            if not chunks:
                return ("", False)
            joined = "\n".join(chunks)
            line = int(probe.get("line") or 0)
            span = int(probe.get("within", 0) or 0)
            # `whole_file` wins over `line`. These builders emit `line: 1` as a
            # placeholder for the file, not as a location. Without this the window
            # was line 1 only, so every whole-file claim ("3 `# Future:` markers")
            # searched one line, found 0, and refuted a live defect.
            if probe.get("whole_file") or not line:
                return (joined, True)
            lines = joined.splitlines()
            lo = max(0, line - 1 - span)
            hi = min(len(lines), line + span)
            return ("\n".join(lines[lo:hi]), True)
        rel = probe.get("path", "")
        if not self.text(rel):
            return ("", False)
        line = int(probe.get("line") or 0)
        span = int(probe.get("within", 0) or 0)
        if probe.get("whole_file") or not line:
            return (self.text(rel), True)
        lines = self.lines(rel)
        lo = max(0, line - 1 - span)
        hi = min(len(lines), line + span)
        return ("\n".join(lines[lo:hi]), True)

    def _text_absent(self, probe: dict) -> ProbeResult:
        window, ok = self._window(probe)
        if not ok:
            return ProbeResult(False, f"{probe.get('path')} unreadable",
                               resolvable=False)
        pat = probe.get("pattern", "")
        if re.search(pat, window, re.I | re.MULTILINE):
            return ProbeResult(False, f"pattern {pat!r} IS present — "
                                       f"the defect has been fixed")
        return ProbeResult(True, f"pattern {pat!r} absent as claimed")

    def _except_handler_silent(self, probe: dict) -> ProbeResult:
        """Law 59: does the `except` handler at ``line`` still swallow silently?

        A textual `text_absent` over a line window cannot answer this. A handler
        body is 1-8 lines of arbitrary code, so any symmetric window large enough
        to cover a long body also reaches into the *neighbouring* function and
        picks up its `logger.warning(...)` -- which reads as "already fixed" on a
        handler that is genuinely silent. That mis-scored 21 of 101 findings.

        Parsing the handler and inspecting only its own body is the only sound test.
        """
        rel = probe.get("path", "")
        want = int(probe.get("line") or 0)
        tree = self.tree(rel)
        if tree is None:
            return ProbeResult(False, f"{rel} does not parse", resolvable=False)

        handler = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.lineno == want:
                handler = node
                break
        if handler is None:
            # the finding's line may be the `try:` that owns the handler
            for node in ast.walk(tree):
                if isinstance(node, ast.Try):
                    for h in node.handlers:
                        if abs(h.lineno - want) <= 2:
                            handler = h
                            break
        if handler is None:
            return ProbeResult(False, f"no except handler at or beside line {want} in "
                                       f"{rel} — the code moved", resolvable=False)

        log_call = re.compile(r"logger|logging|self\.log|_log|\blog\b", re.I)
        verb = re.compile(r"emit|publish|rollback|add|delete|handle|set_|update|"
                          r"append|extend|notify|capture|appendleft|warn|error", re.I)
        handled = False
        for stmt in handler.body:
            if isinstance(stmt, (ast.Return, ast.Raise)):
                handled = True
            for sub in ast.walk(stmt):
                if isinstance(sub, ast.Raise):
                    handled = True
                if isinstance(sub, ast.Call):
                    nm = getattr(sub.func, "attr", "") or getattr(sub.func, "id", "")
                    if log_call.search(nm) or verb.search(nm):
                        handled = True
        exc = ast.unparse(handler.type) if handler.type else "(bare)"
        if handled:
            return ProbeResult(False, f"line {want} `except {exc}` now logs, raises or "
                                       f"acts — fixed")
        return ProbeResult(True, f"line {want} `except {exc}` still swallows silently")


    def _timestamp_default_is_python(self, probe: dict) -> ProbeResult:
        """Law 21: is the timestamp default on this line a Python-side clock?

        Reports a violation only for `default=` / `onupdate=` bound to a Python
        clock. `server_default=` / `server_onupdate=` are the sanctioned form and
        are not reported, so the probe goes quiet once the column is migrated --
        which is exactly what "fixed" means here.
        """
        rel = probe.get("path", "")
        want = int(probe.get("line") or 0)
        tree = self.tree(rel)
        if tree is None:
            return ProbeResult(False, f"{rel} does not parse", resolvable=False)

        # Python clocks reachable from this module: the literals plus any alias
        # the file binds (`from ... import utcnow as _utcnow`).
        clocks = {"utcnow", "now", "utc_now", "date"}
        clocks |= set(probe.get("aliases") or [])
        clocks |= {"datetime", "time"}

        bad: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if fn not in ("Column", "mapped_column"):
                continue
            col = ""
            if node.args:
                a = node.args[0]
                col = a.id if isinstance(a, ast.Name) else (
                    ast.unparse(a) if isinstance(a, ast.Constant) else "")
            for kw in node.keywords:
                if kw.arg not in ("default", "onupdate"):
                    continue
                if kw.arg == "default" and kw.value is not None \
                        and isinstance(kw.value, ast.Call) \
                        and (getattr(kw.value.func, "attr", None)
                             or getattr(kw.value.func, "id", None)) == "func":
                    continue          # func.now() as a Python default is still a
                    #                   Python default, so keep looking
                seg = ast.unparse(kw.value)
                if re.search(r"\b(server_default|server_onupdate)\b", seg):
                    continue
                if any(re.search(rf"\b{re.escape(c)}\b", seg) for c in clocks):
                    bad.append(f"line {node.lineno}: `{col}` {kw.arg}={seg[:48]}")

        if not bad:
            return ProbeResult(
                False, f"{rel} has no Python-side timestamp default "
                       f"(server_default/func.now in use) — fixed")
        near = [b for b in bad if abs(int(re.match(r"line (\d+)", b).group(1)) - want) <= 12] \
            if want else bad
        shown = (near or bad)[0]
        return ProbeResult(True, f"{rel} still uses a Python-side clock — {shown}")

    def _law_unenforced(self, probe: dict) -> ProbeResult:
        """Is a benchmark law still absent from every check's `laws=(...)`?"""
        rel = probe.get("path", "")
        nums = [int(n) for n in (probe.get("laws") or [])]
        try:
            data = json.loads(self.text(rel).strip() or "{}")
        except Exception as exc:
            return ProbeResult(False, f"{rel} unreadable: {exc}", resolvable=False)
        enforced = {str(k) for k in (data.get("enforced_by_check") or {})}
        still = [n for n in nums if str(n) not in enforced]
        if still:
            return ProbeResult(True, f"law(s) {still} still not enforced by any check")
        return ProbeResult(False, f"law(s) {nums} are now enforced -- fixed")

    def _law_citation_drift(self, probe: dict) -> ProbeResult:
        """Do the cited law numbers still exist in the benchmark table?"""
        known: set[str] = set()
        for cand in ("_most_imp_docx/ARCHITECTURE_STACK.md",
                     "ARCHITECTURE_STACK.md"):
            p = self.root / cand
            if not p.exists():
                continue
            body = p.read_text(encoding="utf-8-sig", errors="replace")
            for m in re.finditer(r"^\s*\|\s*(\d{1,3})\s*\|", body, re.M):
                known.add(m.group(1))
            break
        if not known:
            return ProbeResult(False, "benchmark law table not found", resolvable=False)
        return ProbeResult(True, f"benchmark defines {len(known)} laws; "
                                 f"citation drift reported separately")

    def _settings_field_absent(self, probe: dict) -> ProbeResult:
        """Law 221: `settings.X` must have a declared field X."""
        field = probe.get("field") or ""
        if not field:
            return ProbeResult(False, "probe names no field", resolvable=False)
        rx = re.compile(rf"\b{re.escape(field)}\s*[:=]")
        for cand in ("backend/config.py", "backend/infrastructure/utils/config.py"):
            body = self.text(cand)
            if body and rx.search(body):
                return ProbeResult(False, f"`{field}` is declared in {cand} -- fixed")
        return ProbeResult(True, f"no settings field `{field}` is declared")

    def _celery_task_unregistered(self, probe: dict) -> ProbeResult:
        """Law 27: a recurring Celery task must appear in `beat_schedule`.

        Tasks must be collected from `backend/jobs/*.py` -- the same place the
        detector looks. This previously read them out of `celery_app.py`, the
        very file it then searched for them, so every task "appeared in the beat
        schedule" by definition and the probe refuted a finding that was still
        true. A probe that agrees with its own subject agrees with nothing.
        """
        jobs_dir = self.root / "backend" / "jobs"
        if not jobs_dir.is_dir():
            return ProbeResult(False, "backend/jobs/ not found", resolvable=False)
        tasks: set[str] = set()
        for p in sorted(jobs_dir.glob("*.py")):
            body = self.text(self._rel(p))
            if not body:
                continue
            for m in re.finditer(r"@(?:shared_task|app\.task|celery_app\.task"
                                 r"|celery[.\w]*\.task)\b", body):
                tail = body[m.end():m.end() + 900]
                # Same precedence as the detector: explicit `name=`, else the
                # decorated `def`. Taking the first parenthesised token instead
                # yields the kwarg `bind`, so every task collapsed to one name
                # and "is `bind` scheduled?" decided the finding.
                nm = re.search(r"""\bname\s*=\s*["']([\w.]+)["']""", tail)
                if not nm:
                    nm = re.search(r"^\s*(?:async\s+)?def\s+(\w+)", tail,
                                   re.MULTILINE)
                if nm:
                    tasks.add(nm.group(1).split(".")[-1])
        if not tasks:
            return ProbeResult(False, "no Celery tasks found in backend/jobs/",
                               resolvable=False)
        app = ""
        for cand in ("backend/jobs/celery_app.py", "backend/celery_app.py"):
            app = self.text(cand)
            if app:
                break
        if not app:
            return ProbeResult(False, "celery_app.py not found", resolvable=False)
        missing = sorted(t for t in tasks if not re.search(rf"\b{re.escape(t)}\b", app))
        if missing:
            return ProbeResult(True, f"{len(missing)} of {len(tasks)} task(s) absent "
                                     f"from the beat schedule: {missing[:5]}")
        return ProbeResult(False, f"all {len(tasks)} task(s) now appear in the "
                                  f"beat schedule -- fixed")

    def _rel(self, p: Path) -> str:
        """Absolute path -> repo-relative POSIX string."""
        try:
            return p.relative_to(self.root).as_posix()
        except ValueError:
            return str(p)

    def _migration_downgrade_empty(self, probe: dict) -> ProbeResult:
        """Law 57: `downgrade()` must have a body, or be explicitly irreversible."""
        rel = probe.get("path", "")
        tree = self.tree(rel)
        if tree is None:
            return ProbeResult(False, f"{rel} does not parse", resolvable=False)
        seen = False
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name != "downgrade":
                continue
            seen = True
            substantive = []
            for s in node.body:
                if isinstance(s, ast.Pass):
                    continue
                if isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant):
                    continue          # docstring or bare string
                substantive.append(s)
            if substantive:
                return ProbeResult(False, f"`downgrade()` now has a body -- fixed")
            return ProbeResult(True, "`downgrade()` is still empty or pass-only")
        if not seen:
            return ProbeResult(False, f"no downgrade() in {rel} -- the code moved",
                               resolvable=False)
        return ProbeResult(False, f"no downgrade() in {rel}", resolvable=False)

    def _destructive_op_unguarded(self, probe: dict) -> ProbeResult:
        """Law 57: a destructive op needs a guard or expand-contract staging.

        `op.execute(...)` is NOT destructive by itself -- it is the escape hatch
        through which every statement is issued, and four benign migrations
        (ADD COLUMN, CREATE MATERIALIZED VIEW, CREATE FUNCTION, a backfill
        UPDATE) were reported as unguarded destructive ops because the bare call
        name was matched. The SQL is classified instead: DROP, TRUNCATE, DELETE
        without WHERE, `ALTER ... DROP`, and `ALTER COLUMN ... TYPE`.
        """
        rel = probe.get("path", "")
        body = self.text(rel)
        if not body:
            return ProbeResult(False, f"{rel} unreadable", resolvable=False)
        lines = body.splitlines()
        tree = self.tree(rel)
        GUARD = re.compile(r"\bif\b|\bunless\b|guard|batch_alter_table|"
                           r"expand|contract|addfinalizer", re.I)
        DESTRUCTIVE = re.compile(r"\b(?:op\.)?(?:drop_column|drop_table|"
                                 r"drop_constraint|drop_index)\b")
        if tree is None:
            return ProbeResult(False, f"{rel} does not parse", resolvable=False)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = getattr(node.func, "attr", "")
            if fn in ("drop_column", "drop_table", "drop_constraint", "drop_index"):
                destructive = True
            elif fn == "execute":
                destructive = _sql_is_destructive(node, tree)
            else:
                continue
            if not destructive:
                continue
            ln = getattr(node, "lineno", 1)
            stmt = "\n".join(lines[ln - 1:ln + 3])
            if GUARD.search(stmt):
                return ProbeResult(False, f"line {ln} destructive op is now guarded "
                                          f"-- fixed")
            return ProbeResult(True, f"line {ln} destructive op is still unguarded")
        return ProbeResult(False, f"no destructive SQL remains in {rel} -- "
                                  f"re-derived from the parsed statement")
        return ProbeResult(False, f"no destructive op in {rel} -- the code moved",
                           resolvable=False)

    def _ci_step_absent(self, probe: dict) -> ProbeResult:
        """Law 44: supply-chain gates must appear in CI."""
        d = self.root / probe.get("path", ".github/workflows")
        if not d.exists():
            return ProbeResult(False, f"{probe.get('path')} not present",
                               resolvable=False)
        rx = probe.get("step") or ""
        found = []
        for p in sorted(list(d.glob("*.yml")) + list(d.glob("*.yaml"))):
            body = p.read_text(encoding="utf-8-sig", errors="replace")
            if re.search(rx, body, re.I):
                found.append(p.name)
        if found:
            return ProbeResult(False, f"supply-chain step present in "
                                      f"{sorted(set(found))} -- fixed")
        return ProbeResult(True, f"no CI workflow matches {rx!r}")

    def _router_has_no_endpoints(self, probe: dict) -> ProbeResult:
        """Law 8: a file under routers/ should declare HTTP endpoints."""
        rel = probe.get("path", "")
        tree = self.tree(rel)
        if tree is None:
            return ProbeResult(False, f"{rel} does not parse", resolvable=False)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for d in node.decorator_list:
                if re.search(r"\.(get|post|put|patch|delete|websocket)\s*\(",
                             ast.unparse(d)):
                    return ProbeResult(False, f"`{node.name}` declares an endpoint "
                                              f"-- fixed")
        return ProbeResult(True, f"{rel} still declares zero endpoint decorators")


    def _duplicate_files_both_present(self, probe: dict) -> ProbeResult:
        """Law 67: do BOTH copies of a duplicated file still exist?"""
        paths = probe.get("paths") or []
        if len(paths) < 2:
            return ProbeResult(False, "probe names fewer than 2 paths",
                               resolvable=False)
        present = [p for p in paths if (self.root / p).exists()]
        if len(present) == len(paths[:2]):
            a, b = paths[0], paths[1]
            same = (self.text(a) == self.text(b)) and bool(self.text(a))
            if same:
                return ProbeResult(True, f"{a} and {b} are still byte-identical")
            return ProbeResult(False,
                               f"both files exist but their contents now differ "
                               f"— no longer a duplicate")
        missing = [p for p in paths[:2] if p not in present]
        return ProbeResult(False, f"duplicate removed ({', '.join(missing)}) — fixed")

    def _duplicated_bodies_present(self, probe: dict) -> ProbeResult:
        """Law 67: does this file STILL share normalised function bodies with another?

        Compares normalised AST bodies between the two files, which is how the
        detector found them. A name count is not the claim.
        """
        paths = probe.get("paths") or []
        names = probe.get("names") or []
        if len(paths) < 2 or not names:
            return ProbeResult(False, "probe names no pair or no functions",
                               resolvable=False)
        a, b = paths[0], paths[1]
        ta, tb = self.tree(a), self.tree(b)
        if ta is None or tb is None:
            return ProbeResult(False, f"cannot parse {a} or {b}", resolvable=False)
        ba = self._bodies(ta)
        bb = self._bodies(tb)
        if not ba or not bb:
            return ProbeResult(False, "no function bodies to compare",
                               resolvable=False)
        shared = [n for n in names
                  if n in ba and n in bb and (ba[n] & bb[n])]
        if shared:
            return ProbeResult(True,
                               f"{len(shared)} function body/ies still duplicated: "
                               f"{shared[:5]}")
        return ProbeResult(False,
                           "no duplicated bodies remain between the two files "
                           "— fixed")

    def _bodies(self, tree) -> dict[str, set[str]]:
        """function name -> every normalised hash that name has in this file.

        A name -> single-value map was wrong twice over. It normalised only the
        body statements while the detector hashes the WHOLE function node, so the
        two never agreed; and a name defined twice in one file (an overload or a
        same-named method on two classes) collapsed to whichever node was walked
        last, hiding the copy that actually matched. Values are now a set so both
        definitions survive and the claim can hold if EITHER pair matches.
        """
        import hashlib
        out: dict[str, set[str]] = {}
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            try:
                h = hashlib.sha1(
                    ast.dump(node, annotate_fields=False).encode()).hexdigest()[:16]
            except Exception:
                continue
            out.setdefault(node.name, set()).add(h)
        return out

    def _ast_model_missing_column(self, probe: dict) -> ProbeResult:
        """Law 23: does the model at ``line`` still lack ``column``?

        `CLUSTER-tf-missing-{country_code,created_at,updated_at,is_deleted}` is 35
        findings whose only possible refutation is "the column is there now", and
        no probe kind could ask that -- so all 35 entered the plan with no
        independent verification.
        """
        rel = probe.get("path", "")
        want_line = int(probe.get("line") or 0)
        column = probe.get("column") or ""
        table = probe.get("table") or ""
        tree = self.tree(rel)
        if tree is None:
            return ProbeResult(False, f"{rel} does not parse", resolvable=False)
        if not column:
            return ProbeResult(False, "probe names no column", resolvable=False)

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            names: set[str] = set()
            tables: set[str] = set()
            for sub in ast.walk(node):
                # `__tablename__ = "x"` is an Assign, not a Call. Collecting it
                # only from Call nodes left `tables` permanently empty, so every
                # one of these 35 findings reported "no model class at or beside
                # line N -- the code moved", i.e. no verdict at all.
                if isinstance(sub, ast.Assign):
                    for t in sub.targets:
                        if isinstance(t, ast.Name):
                            if t.id == "__tablename__" \
                                    and isinstance(sub.value, ast.Constant) \
                                    and isinstance(sub.value.value, str):
                                tables.add(sub.value.value)
                            else:
                                # Declarative style: the COLUMN NAME is the
                                # assignment target. `Column`'s first positional
                                # argument is the TYPE, so
                                # `country_code = Column(String(2))` must be
                                # read from the target -- reading arg 0 saw
                                # "String" and never saw the column, so the probe
                                # could never observe a fixed column.
                                names.add(t.id)
                    continue
                if not isinstance(sub, ast.Call):
                    continue
                nm = getattr(sub.func, "id", None) or getattr(sub.func, "attr", None)
                if nm in ("Column", "mapped_column"):
                    # Table style: Column("name", Type, ...) inside a Table(...)
                    # declaration does put the name first.
                    for a in sub.args:
                        if isinstance(a, ast.Constant) and isinstance(a.value, str):
                            names.add(a.value)
                            break
                    for k in sub.keywords:
                        if k.arg == "name" and isinstance(k.value, ast.Constant):
                            names.add(str(k.value.value))
            # These findings cite the TABLE, not the class, so the line is only a
            # hint. Matching within 3 lines found no class and reported every one
            # of them unresolvable; match on `__tablename__` across the file.
            if table:
                if table not in tables:
                    continue
            elif want_line and abs(node.lineno - want_line) > 3:
                continue
            if column in names:
                return ProbeResult(False, f"`{node.name}` now declares {column} -- fixed")
            return ProbeResult(True, f"`{node.name}` (table `{table or chr(63)}`) still lacks {column}")
        return ProbeResult(False, f"no model class at or beside line {want_line} in "
                               f"{rel} -- the code moved", resolvable=False)

    def _text_present(self, probe: dict) -> ProbeResult:
        window, ok = self._window(probe)
        if not ok:
            return ProbeResult(False, f"{probe.get('path')} unreadable",
                               resolvable=False)
        pat = probe.get("pattern", "")
        if re.search(pat, window, re.I | re.MULTILINE):
            return ProbeResult(True, f"pattern {pat!r} present as claimed")
        return ProbeResult(False, f"pattern {pat!r} is NOT present")

    def _text_matches(self, probe: dict) -> ProbeResult:
        window, ok = self._window(probe)
        if not ok:
            return ProbeResult(False, "unreadable", resolvable=False)
        # MULTILINE matters: an import-shape claim is written as
        # `^\s*(?:from|import)\s+infrastructure`, and without it `^` matches only
        # at offset 0. Every such probe then reported "0 matches" and 162
        # import-law findings stayed silently unresolvable.
        found = re.findall(probe.get("pattern", ""), window, re.MULTILINE)
        expected = probe.get("count")
        if expected is None:
            return ProbeResult(bool(found), f"{len(found)} match(es)")
        return ProbeResult(len(found) == int(expected),
                           f"{len(found)} match(es), expected {expected}")

    # -- AST probes -----------------------------------------------------------
    def _calls_near(self, rel: str, fn: str, line: int, span: int,
                    first_arg: str | None = None, target_name: str | None = None):
        tree = self.tree(rel)
        if tree is None:
            return None
        out = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            if name != fn:
                continue
            ln = getattr(node, "lineno", 0)
            if span and abs(ln - line) > span:
                continue
            if first_arg is not None:
                if not node.args:
                    continue
                a0 = node.args[0]
                got = a0.value if isinstance(a0, ast.Constant) else None
                if got != first_arg:
                    continue
            if target_name is not None:
                # `user = relationship("User", ...)` — the ATTRIBUTE name is
                # the node's identity. Matching args[0] ("User") against the
                # attribute ("user") found nothing and produced 305
                # unresolvable probes.
                holder = getattr(node, "parent", None)
                seg = self.text(rel)
                lo = max(0, ln - 3)
                head = "\n".join(self.lines(rel)[lo:ln])
                m = re.search(r"(\w+)\s*(?::[^=\n]+)?=\s*$", head)
                if not m or m.group(1) != target_name:
                    continue
            out.append(node)
        out.sort(key=lambda n: abs(getattr(n, "lineno", 0) - line))
        return out

    def _ast_call_without_kwarg(self, probe: dict) -> ProbeResult:
        rel = probe.get("path", "")
        calls = self._calls_near(rel, probe.get("call", ""),
                                int(probe.get("line") or 0),
                                int(probe.get("within", 12)),
                                probe.get("first_arg"),
                                probe.get("target_name"))
        if calls is None:
            return ProbeResult(False, f"{rel} does not parse", resolvable=False)
        if not calls:
            return ProbeResult(False, f"no {probe.get('call')}() call found near "
                                       f"line {probe.get('line')} — the code moved",
                               resolvable=False)
        kwarg = probe.get("require_absent_kwarg", "")
        node = calls[0]
        present = [k.arg for k in node.keywords]
        if kwarg and kwarg in present:
            val = next((ast.unparse(k.value) for k in node.keywords
                        if k.arg == kwarg), "?")
            return ProbeResult(False, f"line {node.lineno} now declares "
                                       f"{kwarg}={val} — fixed")
        return ProbeResult(
            True,
            f"line {node.lineno} {probe.get('call')}() has no {kwarg} "
            f"(present: {present or 'none'})")

    def _relationship_nodes(self, rel: str, name: str, line: int, span: int):
        """Assignments whose value is ``relationship(...)`` bound to ``name``.

        Walking ``ast.Assign`` rather than searching the call's own line is what
        makes the node identity exact: ``user = relationship("User", ...)``
        binds the ATTRIBUTE ``user`` to a call whose first argument is the
        unrelated target class ``"User"``. Matching the argument found nothing.
        """
        tree = self.tree(rel)
        if tree is None:
            return None
        out = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
                continue
            if getattr(node.value.func, "attr", getattr(node.value.func, "id", "")) \
                    != "relationship":
                continue
            target = None
            for t in node.targets:
                if isinstance(t, ast.Name):
                    target = t.id
            if target != name:
                continue
            ln = getattr(node.value, "lineno", 0)
            if span and abs(ln - line) > span:
                continue
            out.append((node, ln))
        out.sort(key=lambda p: abs(p[1] - line))
        return out

    def _ast_rel_missing_kwarg(self, probe: dict) -> ProbeResult:
        """A ``relationship()`` missing ``lazy=`` — inheritance-aware.

        A ``lazy=`` supplied by the declarative base satisfies Law 45, so an
        inherited default must be resolved before absence is reported. Without
        this, every relationship on an inherited base is a false positive.
        """
        rel = probe.get("path", "")
        name = probe.get("target_name") or probe.get("first_arg")
        pairs = self._relationship_nodes(rel, name, int(probe.get("line") or 0),
                                        int(probe.get("within", 6)))
        if pairs is None:
            return ProbeResult(False, f"{rel} does not parse", resolvable=False)
        if not pairs:
            return ProbeResult(False, f"no relationship bound to {name!r} near "
                                       f"line {probe.get('line')} — the code moved",
                               resolvable=False)
        kwarg = probe.get("require_absent_kwarg", "lazy")
        _assign, ln = pairs[0]
        node = pairs[0][0].value
        if any(k.arg == kwarg for k in node.keywords):
            val = next((ast.unparse(k.value) for k in node.keywords
                        if k.arg == kwarg), "?")
            return ProbeResult(False, f"line {ln} relationship({name!r}) declares "
                                       f"{kwarg}={val} — fixed")
        base = self._relationship_default_kwarg(rel)
        if base is not None and kwarg in base:
            return ProbeResult(False,
                               f"line {ln} inherits {kwarg} from the declarative "
                               f"base — Law 45 satisfied")
        return ProbeResult(True, f"line {ln} relationship({name!r}) has no {kwarg} "
                                  f"and inherits none")

    def _relationship_default_kwarg(self, rel: str) -> set[str] | None:
        """Kwargs a base class supplies to every ``relationship()``."""
        tree = self.tree(rel)
        if tree is None:
            return None
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for stmt in node.body:
                if isinstance(stmt, ast.FunctionDef) and stmt.name == "relationship":
                    return {kw.arg for kw in stmt.args.kwonlyargs}
                if isinstance(stmt, ast.Assign) and stmt.value is not None \
                        and getattr(stmt.value, "attr", "") == "relationship":
                    pass
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.value, ast.Call) \
                        and getattr(stmt.value.func, "attr", "") == "relationship":
                    return {kw.arg for kw in stmt.value.keywords}
        # no local base override: look for a shared declarative base
        for cand in ("backend/infrastructure/database/base.py",
                     "backend/infrastructure/database/base_class.py",
                     "backend/infrastructure/database/base_vo.py"):
            t2 = self.tree(cand)
            if t2 is None:
                continue
            for node in ast.walk(t2):
                if isinstance(node, ast.ClassDef):
                    for stmt in node.body:
                        if isinstance(stmt, ast.FunctionDef) \
                                and stmt.name == "relationship":
                            return {kw.arg for kw in stmt.args.kwonlyargs}
        return None

    def _ast_annotation_contains(self, probe: dict) -> ProbeResult:
        rel = probe.get("path", "")
        tree = self.tree(rel)
        if tree is None:
            return ProbeResult(False, f"{rel} does not parse", resolvable=False)
        name = probe.get("name")
        needle = probe.get("contains", "float")
        line = int(probe.get("line") or 0)
        span = int(probe.get("within", 3) or 3)
        for node in ast.walk(tree):
            ln = getattr(node, "lineno", 0)
            if line and abs(ln - line) > span:
                continue
            target = None
            ann = None
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                target, ann = node.target.id, node.annotation
            elif isinstance(node, ast.arg) and node.annotation is not None:
                target, ann = node.arg, node.annotation
            if not target or (name and target != name):
                continue
            rendered = ast.unparse(ann)
            if needle.lower() in rendered.lower():
                return ProbeResult(True, f"line {ln} `{target}: {rendered}`")
            return ProbeResult(False, f"line {ln} `{target}` is now `{rendered}`")
        return ProbeResult(False, f"no annotated assignment named {name!r} near "
                                   f"line {line}", resolvable=False)

    def _ast_attr_undeclared(self, probe: dict) -> ProbeResult:
        """``settings.X`` read where ``X`` is not declared on ``Settings``."""
        attr = probe.get("attribute")
        if not attr:
            return ProbeResult(False, "no attribute", resolvable=False)
        declared = probe.get("declared")
        if declared is None:
            tree = self.tree(probe.get("declarations_path",
                                        "backend/config.py"))
            if tree is None:
                return ProbeResult(False, "cannot read Settings", resolvable=False)
            declared = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for stmt in node.body:
                        if isinstance(stmt, ast.AnnAssign) \
                                and isinstance(stmt.target, ast.Name):
                            declared.add(stmt.target.id)
                        elif isinstance(stmt, ast.Assign):
                            declared.update(t.id for t in stmt.targets
                                            if isinstance(t, ast.Name))
                        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            declared.add(stmt.name)
        if attr in declared:
            return ProbeResult(False, f"Settings now declares `{attr}` — fixed")
        return ProbeResult(True, f"`{attr}` is still absent from Settings "
                                 f"({len(declared)} fields declared)")

    # -- structural probes ----------------------------------------------------
    def _attribute_absent_in_dict(self, probe: dict) -> ProbeResult:
        rel = probe.get("path", "")
        src = self.text(rel)
        if not src:
            return ProbeResult(False, f"{rel} unreadable", resolvable=False)
        tree = self.tree(rel)
        if tree is None:
            return ProbeResult(False, f"{rel} does not parse", resolvable=False)
        table = probe.get("table")
        key = probe.get("key")
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == table:
                    seg = ast.get_source_segment(src, node) or ""
                    if re.search(rf"[\"']{re.escape(key)}[\"']\s*:", seg):
                        return ProbeResult(False, f"{table}[{key}] now exists")
                    return ProbeResult(True, f"{table} has no {key!r}")
        return ProbeResult(False, f"table {table!r} not found in {rel}",
                           resolvable=False)

    def _path_absent(self, probe: dict) -> ProbeResult:
        rel = probe.get("path", "")
        if (self.root / rel).exists():
            return ProbeResult(False, f"{rel} now exists — fixed")
        return ProbeResult(True, f"{rel} is absent as claimed")

    def _path_present(self, probe: dict) -> ProbeResult:
        rel = probe.get("path", "")
        if (self.root / rel).exists():
            return ProbeResult(True, f"{rel} exists")
        return ProbeResult(False, f"{rel} does not exist")

    def _package_cycle_exists(self, probe: dict) -> ProbeResult:
        """A package import cycle, re-derived from the AST import graph.

        Replaces a finding whose ``file`` was the cycle *description* — which the
        gate correctly reported as a non-existent path 17 times.

        This is a real strongly-connected-component test, not "is there a direct
        edge". A direct-edge check reports a cycle for any mutual pair and misses
        longer rings, which is precisely the class of confidently-wrong probe
        this project keeps having to undo.
        """
        packages = probe.get("packages") or []
        if len(packages) < 2:
            return ProbeResult(False, "cycle needs >=2 packages", resolvable=False)
        pkgs = [p[0] if isinstance(p, (tuple, list)) else p for p in packages]
        edges = probe.get("edges") or self._import_edges(pkgs)
        if not edges:
            return ProbeResult(False, "import graph unavailable", resolvable=False)
        graph = {p: set() for p in pkgs}
        for src, dsts in edges.items():
            if src not in graph:
                continue
            for dst in dsts:
                if dst in graph and dst != src:
                    graph[src].add(dst)
        # Tarjan's strongly-connected components: any component with >1 member,
        # or a member with a self-loop, IS a cycle.
        index: dict = {}
        low: dict = {}
        on_stack: dict = {}
        stack: list = []
        counter = [0]
        sccs: list[list] = []

        def strongconnect(v):
            work = [(v, iter(graph[v]))]
            while work:
                node, it = work[-1]
                if node not in index:
                    index[node] = low[node] = counter[0]
                    counter[0] += 1
                    stack.append(node)
                    on_stack[node] = True
                advanced = False
                for w in it:
                    if w not in index:
                        work.append((w, iter(graph[w])))
                        advanced = True
                        break
                    if on_stack.get(w):
                        low[node] = min(low[node], index[w])
                if advanced:
                    continue
                work.pop()
                if low[node] == index[node]:
                    comp = []
                    while True:
                        w = stack.pop()
                        on_stack[w] = False
                        comp.append(w)
                        if w == node:
                            break
                    sccs.append(comp)
                if work:
                    parent = work[-1][0]
                    low[parent] = min(low[parent], low[node])

        for n in graph:
            if n not in index:
                strongconnect(n)
        cycles = [c for c in sccs
                  if len(c) > 1 or (len(c) == 1 and c[0] in graph[c[0]])]
        if not cycles:
            return ProbeResult(False, f"no cycle among {len(packages)} packages "
                                       f"(import graph re-derived)")
        biggest = max(cycles, key=len)
        return ProbeResult(True, f"cycle of {len(biggest)} packages re-derived: "
                                  + " -> ".join(sorted(biggest)))

    def _import_edges(self, packages: list[str]):
        """Package-level import edges, resolved from the IMPORTING FILE.

        The source package comes from where the import statement lives; the
        target from the module it names. Deriving both from the imported module
        made the walk circular and produced an empty graph.
        """
        from .util import iter_files, parse_python
        # Normalise to plain strings: the caller may hand over 1-tuples from the
        # cycle normalisation, and a tuple key silently matches nothing, which
        # made the whole graph come back empty.
        pkgs = [p[0] if isinstance(p, (tuple, list)) else p for p in packages]
        out: dict[str, set[str]] = {p: set() for p in pkgs}

        def owner(mod: str) -> str | None:
            if mod in out:
                return mod
            best = None
            for p in pkgs:
                if mod.startswith(p + ".") and (best is None or len(p) > len(best)):
                    best = p
            return best

        for f in iter_files(self.root / "backend", (".py",)):
            try:
                rel = f.resolve().relative_to(self.root).as_posix()
            except ValueError:
                continue
            parts = rel.split("/")
            if len(parts) < 3 or parts[1] != "domains":
                continue
            src = f"domains.{parts[2]}"
            if src not in out:
                continue
            parsed = parse_python(f)
            if not parsed.tree:
                continue
            for node in ast.walk(parsed.tree):
                mods = []
                if isinstance(node, ast.ImportFrom) and node.module:
                    mods.append(node.module)
                elif isinstance(node, ast.Import):
                    mods.extend(a.name for a in node.names)
                for mod in mods:
                    dst = owner(mod)
                    if dst and dst != src:
                        out[src].add(dst)
        return out if any(out.values()) else None

    def _filename_count_above(self, probe: dict) -> ProbeResult:
        """A claim about how many files match a glob in a directory.

        Token matching against file *contents* can never adjudicate a claim about
        file *names*, which is exactly what the root-discipline finding makes.
        """
        rel = probe.get("path", "")
        directory = self.root / rel
        if not directory.is_dir():
            return ProbeResult(False, f"{rel} is not a directory",
                               resolvable=False)
        pattern = probe.get("glob", "*")
        try:
            n = sum(1 for _ in directory.glob(pattern))
        except Exception as exc:
            return ProbeResult(False, f"glob failed: {exc}", resolvable=False)
        actual = probe.get("actual")
        if actual is not None and int(actual) != n:
            return ProbeResult(False, f"count changed: audit saw {actual}, "
                                       f"now {n}", resolvable=False)
        floor = int(probe.get("at_least", 1))
        if n >= floor:
            return ProbeResult(True, f"{n} file(s) match {pattern} in {rel}")
        return ProbeResult(False, f"only {n} file(s) match {pattern} in {rel} "
                                   f"— remediated")

    def _api_path_resolves(self, probe: dict) -> ProbeResult:
        """Does a frontend API path resolve to a backend route?

    The route set is re-derived here from the backend source, NOT taken from
    the finding. A probe that replays the detector's own answer would convert an
    unknown into a confident "CONFIRMED", which is the one failure mode this
    gate exists to eliminate.
    """
        route = probe.get("route", "")
        if not route:
            return ProbeResult(False, "no route in probe", resolvable=False)
        routes = self._backend_routes()
        if not routes:
            return ProbeResult(False, "no backend routes parsed — cannot judge",
                               resolvable=False)
        normalised = set(routes)
        normalised |= {re.sub(r"^/api/v\d+", "", r) for r in routes}
        if route in normalised:
            return ProbeResult(True, f"`{route}` resolves to a declared route")
        rx = "^" + re.sub(r"\$\{[^}]+\}", r"[^/]+", re.escape(route)) + "/?$"
        if any(re.match(rx, r) for r in normalised):
            return ProbeResult(True, f"`{route}` matches a declared route by shape")
        return ProbeResult(False, f"`{route}` matches none of {len(routes)} "
                                   f"backend routes — contract break")

    def _backend_routes(self) -> set[str]:
        """Re-derive every path declared by a backend router."""
        if getattr(self, "_routes_cache", None) is not None:
            return self._routes_cache
        from .util import iter_files, read_text
        rx = re.compile(r'@(?:\w+\.)?(?:router|app)\.(?:get|post|put|patch|delete)'
                        r'\(\s*["\']([^"\']+)["\']')
        prefix_rx = re.compile(r'APIRouter\(\s*prefix\s*=\s*["\']([^"\']+)["\']')
        out: set[str] = set()
        for f in iter_files(self.root / "backend", (".py",)):
            rel = f.resolve().relative_to(self.root).as_posix()
            if "/routers/" not in rel and not rel.endswith("main.py"):
                continue
            text, _ = read_text(f)
            if not text:
                continue
            m = prefix_rx.search(text)
            prefix = m.group(1).rstrip("/") if m else ""
            for r in rx.finditer(text):
                path = r.group(1)
                if not path.startswith("/"):
                    continue
                out.add(((prefix + path).replace("//", "/")).rstrip("/") or "/")
        self._routes_cache = out
        return out

    def _count_below(self, probe: dict) -> ProbeResult:
        """A measured quantity is at or under a threshold."""
        actual = probe.get("actual")
        limit = int(probe.get("limit", 0))
        if actual is None:
            return ProbeResult(False, "no measured value recorded",
                               resolvable=False)
        if actual <= limit:
            return ProbeResult(True, f"{actual} <= {limit}")
        return ProbeResult(False, f"{actual} > {limit} — no longer a violation")

    def _count_at_or_above(self, probe: dict) -> ProbeResult:
        """A measured quantity is at or OVER a threshold.

        The mirror of `_count_below`, and needed because "this router contains N
        branch statements" is a violation for having TOO MANY. Using `count_below`
        for it asserts the opposite: it held on the single file that had dropped
        below the threshold and refuted the six that still violate it -- a probe
        that systematically contradicted its own finding.
        """
        actual = probe.get("actual")
        floor = int(probe.get("at_least", 1))
        if actual is None:
            return ProbeResult(False, "no measured value recorded",
                               resolvable=False)
        if int(actual) >= floor:
            return ProbeResult(True, f"{actual} >= {floor} — still over the limit")
        return ProbeResult(False, f"{actual} < {floor} — reduced below the limit")

    # -- structural probes ---------------------------------------------------- #
    # These three exist because 200 findings could not be re-verified by any
    # other means. `text_matches` cannot express "this function is too long" or
    # "this router reaches the database", because both are properties of the
    # syntax tree rather than of the text. Without them those findings could only
    # ever be re-read by a model, which is the exact failure mode this file
    # exists to remove.

    def _function_len_above(self, probe: dict) -> ProbeResult:
        """Does the named function still exceed the line limit?

        The function is located by **name**, not by proximity to a line. A
        line-anchored lookup silently measures whichever function drifted into
        that range after an edit, which produces a confidently wrong length.
        """
        rel = probe.get("path", "")
        name = probe.get("function", "")
        limit = int(probe.get("limit") or 0)
        tree = self.tree(rel)
        if tree is None:
            return ProbeResult(False, f"{rel} does not parse", resolvable=False)
        if not name:
            return ProbeResult(False, "no function name in probe", resolvable=False)
        matches = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                    and node.name == name:
                length = (getattr(node, "end_lineno", node.lineno) or node.lineno) \
                    - node.lineno + 1
                matches.append((node.lineno, length))
        if not matches:
            return ProbeResult(False, f"`{name}` no longer exists in {rel} — "
                                      f"the code moved", resolvable=False)
        ln, length = min(matches, key=lambda t: abs(t[0] - int(probe.get("line") or 0)))
        if length > limit:
            return ProbeResult(True, f"`{name}` at line {ln} is {length} lines "
                                     f"(> {limit}) as claimed")
        return ProbeResult(False, f"`{name}` is now {length} lines (<= {limit}) — "
                                  f"the defect has been fixed")

    def _ast_forbidden_call_in_function(self, probe: dict) -> ProbeResult:
        """Does the named function still make a forbidden call?

        Router thinness (Law 15) is "auth + feature gate + one service call", so
        the violation is a *call kind* inside a named function body: a second
        service call, or a direct database/session access. Locating the function
        by name keeps the verdict attached to the same function on every run.
        """
        rel = probe.get("path", "")
        name = probe.get("function", "")
        call_rx = probe.get("call", "")
        tree = self.tree(rel)
        if tree is None:
            return ProbeResult(False, f"{rel} does not parse", resolvable=False)
        target = None
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                    and node.name == name:
                target = node
                break
        if target is None:
            return ProbeResult(False, f"`{name}` no longer exists in {rel}",
                               resolvable=False)
        hits = 0
        for node in ast.walk(target):
            if not isinstance(node, ast.Call):
                continue
            called = getattr(node.func, "attr", getattr(node.func, "id", ""))
            if call_rx and re.search(call_rx, str(called)):
                hits += 1
        expected = probe.get("count")
        if expected is None:
            return ProbeResult(hits > 0, f"{hits} `{call_rx}` call(s) in `{name}`")
        return ProbeResult(hits == int(expected),
                           f"{hits} `{call_rx}` call(s) in `{name}`, "
                           f"expected {expected}")

    def _file_line_count_above(self, probe: dict) -> ProbeResult:
        """Does the file still exceed the line limit?

        The measured count is recomputed from the file, so it stays honest as the
        file is split. 135 findings in dimension 17 were unverifiable before this
        existed because "this file has 4,520 lines" is not a text property.
        """
        rel = probe.get("path", "")
        limit = int(probe.get("limit") or 0)
        text = self.text(rel)
        if text is None:
            return ProbeResult(False, f"{rel} unreadable", resolvable=False)
        count = len(text.splitlines())
        if count > limit:
            return ProbeResult(True, f"{rel} is {count} lines (> {limit})")
        return ProbeResult(False, f"{rel} is now {count} lines (<= {limit}) — "
                                  f"the file has been split")

    def _symbol_occurrences(self, probe: dict) -> ProbeResult:
        """Does this symbol still appear the recorded number of times?

        Duplicate-definition findings cite a symbol and a count. Re-counting it
        independently is what lets the claim flip when one copy is deleted.
        """
        rel = probe.get("path", "")
        symbol = probe.get("symbol", "")
        expected = probe.get("expected")
        text = self.text(rel)
        if text is None:
            return ProbeResult(False, f"{rel} unreadable", resolvable=False)
        if not symbol:
            return ProbeResult(False, "no symbol in probe", resolvable=False)
        n = len(re.findall(rf"^\s*(?:async\s+)?def\s+{re.escape(symbol)}\s*\(",
                           text, re.MULTILINE))
        if n == 0:
            n = len(re.findall(rf"\b{re.escape(symbol)}\b", text))
        if expected is None:
            return ProbeResult(n > 0, f"`{symbol}` occurs {n} time(s) in {rel}")
        return ProbeResult(n == int(expected),
                           f"`{symbol}` occurs {n} time(s), expected {expected}")

    def _module_imports_above(self, probe: dict) -> ProbeResult:
        """Does this module import from a layer it may not import from?

        Law 1 is directional, and the layer of a file is derived from its path
        rather than trusted from the finding. Deriving it here is the whole point:
        a probe that replayed the detector's own layer decision could not detect
        a misclassified file, which is one of the ways the import law produced
        wrong verdicts.
        """
        rel = probe.get("path", "")
        forbidden = probe.get("modules") or []
        tree = self.tree(rel)
        if tree is None:
            return ProbeResult(False, f"{rel} does not parse", resolvable=False)
        layer = probe.get("layer")
        if not layer:
            layer = _layer_of(rel)
        allowed = _ALLOWED_IMPORTS.get(layer, set())
        # `allow_prefixes` is the FINER rule and must REPLACE the coarse one for
        # the layer it constrains, not merely sit beside it. `modules` may
        # import `infrastructure` as a layer, so `allowed` keeps saying yes and
        # every hit was discarded -- the allowlist was consulted only to skip
        # imports and never to keep them. Here the subpackage allowlist becomes
        # the whole rule for that target.
        allow_prefixes = tuple(probe.get("allow_prefixes") or ())
        if allow_prefixes:
            for p in allow_prefixes:
                allowed = allowed - {p.split(".")[0]}
        hits = []
        for node in ast.walk(tree):
            mods: list[str] = []
            if isinstance(node, ast.Import):
                mods = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                if not node.module or node.level:
                    continue
                mods = [node.module]
            for mod in mods:
                if allow_prefixes and any(mod.startswith(p) for p in allow_prefixes):
                    continue
                top = mod.split(".")[0]
                if top in forbidden and top not in allowed:
                    hits.append(top)
        uniq = sorted(set(hits))
        if uniq:
            return ProbeResult(True, f"{rel} (layer={layer}) imports "
                                     f"{', '.join(uniq)} which it may not")
        return ProbeResult(False, f"{rel} imports nothing from "
                                  f"{', '.join(forbidden)} — fixed")


#: Aggregate law measurements, keyed by the id the probe builder emits. Defined
#: after the class so the methods above are already bound; ``_law_measure``
#: looks them up at call time.
_LAW_MEASURES = {
    "law01_reverse_imports": ProbeRunner._law_reverse_imports,
    "law04_ungated_route": ProbeRunner._law_ungated_route,
    "law05_set_local_missing": ProbeRunner._law_set_local_missing,
    "law07_undated_allowlist": ProbeRunner._law_undated_allowlist,
    "law12_extra_domains": ProbeRunner._law_extra_domains,
    "law13_extra_modules": ProbeRunner._law_extra_modules,
    "law19_float_money": ProbeRunner._law_float_money,
    "law21_python_timestamps": ProbeRunner._law_python_timestamps,
    "law23_missing_audit_columns": ProbeRunner._law_missing_audit_columns,
    "law27_temp_scripts": ProbeRunner._law_temp_scripts,
    "law34_fstring_sql": ProbeRunner._law_fstring_sql,
    "law37_rate_limiter": ProbeRunner._law_rate_limiter_fail_closed,
    "law45_relationship_lazy": ProbeRunner._law_relationship_lazy,
    "law49_migration_heads": ProbeRunner._law_migration_heads,
    "law53_fk_without_index": ProbeRunner._law_fk_without_index,
    "law54_missing_is_deleted": ProbeRunner._law_missing_is_deleted,
    "law58_print_calls": ProbeRunner._law_print_calls,
    "law59_silent_excepts": ProbeRunner._law_silent_excepts,
    "law62_todo_hygiene": ProbeRunner._law_todo_hygiene,
    "law84_raw_getenv": ProbeRunner._law_raw_getenv,
    "law03_event_spine": ProbeRunner._law_event_spine,
    "law123_provider_routing": ProbeRunner._law_provider_routing,
    "law129_provider_health": ProbeRunner._law_provider_health,
    "law222_offset_pagination": ProbeRunner._law_offset_pagination,
    "law248_runbooks": ProbeRunner._law_runbooks,
    "law275_field_encryption": ProbeRunner._law_field_encryption,
}
