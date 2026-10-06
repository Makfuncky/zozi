"""ZOZI Forensic Audit — Core data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class Phase(str, Enum):
    EMERGENCY = "emergency"
    BOOT = "boot"
    TECH = "tech"
    DB = "db"
    LOGIC = "logic"
    ARCH = "arch"
    SECURITY = "security"
    PAYMENT = "payment"
    COMPLIANCE = "compliance"
    FRONTEND = "frontend"
    MOBILE = "mobile"
    TESTING = "testing"
    INFRA = "infra"
    DOCS = "docs"
    DEFER = "defer"


class Priority(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class Status(str, Enum):
    NEW = "NEW"
    COMPILED = "COMPILED"
    RESOLVED = "RESOLVED"
    DEFERRED = "DEFERRED"
    INVALID = "INVALID"


class TruthLevel(str, Enum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"


class ClaimState(str, Enum):
    VERIFIED = "VERIFIED"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"
    CONTRADICTED = "CONTRADICTED"


class CompletionBlocker(str, Enum):
    YES = "yes"
    NO = "no"
    PARTIAL = "partial"


class EvidenceStrength(str, Enum):
    SINGLE = "single"
    MULTIPLE = "multiple"
    TRIANGULATED = "triangulated"


@dataclass(slots=True)
class Finding:
    id: str = ""
    dimension: str = ""
    phase: str = Phase.ARCH.value
    status: str = Status.NEW.value
    cluster: str = ""
    file: str = ""
    line: int = 0
    current: str = ""
    target: str = ""
    delta: str = ""
    fix: str = ""
    effort: str = "S"
    priority: str = Priority.P2.value
    confidence: int = 3
    evidence_strength: str = EvidenceStrength.SINGLE.value
    truth_level: str = TruthLevel.L0.value
    claim_state: str = ClaimState.VERIFIED.value
    sibling: str = ""
    verify: str = ""
    test: str = ""
    rollback: str = "git revert <commit>"
    blast_radius: str = ""
    depends_on: str = ""
    blocks: str = ""
    completion_blocker: str = CompletionBlocker.NO.value
    laws: tuple[int, ...] = field(default_factory=tuple)
    snippet: str = ""
    notes: str = ""
    origin: str = "static"
    #: Machine-checkable rule that re-decides this finding on the next run.
    #: Attached by `zz_core.probes.attach()`. It MUST be declared here: `Finding`
    #: is a `slots=True` dataclass, so assigning an undeclared attribute raises
    #: `AttributeError` — which silently killed the entire probe layer while every
    #: consumer (`emit.py`, `checklist.py`, `loop.py`) kept reading `f.probe`.
    probe: dict = field(default_factory=dict)


@dataclass(slots=True)
class Observation:
    scope_type: str = "file"
    scope_id: str = ""
    path: str = ""
    line: int = 0
    dimension: str = ""
    truth_level: str = TruthLevel.L0.value
    claim_state: str = ClaimState.VERIFIED.value
    evidence: str = ""
    note: str = ""
    cluster: str = ""


@dataclass(slots=True)
class ToolResult:
    name: str = ""
    cmd: str = ""
    exit_code: Optional[int] = None
    duration_s: float = 0.0
    stdout_tail: str = ""
    stderr_tail: str = ""
    available: bool = False
    skipped_reason: str = ""
    # integration results are carried back as (advisory) findings
    ok: bool = False
    findings: tuple = ()
    duration_ms: int = 0
    notes: str = ""
    #: Untruncated stdout, capped. Counts must be parsed from this, never from
    #: the truncated tail: a head+tail elision silently under-reports every
    #: count in a long test run.
    full_stdout: str = ""

    @property
    def status(self) -> str:
        if self.skipped_reason:
            return "SKIPPED"
        if self.exit_code is None:
            return "INFO" if self.ok else "SKIPPED"
        return "PASS" if self.exit_code == 0 else "FAIL"

    def to_row(self) -> dict:
        return {
            "name": self.name, "cmd": self.cmd, "status": self.status,
            "exit_code": self.exit_code, "duration_s": self.duration_s,
            "skipped_reason": self.skipped_reason, "notes": self.notes,
        }


def _finding_row(self) -> dict:
    return {
        "id": self.id, "dimension": self.dimension, "phase": self.phase,
        "status": self.status, "cluster": self.cluster, "file": self.file,
        "line": self.line, "current": self.current, "target": self.target,
        "delta": self.delta, "fix": self.fix, "effort": self.effort,
        "priority": self.priority, "confidence": self.confidence,
        "evidence_strength": self.evidence_strength,
        "truth_level": self.truth_level, "claim_state": self.claim_state,
        "sibling": self.sibling, "verify": self.verify, "test": self.test,
        "rollback": self.rollback, "blast_radius": self.blast_radius,
        "depends_on": self.depends_on, "blocks": self.blocks,
        "completion_blocker": self.completion_blocker,
        "laws": list(self.laws), "snippet": self.snippet,
        "notes": self.notes, "origin": self.origin,
        # Without this key the probe never reaches findings.jsonl, so every
        # downstream reader (`zozi_verify.py`, `zozi_compile.py`, the self-test)
        # sees a finding it can never re-decide.
        "probe": dict(self.probe or {}),
    }


def _finding_location(self) -> str:
    """Canonical ``file:line`` rendering used by every report table."""
    if not self.file:
        return "—"
    return f"{self.file}:{self.line}" if self.line else self.file


def _observation_row(self) -> dict:
    return {
        "scope_type": self.scope_type, "scope_id": self.scope_id,
        "path": self.path, "line": self.line, "dimension": self.dimension,
        "truth_level": self.truth_level, "claim_state": self.claim_state,
        "evidence": self.evidence, "note": self.note, "cluster": self.cluster,
    }


Finding.to_row = _finding_row
Finding.location = property(_finding_location)
Observation.to_row = _observation_row


@dataclass
class Recommendation:
    """An improvement the codebase does not currently encode anywhere.

    Recommendations are deliberately *not* findings: a missing
    ``create_refund_ledger_entry`` is a defect, while "batch payout
    reconciliation" is an opportunity. Mixing the two corrupts the blocker
    count, so the compiler treats them as a separate stream.
    """

    id: str = ""
    area: str = ""                 # design | data | workflow | finance | qa | coverage | ops
    title: str = ""
    rationale: str = ""
    current: str = ""
    proposal: str = ""
    benefit: str = ""              # why it matters, quantified where possible
    effort: str = "M"              # S=1h M=2.5h L=6h XL=20h
    impact: str = "medium"         # low | medium | high
    category: str = "automation"   # automation | quality | design | schema | process
    prerequisites: tuple = ()
    evidence: str = ""             # file:line or measured fact
    confidence: int = 4            # 1..5
    human_effort_saved: str = ""   # qualitative or hours/week
    dimension: str = ""
    origin: str = "static"

    def to_row(self) -> dict:
        return {
            "id": self.id, "area": self.area, "title": self.title,
            "rationale": self.rationale, "current": self.current,
            "proposal": self.proposal, "benefit": self.benefit,
            "effort": self.effort, "impact": self.impact,
            "category": self.category, "prerequisites": list(self.prerequisites),
            "evidence": self.evidence, "confidence": self.confidence,
            "human_effort_saved": self.human_effort_saved,
            "dimension": self.dimension, "origin": self.origin,
        }


@dataclass
class CheckResult:
    """What one check (one self-contained sub-agent) returns."""

    check: str = ""
    dimension: str = ""
    findings: list = field(default_factory=list)
    observations: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)
    facts: dict = field(default_factory=dict)
    error: str = ""


@dataclass
class ScanContext:
    root: Path = field(default_factory=Path.cwd)
    out_dir: Path = field(default_factory=lambda: Path.cwd() / "_zozi_audit")
    backend: Optional[Path] = None
    frontend: Optional[Path] = None
    all_files: list[Path] = field(default_factory=list)
    py_files: list[Path] = field(default_factory=list)
    ts_files: list[Path] = field(default_factory=list)
    js_files: list[Path] = field(default_factory=list)
    docs: list[Path] = field(default_factory=list)
    inventory: dict[str, Any] = field(default_factory=dict)
    tools: dict[str, ToolResult] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    run_id: str = ""
    started_at: str = ""
    fast: bool = False
    workers: int = 10

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root = self.root.resolve() if self.root.exists() else self.root
        self.out_dir = Path(self.out_dir)
        self.backend = Path(self.backend) if self.backend else self.root / "backend"
        self.frontend = Path(self.frontend) if self.frontend else self.root / "frontend"
        self.fast = bool(self.options.get("fast", self.fast))
        self.workers = int(self.options.get("workers", self.workers) or 10)
        self._memo: dict[str, Any] = {}
        self._text: dict[str, str] = {}
        self._lock = __import__("threading").RLock()

    # -- paths -------------------------------------------------------------- #
    def rel(self, p) -> str:
        """Repo-relative path, always with forward slashes.

        Every scanner matches on ``backend/domains/...``-style strings; a
        Windows ``\\`` separator silently defeats those filters and makes a
        check report zero findings instead of failing loudly.
        """
        p = Path(p)
        try:
            return p.resolve().relative_to(self.root.resolve()).as_posix()
        except ValueError:
            try:
                return p.relative_to(self.root).as_posix()
            except ValueError:
                return p.as_posix()

    def abs(self, p) -> Path:
        p = Path(p)
        return p if p.is_absolute() else self.root / p

    def line_of(self, p, needle: str, start: int = 0) -> int:
        """1-based line of ``needle`` in ``p`` (path, str path, or text)."""
        if isinstance(p, Path) or (isinstance(p, str) and ("/" in p or "\\" in p
                                                          or p.endswith((".py", ".ts", ".tsx", ".md", ".yml", ".yaml", ".json")))):
            text = self.read(self.abs(p))[0] if not Path(p).exists() else self.read(Path(p))[0]
        else:
            text = str(p)
        idx = text.find(needle, start)
        if idx == -1:
            return 0
        return text[:idx].count("\n") + 1

    # -- cached IO ---------------------------------------------------------- #
    def read(self, p):
        """Cached tolerant read; returns ``(text, truncated)``."""
        key = str(p)
        with self._lock:
            hit = self._text.get(key)
        if hit is not None:
            return hit
        from .util import read_text
        value = read_text(Path(p))
        with self._lock:
            self._text.setdefault(key, value)
            return self._text[key]

    def memo(self, key: str, factory):
        """Memoise a lazily-built shared fact across the worker pool."""
        with self._lock:
            if key in self._memo:
                return self._memo[key]
        value = factory()
        with self._lock:
            self._memo.setdefault(key, value)
            return self._memo[key]
