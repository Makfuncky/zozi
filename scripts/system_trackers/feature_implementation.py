#!/usr/bin/env python3
"""
ZOZI Feature Tracker — Automated Codebase Status Matrix Generator
=================================================================

Reads feature_definitions.yaml, scans the codebase folder-by-folder and
file-by-file, compares actual implementation against expected features,
calculates weighted completion percentages, and generates the full
CODEBASE_STATUS_MATRIX.md with all 6 table sections.

Optional: Uses local Ollama for semantic analysis of code vs. feature
descriptions (graceful degradation if Ollama unavailable).

Usage:
    python scripts/feature_tracker.py                    # normal scan
    python scripts/feature_tracker.py --with-ollama      # enable AI analysis
    python scripts/feature_tracker.py --output out.md    # custom output path
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

# ============================================================================
# CONFIG
# ============================================================================

ROOT_DIR = Path(__file__).resolve().parent.parent  # repo root
DEFINITIONS_FILE = ROOT_DIR / "scripts" / "feature_definitions.yaml"
DEFAULT_OUTPUT = ROOT_DIR / "documents" / "CODEBASE_STATUS_MATRIX_AUTO.md"

# Section mapping by scope tags
SECTION_MAPPING = {
    "section_i_infrastructure": ["Internal", "All roles"],
    "section_ii_customer": ["Customer"],
    "section_iii_supplier": ["Supplier"],
    "section_iv_logistics": ["Logistor"],
    "section_v_admin": ["Admin"],
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class CheckResult:
    name: str
    found: bool
    details: str = ""
    score: float = 0.0  # 0.0 - 1.0


@dataclass
class FeatureScore:
    feature_id: str
    name: str
    description: str
    scope: str
    todo_ref: str
    matrix_section: str
    weight: int
    checks: List[CheckResult] = field(default_factory=list)
    raw_score: float = 0.0
    weighted_score: float = 0.0
    status_emoji: str = "🔍"
    ai_analysis: Optional[str] = None

    def calculate(self) -> None:
        if not self.checks:
            self.raw_score = 0.0
        else:
            self.raw_score = sum(c.score for c in self.checks) / len(self.checks)
        self.weighted_score = self.raw_score * self.weight

        if self.raw_score >= 0.95:
            self.status_emoji = "✅"
        elif self.raw_score >= 0.60:
            self.status_emoji = "⚠️"
        elif self.raw_score > 0.0:
            self.status_emoji = "⚠️"
        else:
            self.status_emoji = "❌"


# ============================================================================
# FILE SYSTEM SCANNER
# ============================================================================

class CodebaseScanner:
    """Walks the codebase and verifies feature implementations."""

    def __init__(self, root: Path):
        self.root = root
        self._file_cache: Dict[Path, str] = {}

    def file_exists(self, rel_path: str) -> bool:
        return (self.root / rel_path).exists()

    def read_file(self, rel_path: str) -> Optional[str]:
        path = self.root / rel_path
        if not path.exists():
            return None
        if path in self._file_cache:
            return self._file_cache[path]
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            self._file_cache[path] = content
            return content
        except Exception:
            return None

    def find_pattern(self, rel_path: str, pattern: str) -> bool:
        content = self.read_file(rel_path)
        if not content:
            return False
        try:
            return bool(re.search(pattern, content, re.IGNORECASE))
        except re.error:
            return pattern.lower() in content.lower()

    def count_files_in_dir(self, rel_dir: str, ext: str = "") -> int:
        dir_path = self.root / rel_dir
        if not dir_path.exists():
            return 0
        count = 0
        for p in dir_path.rglob("*"):
            if p.is_file():
                if not ext or p.suffix == ext:
                    if "__pycache__" not in str(p) and "node_modules" not in str(p):
                        count += 1
        return count

    def check_backend_files(self, files: List[str]) -> CheckResult:
        if not files:
            return CheckResult("Backend Files", True, "none required", 1.0)
        found = [f for f in files if self.file_exists(f)]
        score = len(found) / len(files)
        return CheckResult(
            "Backend Files",
            len(found) == len(files),
            f"{len(found)}/{len(files)} present",
            score,
        )

    def check_backend_patterns(self, patterns: List[str], files: List[str]) -> CheckResult:
        if not patterns:
            return CheckResult("Backend Patterns", True, "none required", 1.0)
        if not files:
            return CheckResult("Backend Patterns", False, "no files to scan", 0.0)
        found_count = 0
        for pattern in patterns:
            for f in files:
                if self.find_pattern(f, pattern):
                    found_count += 1
                    break
        score = found_count / len(patterns) if patterns else 1.0
        return CheckResult(
            "Backend Patterns",
            found_count == len(patterns),
            f"{found_count}/{len(patterns)} patterns found",
            score,
        )

    def check_frontend_web(self, files: List[str]) -> CheckResult:
        if not files:
            return CheckResult("Web Pages", True, "none required", 1.0)
        found = [f for f in files if self.file_exists(f)]
        score = len(found) / len(files)
        return CheckResult(
            "Web Pages",
            len(found) == len(files),
            f"{len(found)}/{len(files)} present",
            score,
        )

    def check_frontend_mobile(self, files: List[str]) -> CheckResult:
        if not files:
            return CheckResult("Mobile Screens", True, "none required", 1.0)
        found = [f for f in files if self.file_exists(f)]
        score = len(found) / len(files)
        return CheckResult(
            "Mobile Screens",
            len(found) == len(files),
            f"{len(found)}/{len(files)} present",
            score,
        )

    def check_models(self, models: List[str]) -> CheckResult:
        if not models:
            return CheckResult("DB Models", True, "none required", 1.0)
        # Scan all model files for class definitions
        model_dir = self.root / "backend" / "db"
        if not model_dir.exists():
            # fallback: scan backend/models/
            model_dir = self.root / "backend" / "models"
        found_count = 0
        all_content = ""
        for p in model_dir.rglob("*.py"):
            try:
                all_content += p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                pass
        # Also scan backend/db/models.py if exists
        db_models = self.root / "backend" / "db" / "models.py"
        if db_models.exists():
            try:
                all_content += db_models.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                pass

        for m in models:
            if re.search(rf"class\s+{m}\s*\(", all_content):
                found_count += 1
        score = found_count / len(models) if models else 1.0
        return CheckResult(
            "DB Models",
            found_count == len(models),
            f"{found_count}/{len(models)} classes found",
            score,
        )

    def check_api_routes(self, routes: List[str]) -> CheckResult:
        if not routes:
            return CheckResult("API Routes", True, "none required", 1.0)
        # Scan all router files
        router_dir = self.root / "backend" / "routers"
        if not router_dir.exists():
            return CheckResult("API Routes", False, "router dir missing", 0.0)
        all_content = ""
        for p in router_dir.glob("*.py"):
            try:
                all_content += p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                pass

        found_count = 0
        for route in routes:
            # Extract just the path part (e.g., "/auth/login" from "POST /auth/login")
            path = route.split()[-1] if " " in route else route
            method = route.split()[0] if " " in route else ""
            # Look for path in router decorators
            if path in all_content:
                found_count += 1
        score = found_count / len(routes) if routes else 1.0
        return CheckResult(
            "API Routes",
            found_count == len(routes),
            f"{found_count}/{len(routes)} routes found",
            score,
        )

    def check_tests(self, tests: List[str]) -> CheckResult:
        if not tests:
            return CheckResult("Tests", True, "none required", 1.0)
        found = [t for t in tests if self.file_exists(t)]
        score = len(found) / len(tests)
        return CheckResult(
            "Tests",
            len(found) == len(tests),
            f"{len(found)}/{len(tests)} test files",
            score,
        )


# ============================================================================
# OLLAMA INTEGRATION (OPTIONAL)
# ============================================================================

class OllamaAnalyzer:
    """Uses local Ollama for semantic analysis of code vs. feature description."""

    def __init__(self, model: str = "llama3.1", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.available = self._check_available()

    def _check_available(self) -> bool:
        try:
            import urllib.request
            with urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=2) as r:
                return r.status == 200
        except Exception:
            return False

    def analyze_feature(self, feature_name: str, description: str,
                        code_sample: str) -> Tuple[float, str]:
        """
        Returns (confidence_score 0-1, analysis_text).
        Falls back to (0.5, "Ollama unavailable") if not available.
        """
        if not self.available:
            return 0.5, "Ollama unavailable — using structural scan only"

        prompt = f"""You are a code reviewer. Analyze if the following code implements
the described feature.

FEATURE: {feature_name}
DESCRIPTION: {description}

CODE SAMPLE (first 2000 chars):
{code_sample[:2000]}

Respond in JSON only:
{{"confidence": 0.0-1.0, "analysis": "brief 1-sentence assessment", "missing": "key missing element or 'none'"}}
"""
        try:
            import urllib.request
            payload = json.dumps({
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.2, "num_predict": 300},
            }).encode("utf-8")
            req = urllib.request.Request(
                f"{self.base_url}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read().decode("utf-8"))
                response = data.get("response", "{}")
                try:
                    parsed = json.loads(response)
                    conf = float(parsed.get("confidence", 0.5))
                    analysis = parsed.get("analysis", "no analysis")
                    missing = parsed.get("missing", "")
                    if missing and missing != "none":
                        analysis += f" | Missing: {missing}"
                    return max(0.0, min(1.0, conf)), analysis
                except Exception:
                    return 0.5, response[:200]
        except Exception as e:
            return 0.5, f"Ollama error: {e}"


# ============================================================================
# MAIN TRACKER
# ============================================================================

class FeatureTracker:
    """Main orchestrator — loads definitions, scans, scores, generates report."""

    def __init__(self, use_ollama: bool = False):
        self.scanner = CodebaseScanner(ROOT_DIR)
        self.ollama = OllamaAnalyzer() if use_ollama else None
        self.features: List[FeatureScore] = []
        self.definitions: Dict[str, Any] = {}

    def load_definitions(self) -> None:
        print(f"📖 Loading definitions from {DEFINITIONS_FILE}...")
        if not DEFINITIONS_FILE.exists():
            print(f"❌ Definitions file not found: {DEFINITIONS_FILE}")
            sys.exit(1)
        with open(DEFINITIONS_FILE, "r", encoding="utf-8") as f:
            self.definitions = yaml.safe_load(f)

    def scan_all_features(self) -> None:
        features_def = self.definitions.get("systems_overview", [])
        total = len(features_def)
        print(f"🔍 Scanning {total} features...\n")

        for i, feat in enumerate(features_def, 1):
            feat_id = feat.get("id", f"FEAT_{i:03d}")
            name = feat.get("name", "Unnamed Feature")
            print(f"  [{i}/{total}] {feat_id}: {name}", end="")

            score = FeatureScore(
                feature_id=feat_id,
                name=name,
                description=feat.get("description", "").strip(),
                scope=feat.get("scope", ""),
                todo_ref=feat.get("todo_ref", "—"),
                matrix_section=feat.get("matrix_section", ""),
                weight=int(feat.get("weight", 5)),
            )

            expected = feat.get("expected", {})

            # Run all checks
            backend_files = expected.get("backend_files", [])
            score.checks.append(self.scanner.check_backend_files(backend_files))
            score.checks.append(
                self.scanner.check_backend_patterns(
                    expected.get("backend_patterns", []),
                    backend_files,
                )
            )
            score.checks.append(self.scanner.check_frontend_web(expected.get("frontend_web", [])))
            score.checks.append(
                self.scanner.check_frontend_mobile(expected.get("frontend_mobile", []))
            )
            score.checks.append(self.scanner.check_models(expected.get("models", [])))
            score.checks.append(self.scanner.check_api_routes(expected.get("api_routes", [])))
            score.checks.append(self.scanner.check_tests(expected.get("tests", [])))

            # Optional: Ollama semantic analysis
            if self.ollama and self.ollama.available and backend_files:
                code_sample = ""
                for bf in backend_files[:2]:
                    content = self.scanner.read_file(bf)
                    if content:
                        code_sample += f"\n\n# --- {bf} ---\n{content}"
                if code_sample:
                    conf, analysis = self.ollama.analyze_feature(
                        name, score.description, code_sample
                    )
                    score.ai_analysis = analysis
                    # Blend AI confidence (20% weight) with structural score
                    structural = sum(c.score for c in score.checks) / len(score.checks)
                    blended = 0.8 * structural + 0.2 * conf
                    # Adjust first check to reflect blended score
                    score.checks[0].score = blended

            score.calculate()
            self.features.append(score)

            pct = int(score.raw_score * 100)
            print(f" → {score.status_emoji} {pct}%")

    def calculate_section_totals(self) -> Dict[str, Dict[str, float]]:
        """Calculate totals per matrix section."""
        sections = {
            "systems_overview": {"count": 0, "weighted_total": 0, "weighted_done": 0},
            "section_i_infrastructure": {"count": 0, "weighted_total": 0, "weighted_done": 0},
            "section_ii_customer": {"count": 0, "weighted_total": 0, "weighted_done": 0},
            "section_iii_supplier": {"count": 0, "weighted_total": 0, "weighted_done": 0},
            "section_iv_logistics": {"count": 0, "weighted_total": 0, "weighted_done": 0},
            "section_v_admin": {"count": 0, "weighted_total": 0, "weighted_done": 0},
        }

        for feat in self.features:
            # Systems overview always includes all features
            sections["systems_overview"]["count"] += 1
            sections["systems_overview"]["weighted_total"] += feat.weight
            sections["systems_overview"]["weighted_done"] += feat.weighted_score

            # Distribute to other sections based on scope
            scope_parts = [s.strip() for s in feat.scope.split("·")]
            for section_key, scope_tags in SECTION_MAPPING.items():
                if any(tag in scope_parts for tag in scope_tags):
                    sections[section_key]["count"] += 1
                    sections[section_key]["weighted_total"] += feat.weight
                    sections[section_key]["weighted_done"] += feat.weighted_score

        # Calculate percentages
        for key, data in sections.items():
            if data["weighted_total"] > 0:
                data["pct"] = (data["weighted_done"] / data["weighted_total"]) * 100
            else:
                data["pct"] = 0.0

        return sections

    def generate_markdown(self, output_path: Path) -> None:
        print(f"\n📝 Generating markdown at {output_path}...")
        sections = self.calculate_section_totals()
        lines: List[str] = []

        lines.append("# ZOZI Codebase Status Matrix — AUTO-GENERATED")
        lines.append("")
        lines.append(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Generator:** `scripts/feature_tracker.py`")
        lines.append(f"**Definitions:** `scripts/feature_definitions.yaml`")
        if self.ollama and self.ollama.available:
            lines.append(f"**AI Analysis:** Ollama `{self.ollama.model}` enabled ✅")
        else:
            lines.append("**AI Analysis:** Structural scan only (Ollama not available)")
        lines.append("")
        lines.append("> ⚠️ This file is AUTO-GENERATED. Edit `feature_definitions.yaml` to update features,")
        "> then re-run `python scripts/feature_tracker.py` to regenerate."
        lines.append("")
        lines.append("---")
        lines.append("")

        # Executive summary
        lines.append("## 📊 Executive Summary")
        lines.append("")
        lines.append("| Section | Features | Weighted Completion |")
        lines.append("|---|---|---|")
        summary_map = {
            "systems_overview": "🗂️ Systems Overview (all features)",
            "section_i_infrastructure": "🌐 Section I — System & Infrastructure",
            "section_ii_customer": "👤 Section II — Customer Features",
            "section_iii_supplier": "🏭 Section III — Supplier Panel",
            "section_iv_logistics": "🚚 Section IV — Logistor Panel",
            "section_v_admin": "👨‍💼 Section V — Admin Panel",
        }
        for key, label in summary_map.items():
            s = sections[key]
            pct = s["pct"]
            emoji = "🟢" if pct >= 90 else "🟡" if pct >= 60 else "🔴"
            lines.append(f"| {emoji} {label} | {s['count']} | **{pct:.1f}%** |")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Generate each table section
        lines.extend(self._render_systems_overview())
        lines.extend(self._render_section("section_i_infrastructure",
                                          "🌐 Section I — System & Infrastructure Features"))
        lines.extend(self._render_section("section_ii_customer",
                                          "👤 Section II — Customer Features & Systems Status"))
        lines.extend(self._render_section("section_iii_supplier",
                                          "🏭 Section III — Supplier Panel Features & Systems Status"))
        lines.extend(self._render_section("section_iv_logistics",
                                          "🚚 Section IV — Logistor (Logistics Partner) Panel Features & Systems Status"))
        lines.extend(self._render_section("section_v_admin",
                                          "👨‍💼 Section V — Admin Panel Features & Systems Status"))

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"✅ Written {len(lines)} lines to {output_path}")

    def _render_systems_overview(self) -> List[str]:
        """Render the 🗂️ Systems Overview master quick reference table."""
        lines = []
        lines.append("## 🗂️ Systems Overview — Master Quick Reference")
        lines.append("")
        lines.append("A high-level map of every major system in ZOZI, with build status,")
        "what's live, and what still needs to be built."
        lines.append("")
        lines.append("**Status key:** ✅ Complete · ⚠️ Partial / In Progress · ❌ Not Yet Built")
        lines.append("")
        lines.append("| # | System | Scope | Status | Description | % |")
        lines.append("|---|---|---|---|---|---|")

        for i, feat in enumerate(self.features, 1):
            pct = int(feat.raw_score * 100)
            # Truncate description to 120 chars
            desc = feat.description.replace("\n", " ").strip()
            if len(desc) > 140:
                desc = desc[:137] + "..."
            lines.append(
                f"| {i} | {feat.status_emoji} **{feat.name}** | {feat.scope} | "
                f"{feat.status_emoji} | {desc} | **{pct}%** |"
            )
        lines.append("")
        lines.append("---")
        lines.append("")
        return lines

    def _render_section(self, section_key: str, section_title: str) -> List[str]:
        """Render one of the 5 detailed section tables (I-V)."""
        lines = []
        lines.append(f"## {section_title}")
        lines.append("")

        # Filter features belonging to this section
        scope_tag_map = {
            "section_i_infrastructure": ["Internal", "All roles"],
            "section_ii_customer": ["Customer"],
            "section_iii_supplier": ["Supplier"],
            "section_iv_logistics": ["Logistor"],
            "section_v_admin": ["Admin"],
        }
        scope_tags = scope_tag_map.get(section_key, [])
        section_features = []
        for feat in self.features:
            scope_parts = [s.strip() for s in feat.scope.split("·")]
            if any(tag in scope_parts for tag in scope_tags):
                section_features.append(feat)

        if not section_features:
            lines.append("_No features mapped to this section._")
            lines.append("")
            lines.append("---")
            lines.append("")
            return lines

        # Table header
        lines.append(
            "| Feature | TODO Ref | Backend | Web | Mobile | Models | Routes | Tests | % |"
        )
        lines.append(
            "|---|---|---|---|---|---|---|---|---|"
        )

        for feat in section_features:
            checks_dict = {c.name: c for c in feat.checks}
            be = checks_dict.get("Backend Files")
            web = checks_dict.get("Web Pages")
            mob = checks_dict.get("Mobile Screens")
            mdl = checks_dict.get("DB Models")
            rte = checks_dict.get("API Routes")
            tst = checks_dict.get("Tests")

            def emoji_for(c: Optional[CheckResult]) -> str:
                if not c:
                    return "—"
                if c.score >= 0.95:
                    return "✅"
                if c.score > 0:
                    return "⚠️"
                return "❌"

            pct = int(feat.raw_score * 100)
            ai_note = ""
            if feat.ai_analysis and feat.ai_analysis != "Ollama unavailable — using structural scan only":
                ai_note = f" _({feat.ai_analysis[:60]})_"

            lines.append(
                f"| {feat.status_emoji} **{feat.name}**{ai_note} | {feat.todo_ref} | "
                f"{emoji_for(be)} {be.details if be else '—'} | "
                f"{emoji_for(web)} {web.details if web else '—'} | "
                f"{emoji_for(mob)} {mob.details if mob else '—'} | "
                f"{emoji_for(mdl)} {mdl.details if mdl else '—'} | "
                f"{emoji_for(rte)} {rte.details if rte else '—'} | "
                f"{emoji_for(tst)} {tst.details if tst else '—'} | "
                f"**{pct}%** |"
            )

        lines.append("")
        lines.append("---")
        lines.append("")
        return lines


# ============================================================================
# CLI
# ============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="ZOZI Feature Tracker — scans codebase and generates status matrix"
    )
    parser.add_argument(
        "--with-ollama",
        action="store_true",
        help="Enable Ollama semantic analysis (requires local Ollama running)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT),
        help=f"Output markdown path (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("  ZOZI FEATURE TRACKER — AUTOMATED CODEBASE STATUS MATRIX")
    print("=" * 70)
    print(f"  Root:        {ROOT_DIR}")
    print(f"  Definitions: {DEFINITIONS_FILE}")
    print(f"  Output:      {args.output}")
    print(f"  Ollama:      {'ENABLED' if args.with_ollama else 'disabled'}")
    print("=" * 70)
    print()

    tracker = FeatureTracker(use_ollama=args.with_ollama)
    tracker.load_definitions()
    tracker.scan_all_features()
    tracker.generate_markdown(Path(args.output))

    # Final summary
    sections = tracker.calculate_section_totals()
    print("\n" + "=" * 70)
    print("  FINAL SCORES")
    print("=" * 70)
    for key, label in {
        "systems_overview": "Systems Overview",
        "section_i_infrastructure": "Section I (Infrastructure)",
        "section_ii_customer": "Section II (Customer)",
        "section_iii_supplier": "Section III (Supplier)",
        "section_iv_logistics": "Section IV (Logistics)",
        "section_v_admin": "Section V (Admin)",
    }.items():
        pct = sections[key]["pct"]
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"  {label:<25} [{bar}] {pct:5.1f}%")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())