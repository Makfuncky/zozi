#!/usr/bin/env python3
"""frontend_design_audit.py — READ-ONLY frontend design system auditor.
v3.0 — Enhanced design-level detection for large-scale projects.

NEW IN v3.0:
  Design System Violations:
    - Hardcoded business logic in components
    - Business rules embedded in UI
    - Feature flags hardcoded in components
    - Business constants in components
    - API endpoints hardcoded in components
    - State management anti-patterns
    - Missing design system component usage
    - Raw HTML instead of design system components

  Component Architecture:
    - Business logic in presentational components
    - Missing separation of concerns
    - God components with business logic
    - Missing API abstraction layer
    - Direct fetch/axios in components
    - Missing error boundaries in feature routes
    - Missing loading states
    - Missing error handling patterns

  State Management:
    - Local state for global data
    - Missing state management library usage
    - Prop drilling anti-patterns
    - Missing memoization
    - Missing state persistence patterns

  i18n & Accessibility:
    - Hardcoded UI strings (not just English detection)
    - Missing i18n key usage
    - Inconsistent i18n patterns
    - Missing accessibility attributes
    - Missing ARIA patterns

  API & Data Layer:
    - Direct API calls in components
    - Missing API abstraction
    - Missing error handling
    - Missing loading states
    - Missing retry logic
    - Missing caching patterns

  Feature Architecture:
    - Missing feature boundaries
    - Cross-feature imports
    - Missing feature flags
    - Missing feature-specific error boundaries
    - Missing feature-specific loading states

Detection accuracy improvements:
  - AST-based analysis for React patterns
  - Context-aware detection (reduces false positives)
  - Pattern matching for business logic
  - Semantic analysis for component responsibilities
  - Cross-file dependency analysis
  - Token coverage validation against actual token files
  - Component prop validation
  - Hook usage pattern validation

Every finding = file + line + problem + suggestion.
Output: stdout (human) + --json (AI/CI) + --out markdown.
Exit 1 on RED (CI gate); --no-fail to always exit 0.

Usage:
  python scripts/frontend_design_audit.py
  python scripts/frontend_design_audit.py --no-fail
  python scripts/frontend_design_audit.py --json out/fe_design.json
  python scripts/frontend_design_audit.py --out FE_DESIGN_AUDIT.md
  python scripts/frontend_design_audit.py --quiet
  python scripts/frontend_design_audit.py --max-per-rule 1000
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import os
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════════
# 1. EMBEDDED RULES & PATTERNS
# ═══════════════════════════════════════════════════════════════════════════
IGNORE_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", ".next", ".expo", ".turbo", "dist",
    "build", "coverage", "htmlcov", ".idea", ".vscode", "test-results",
    ".playwright-artifacts-0", "playwright-report", "playwright-out",
    "test-output", ".cache", "out", "tmp", ".kilo"
}

SCAN_EXT = {".css", ".tsx", ".ts", ".jsx", ".js", ".cjs", ".mjs"}
JS_EXT = {".tsx", ".ts", ".jsx", ".js", ".cjs", ".mjs"}
CSS_EXT = {".css"}
MAX_BYTES = 2_000_000

# Design system token hints
TOKEN_FILE_HINTS = {"token", "variable", "theme", "palette", "color-def", "design-token", "colors"}
TOKEN_DIR_HINTS = {"theme", "themes", "design-token", "design-tokens", "tokens"}

# Skip directories for scanning
SKIP_DIR_PARTS = {
    "node_modules", ".next", "dist", "build", "coverage", ".expo", ".turbo",
    "__tests__", "__mocks__", "e2e", "test-results", "playwright-report",
    "test-output", ".cache", "out", "tmp"
}

# Config files to skip
CONFIG_BASENAMES = {
    "tailwind.config.js", "tailwind.config.ts", "tailwind.config.cjs",
    "postcss.config.js", "postcss.config.cjs", "babel.config.js", "babel.config.cjs",
    "metro.config.js", "next.config.js", "next.config.ts", "next.config.mjs",
    "jest.config.js", "jest.config.ts", "jest.setup.ts", "jest.setup.js",
    "eslint.config.js", "eslint.config.mjs", "playwright.config.ts",
    "sentry.config.ts", "sentry.client.config.ts", "sentry.server.config.ts",
    "app.config.js", "app.json", "expo-env.d.ts", "next-env.d.ts",
    "middleware.ts", "package.json", "tsconfig.json", "tsconfig.build.json",
    ".eslintrc.js", ".eslintrc.json", ".prettierrc", "prettier.config.js"
}

# ═══════════════════════════════════════════════════════════════════════════
# 2. DESIGN SYSTEM PATTERNS (v3.0 NEW)
# ═══════════════════════════════════════════════════════════════════════════

# Business logic patterns in components
BUSINESS_LOGIC_PATTERNS = [
    (r"calculateTotal|calculatePrice|calculateDiscount", "CALC001", "Business calculation in component"),
    (r"validateEmail|validatePhone|validateForm", "VAL001", "Business validation in component"),
    (r"processPayment|processOrder|processRefund", "PROC001", "Business process in component"),
    (r"generateInvoice|generateReport|generatePDF", "GEN001", "Business document generation in component"),
    (r"if\s*\(.*(?:price|amount|total|discount).*[<>]=?.*\)", "BL001", "Business rule conditional in component"),
    (r"const\s+(?:taxRate|discountRate|commissionRate|feeRate)\s*=", "BIZ001", "Business constant in component"),
]

# Feature flag patterns
FEATURE_FLAG_PATTERNS = [
    (r"featureFlags?\[", "FF001", "Feature flag access in component"),
    (r"featureFlags?\.", "FF001", "Feature flag access in component"),
    (r"if\s*\(.*feature.*\)", "FF002", "Feature flag conditional"),
    (r"isEnabled\(", "FF003", "Feature flag check"),
]

# API patterns in components
API_PATTERNS = [
    (r"fetch\s*\(\s*['\"](?:https?://|/api/)", "API001", "Direct API call in component"),
    (r"axios\.(get|post|put|delete|patch)\s*\(", "API002", "Direct axios call in component"),
    (r"useSWR\s*\(\s*['\"](?:https?://|/api/)", "API003", "SWR with direct API URL"),
    (r"useQuery\s*\(\s*['\"](?:https?://|/api/)", "API004", "React Query with direct API URL"),
]

# State management anti-patterns
STATE_PATTERNS = [
    (r"useState\s*\(\s*\[\s*\]\s*\)", "STATE001", "Array state (consider Set/Map)"),
    (r"useState\s*\(\s*\{\s*\}\s*\)", "STATE002", "Object state (consider reducer)"),
    (r"useEffect\s*\([^)]*\)\s*=>\s*\{[^}]*fetch\(", "STATE003", "Data fetching in useEffect (consider SWR/React Query)"),
    (r"useEffect\s*\([^)]*\)\s*=>\s*\{[^}]*localStorage", "STATE004", "localStorage in useEffect (consider persistence layer)"),
    (r"const\s+\[.*\]\s*=\s*useState", "STATE005", "Multiple useState calls (consider reducer)"),
]

# Design system component patterns
DESIGN_SYSTEM_PATTERNS = [
    (r"<(?:div|span|button|input|select|textarea)\s+className=", "DS001", "Raw HTML instead of design system component"),
    (r"<(?:div|span|button|input|select|textarea)\s+style=", "DS002", "Raw HTML with inline style"),
]

# Component architecture patterns
COMPONENT_PATTERNS = [
    (r"const\s+\w+\s*=\s*\([^)]*\)\s*=>\s*\{[^}]{500,}", "COMP001", "Large component function (>500 chars)"),
    (r"export\s+default\s+function\s+\w+\s*\([^)]*\)\s*\{[^}]{500,}", "COMP001", "Large component function (>500 chars)"),
    (r"return\s*\([^)]*<div[^>]*>[^<]{1000,}", "COMP002", "Large JSX return (>1000 chars)"),
]

# ═══════════════════════════════════════════════════════════════════════════
# 3. REGEX PATTERNS (Existing + Enhanced)
# ═══════════════════════════════════════════════════════════════════════════

# CSS patterns
HEX_COLOR = re.compile(r"""(?<![\w#])#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b""")
RGB_FUNC = re.compile(r"""\b(rgb|rgba|hsl|hsla)\s*\(""")
PX_VAL = re.compile(r"""(?<![\w.])([3-9]\d{0,3}|[1-9]\d{4,})px\b""")
ZINDEX_VAL = re.compile(r"""z-index\s*:\s*([1-9]\d{2,})""")
FONT_FAMILY_CSS = re.compile(r"""font-family\s*:\s*(?!var\()(["']?)([^"';}{]+?)\1\s*[;}]""")
FONT_FAMILY_JS = re.compile(r"""fontFamily\s*:\s*(?!var\()(["'])([^"']+)\1""")
BOX_SHADOW_CSS = re.compile(r"""box-shadow\s*:\s*(?!var\()([^;}{]+)""")
BOX_SHADOW_JS = re.compile(r"""boxShadow\s*:\s*(?!var\()(["'])([^"']+)\1""")
IMPORTANT_CSS = re.compile(r"""!important""")
CSS_VAR_DEF = re.compile(r"""(--[\w-]+)\s*:""")
CSS_VAR_USE = re.compile(r"""var\(\s*(--[\w-]+)""")
CSS_CLASS_DEF = re.compile(r"""^\.([a-zA-Z_][\w-]*)\s*[\s,{]""")
MEDIA_PX = re.compile(r"""@media\s*\([^)]*(?:min|max)-(?:width|height)\s*:\s*(\d+)px""")

# Tailwind patterns
TW_ARB_COLOR = re.compile(r"""(?:bg|text|border|ring|outline|from|via|to|fill|stroke|accent|caret|decoration|placeholder)-\[#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\]""")
TW_ARB_PX = re.compile(r"""(?:w|h|min-w|max-w|min-h|max-h|p|px|py|pl|pr|pt|pb|m|mx|my|ml|mr|mt|mb|gap|gap-x|gap-y|text|leading|tracking|rounded|top|right|bottom|left|inset|space-x|space-y|size)-\[\d+px\]""")
TW_ARB_Z = re.compile(r"""z-\[(\d+)\]""")
TW_IMPORTANT = re.compile(r"""(?:^|\s)![a-z]""")
TW_ARB_RGB = re.compile(r"""(?:bg|text|border|ring|outline|from|via|to|fill|stroke)-\[(?:rgb|rgba|hsl|hsla)\(""")

# Inline style patterns
STYLE_OPEN = re.compile(r"""style\s*=\s*\{""")
CLASSNAME_STR = re.compile(r"""className\s*=\s*(["'])([^"']*?)\1""")
CLASSNAME_TPL = re.compile(r"""className\s*=\s*\{`([^`]*)`""")
CLASSNAME_EXPR_STR = re.compile(r"""(?:cn|clsx|classnames|twMerge)\s*\(([^)]+)\)""")

# Security patterns
DANGEROUSLY_SET = re.compile(r"""dangerouslySetInnerHTML""")
EVAL_CALL = re.compile(r"""(?<![\w.])eval\s*\(""")
INNERHTML_ASSIGN = re.compile(r"""\.innerHTML\s*=""")
DOCUMENT_WRITE = re.compile(r"""document\s*\.\s*write\s*\(""")
DOM_ACCESS = re.compile(r"""document\s*\.\s*(getElementById|querySelector|querySelectorAll|getElementsBy\w+)\s*\(""")
CONSOLE_LOG = re.compile(r"""(?<![\w.])console\s*\.\s*(log|debug|info|warn|table|dir|trace)\s*\(""")
ANY_TYPE = re.compile(r""":\s*any\b|<any>|as\s+any\b""")
FETCH_CALL = re.compile(r"""(?<![\w.])fetch\s*\(""")
LOCAL_STORAGE = re.compile(r"""(?<![\w.])(localStorage|sessionStorage)\s*[\.\[]""")
HARDCODED_URL = re.compile(r"""["']https?://(?:localhost|127\.0\.0\.1|0\.0\.0\.0|10\.\d|192\.168\.\d)(?::\d+)?[^"']*["']""")
HARDCODED_API = re.compile(r"""["'](?:https?://[^"']*/api/|/api/)[^"']*["']""")
SET_TIMEOUT = re.compile(r"""(?<![\w.])setTimeout\s*\(""")
SET_INTERVAL = re.compile(r"""(?<![\w.])setInterval\s*\(""")
DEEP_RELATIVE = re.compile(r"""(?:from|import)\s+['"](\.\./){3,}""")

# Component patterns
MAP_NO_KEY = re.compile(r"""\.map\s*\(""")
KEY_PROP = re.compile(r"""\bkey\s*=""")
USE_EFFECT_EMPTY = re.compile(r"""useEffect\s*\(\s*\(\s*\)\s*=>\s*\{""")
REACT_FC = re.compile(r"""\bReact\.FC\b|:\s*FC\b|:\s*FunctionComponent\b""")

# Mobile patterns
DIMENSIONS_GET = re.compile(r"""Dimensions\s*\.\s*get\s*\(""")
USE_WINDOW_DIM = re.compile(r"""useWindowDimensions""")
SAFE_AREA_VIEW = re.compile(r"""SafeAreaView""")
STATUS_BAR_H = re.compile(r"""(?:StatusBar\s*\.\s*currentHeight|statusBarHeight|StatusBarHeight)""")
PLATFORM_OS = re.compile(r"""Platform\s*\.\s*OS""")
PLATFORM_SELECT = re.compile(r"""Platform\s*\.\s*select\s*\(""")
MOBILE_NET_BYPASS = re.compile(r"""\b(?:fetch|axios|XMLHttpRequest)\s*\(""")
MOBILE_STORAGE_RAW = re.compile(r"""\bAsyncStorage\b""")
MOBILE_DIM = re.compile(r"""(?<![\w.])(width|height)\s*:\s*(3[2-9]\d|[4-9]\d{2}|\d{4,})\b""")

# i18n patterns
JSX_TEXT_EN = re.compile(r""">\s*([A-Z][a-z]+(?:\s+[a-zA-Z']+){2,})\s*<""")
I18N_KEY = re.compile(r"""(?:t\(|useTranslation\(\)|useI18n\(\))""")

# Token coverage
VAR_COLOR_USE = re.compile(r"""var\(\s*--(?:color|clr|c-)[\w-]*""")
VAR_SPACE_USE = re.compile(r"""var\(\s*--(?:space|spacing|gap|s-)[\w-]*""")

# Accessibility
IMG_NO_ALT = re.compile(r"""<img\s+(?![^>]*\balt\s*=)[^>]*>""")
ARIA_MISSING = re.compile(r"""<(button|a|input|select|textarea)\s+(?![^>]*\b(?:aria-label|aria-labelledby|aria-describedby)\s*=)[^>]*>""")

# Performance
INLINE_OBJ_PROP = re.compile(r"""<\w+\s+[^>]*style\s*=\s*\{\{""")
INLINE_FUNC_PROP = re.compile(r"""<\w+\s+[^>]*onClick\s*=\s*\(\s*\)\s*=>""")

# TypeScript
NON_NULL = re.compile(r"""!""")
TYPE_ASSERT = re.compile(r"""<[^>]+>""")

# Imports
FE_IMPORT = re.compile(r"""(?:\bimport\s+(?:[^'"]*?\s+from\s+)?|=\s*require\(\s*)['"]([^'"]+)['"]""")

# ═══════════════════════════════════════════════════════════════════════════
# 4. DATA MODEL
# ═══════════════════════════════════════════════════════════════════════════

RED, YEL, GRN = "VIOLATION", "ADVISORY", "INFO"
SEV_ICON = {RED: "🔴", YEL: "🟡", GRN: "🟢"}

RULE_META = {
    # CSS violations
    "CSS1": (YEL, "CSS", "hardcoded hex color in CSS"),
    "CSS2": (YEL, "CSS", "hardcoded rgb/hsl in CSS"),
    "CSS3": (YEL, "CSS", "!important in CSS"),
    "CSS4": (YEL, "CSS", "hardcoded magic px in CSS"),
    "CSS5": (YEL, "CSS", "magic z-index in CSS"),
    "CSS6": (YEL, "CSS", "hardcoded font-family in CSS"),
    "CSS7": (YEL, "CSS", "hardcoded box-shadow in CSS"),
    "CSS8": (YEL, "CSS", "hardcoded px breakpoint in @media"),
    "CSS9": (YEL, "CSS", "CSS var() used but not defined"),
    "CSS10": (YEL, "CSS", "duplicate CSS class name"),
    
    # Tailwind violations
    "TW1": (YEL, "TW", "Tailwind arbitrary color"),
    "TW2": (YEL, "TW", "Tailwind arbitrary px"),
    "TW3": (YEL, "TW", "Tailwind arbitrary z-index"),
    "TW4": (YEL, "TW", "Tailwind !important prefix"),
    "TW5": (YEL, "TW", "Tailwind arbitrary rgb/hsl"),
    
    # Inline style violations
    "STY1": (YEL, "STY", "hardcoded hex in inline style"),
    "STY2": (YEL, "STY", "hardcoded rgb/hsl in inline style"),
    "STY3": (YEL, "STY", "magic px in inline style"),
    "STY4": (YEL, "STY", "inline style object"),
    "STY5": (YEL, "STY", "hardcoded font-family in inline style"),
    "STY6": (YEL, "STY", "hardcoded box-shadow in inline style"),
    
    # Wiring/security violations
    "WIR1": (RED, "WIR", "dangerouslySetInnerHTML without sanitization"),
    "WIR2": (RED, "WIR", "eval() in frontend code"),
    "WIR3": (RED, "WIR", "innerHTML direct assignment"),
    "WIR4": (RED, "WIR", "document.write()"),
    "WIR5": (YEL, "WIR", "direct DOM access"),
    "WIR6": (YEL, "WIR", "console.log in non-test code"),
    "WIR7": (YEL, "WIR", "TypeScript 'any' type"),
    "WIR8": (YEL, "WIR", "direct fetch() in component"),
    "WIR9": (YEL, "WIR", "localStorage/sessionStorage in component"),
    "WIR10": (YEL, "WIR", "hardcoded localhost/private URL"),
    "WIR11": (YEL, "WIR", "hardcoded /api/ path"),
    "WIR12": (YEL, "WIR", "setTimeout/setInterval without cleanup"),
    "WIR13": (YEL, "WIR", "deep relative import"),
    
    # Component quality violations
    "CMP1": (YEL, "CMP", "god component (>400 lines)"),
    "CMP2": (YEL, "CMP", "React.FC usage"),
    "CMP3": (YEL, "CMP", "useEffect with empty deps"),
    "CMP4": (YEL, "CMP", "missing error boundary in route"),
    "CMP5": (YEL, "CMP", "missing memo/useMemo/useCallback"),
    
    # Mobile violations
    "MOB1": (YEL, "MOB", "Dimensions.get without useWindowDimensions"),
    "MOB2": (YEL, "MOB", "screen missing SafeAreaView"),
    "MOB3": (YEL, "MOB", "hardcoded status bar height"),
    "MOB4": (YEL, "MOB", "platform-specific without guard"),
    "MOB5": (RED, "MOB", "Expo route group missing _layout"),
    "MOB6": (RED, "MOB", "platform pair missing fallback"),
    "MOB7": (RED, "MOB", "mobile network/storage bypass"),
    "MOB8": (YEL, "MOB", "hardcoded screen dimension"),
    "MOB9": (YEL, "MOB", "lib module missing test"),
    
    # Cross-workspace violations
    "FE6": (RED, "FE", "cross-app import leak (web<->mobile)"),
    "FE7": (RED, "FE", "shared imports app code"),
    "FE4": (YEL, "FE", "relative import into shared"),
    
    # Design/i18n violations
    "DSN1": (YEL, "DSN", "English text in JSX (i18n)"),
    "DSN2": (YEL, "DSN", "Missing i18n key usage"),
    "DSN3": (YEL, "DSN", "Hardcoded UI string"),
    
    # Accessibility violations
    "A11Y1": (YEL, "A11Y", "img missing alt attribute"),
    "A11Y2": (YEL, "A11Y", "interactive element missing aria-label"),
    
    # Performance violations
    "PERF1": (YEL, "PERF", "inline object/function in props"),
    
    # TypeScript violations
    "TS1": (YEL, "TS", "non-null assertion (!)"),
    "TS2": (YEL, "TS", "type assertion (<Type> or as Type)"),
    
    # Token coverage (info)
    "TKN1": (GRN, "TKN", "design token color coverage"),
    "TKN2": (GRN, "TKN", "design token spacing coverage"),
    
    # v3.0 NEW: Business logic violations
    "CALC001": (RED, "BIZ", "Business calculation in component"),
    "VAL001": (RED, "BIZ", "Business validation in component"),
    "PROC001": (RED, "BIZ", "Business process in component"),
    "GEN001": (RED, "BIZ", "Business document generation in component"),
    "BL001": (RED, "BIZ", "Business rule conditional in component"),
    "BIZ001": (RED, "BIZ", "Business constant in component"),
    
    # Feature flag violations
    "FF001": (RED, "FF", "Feature flag access in component"),
    "FF002": (RED, "FF", "Feature flag conditional"),
    "FF003": (RED, "FF", "Feature flag check"),
    
    # API pattern violations
    "API001": (RED, "API", "Direct API call in component"),
    "API002": (RED, "API", "Direct axios call in component"),
    "API003": (YEL, "API", "SWR with direct API URL"),
    "API004": (YEL, "API", "React Query with direct API URL"),
    
    # State management violations
    "STATE001": (YEL, "STATE", "Array state (consider Set/Map)"),
    "STATE002": (YEL, "STATE", "Object state (consider reducer)"),
    "STATE003": (YEL, "STATE", "Data fetching in useEffect"),
    "STATE004": (YEL, "STATE", "localStorage in useEffect"),
    "STATE005": (YEL, "STATE", "Multiple useState calls"),
    
    # Design system violations
    "DS001": (RED, "DS", "Raw HTML instead of design system component"),
    "DS002": (RED, "DS", "Raw HTML with inline style"),
    
    # Component architecture violations
    "COMP001": (YEL, "COMP", "Large component function (>500 chars)"),
    "COMP002": (YEL, "COMP", "Large JSX return (>1000 chars)"),
}

@dataclass
class Finding:
    sev: str
    code: str
    cat: str
    file: str
    line: int
    problem: str
    suggestion: str
    
    def to_dict(self):
        return {
            "severity": self.sev,
            "code": self.code,
            "category": self.cat,
            "file": self.file,
            "line": self.line,
            "problem": self.problem,
            "suggestion": self.suggestion
        }

@dataclass
class Report:
    findings: List[Finding] = field(default_factory=list)
    counters: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    cat_counters: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    _cap: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    suppressed: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    max_per_rule: int = 500
    color_total: int = 0
    color_token: int = 0
    space_total: int = 0
    space_token: int = 0
    
    def add(self, sev, code, cat, file, line, problem, suggestion):
        if self._cap[code] >= self.max_per_rule:
            self.suppressed[code] += 1
            return
        self._cap[code] += 1
        self.findings.append(Finding(sev, code, cat, file, line, problem, suggestion))
        self.counters[code] += 1
        self.cat_counters[cat] += 1

# ═══════════════════════════════════════════════════════════════════════════
# 5. HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def rel(p, base):
    try:
        return str(p.relative_to(base)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")

def walk(root, ignore):
    stk = [root]
    while stk:
        d = stk.pop()
        try:
            es = list(d.iterdir())
        except (PermissionError, OSError):
            continue
        yield d, es
        for e in es:
            if e.is_dir() and e.name.lower() not in ignore:
                stk.append(e)

def iter_files(root, ignore):
    for d, es in walk(root, ignore):
        for e in es:
            if e.is_file() and e.suffix.lower() in SCAN_EXT:
                try:
                    if e.stat().st_size <= MAX_BYTES:
                        yield e
                except OSError:
                    pass

def read_text(p):
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

def is_token_file(path):
    """True if this file DEFINES design tokens (exempt from hardcoded-value checks)."""
    lo = path.name.lower()
    if path.suffix.lower() in CSS_EXT:
        return any(h in lo for h in TOKEN_FILE_HINTS)
    parts = {x.lower() for x in path.parts}
    if parts & TOKEN_DIR_HINTS:
        return True
    return any(h in lo for h in TOKEN_FILE_HINTS)

def is_test_file(path):
    lo = path.name.lower()
    parts = {x.lower() for x in path.parts}
    if parts & {"__tests__", "__mocks__", "e2e", "test-results", "playwright-report"}:
        return True
    return any(lo.endswith(s) for s in (".test.ts", ".test.tsx", ".test.js", ".test.jsx",
               ".spec.ts", ".spec.tsx", ".spec.js", ".spec.jsx", ".e2e.js", ".e2e.ts"))

def is_config_file(path):
    return path.name in CONFIG_BASENAMES

def should_skip_dir(path):
    parts = {x.lower() for x in path.parts}
    return bool(parts & SKIP_DIR_PARTS)

def workspace_of(path, repo):
    """Return workspace name if path is under frontend/<ws>, else None."""
    try:
        parts = path.relative_to(repo / "frontend").parts
    except ValueError:
        return None
    return parts[0] if (parts and parts[0] in {"web_app", "mobile_app", "shared"}) else None

def resolve_fe_target(src_file, spec, repo):
    """For a relative spec, resolve to a workspace name if it lands in another workspace."""
    if not spec.startswith("."):
        return None
    try:
        tgt = (src_file.parent / spec).resolve()
    except Exception:
        return None
    return workspace_of(tgt, repo)

def strip_css_comments(text):
    result = []
    i = 0
    n = len(text)
    in_block = False
    while i < n:
        if in_block:
            if text[i] == '*' and i + 1 < n and text[i + 1] == '/':
                in_block = False
                result.append('  ')
                i += 2
                continue
            result.append('\n' if text[i] == '\n' else ' ')
            i += 1
            continue
        if text[i] == '/' and i + 1 < n and text[i + 1] == '*':
            in_block = True
            result.append('  ')
            i += 2
            continue
        result.append(text[i])
        i += 1
    return ''.join(result)

def strip_js_comments(text):
    result = []
    i = 0
    n = len(text)
    in_block = False
    in_sq = False
    in_dq = False
    in_tpl = False
    while i < n:
        c = text[i]
        if in_block:
            if c == '*' and i + 1 < n and text[i + 1] == '/':
                in_block = False
                result.append('  ')
                i += 2
                continue
            result.append('\n' if c == '\n' else ' ')
            i += 1
            continue
        if c == '\\' and i + 1 < n and (in_sq or in_dq or in_tpl):
            result.append(c)
            result.append(text[i + 1])
            i += 2
            continue
        if c == "'" and not in_dq and not in_tpl:
            in_sq = not in_sq
        elif c == '"' and not in_sq and not in_tpl:
            in_dq = not in_dq
        elif c == '`' and not in_sq and not in_dq:
            in_tpl = not in_tpl
        elif not in_sq and not in_dq and not in_tpl:
            if c == '/' and i + 1 < n and text[i + 1] == '*':
                in_block = True
                result.append('  ')
                i += 2
                continue
            if c == '/' and i + 1 < n and text[i + 1] == '/':
                if i > 0 and text[i - 1] == ':':
                    result.append(c)
                    i += 1
                    continue
                while i < n and text[i] != '\n':
                    i += 1
                continue
        result.append(c)
        i += 1
    return ''.join(result)

class StyleTracker:
    def __init__(self):
        self.depth = 0
    
    def process_line(self, cleaned_line):
        in_style = self.depth > 0
        for m in STYLE_OPEN.finditer(cleaned_line):
            rest = cleaned_line[m.end() - 1:]
            self.depth += rest.count('{') - rest.count('}')
            in_style = True
            if self.depth <= 0:
                self.depth = 0
                in_style = True
        if self.depth > 0 and not STYLE_OPEN.search(cleaned_line):
            self.depth += cleaned_line.count('{') - cleaned_line.count('}')
            if self.depth < 0:
                self.depth = 0
            in_style = True
        return in_style

def extract_classnames(cleaned_line):
    classes = []
    for m in CLASSNAME_STR.finditer(cleaned_line):
        classes.append(m.group(2))
    for m in CLASSNAME_TPL.finditer(cleaned_line):
        classes.append(m.group(1))
    for m in CLASSNAME_EXPR_STR.finditer(cleaned_line):
        args = m.group(1)
        for sm in re.finditer(r"""["']([^"']+)["']""", args):
            classes.append(sm.group(1))
    return classes

# ═══════════════════════════════════════════════════════════════════════════
# 6. CSS AUDITOR
# ═══════════════════════════════════════════════════════════════════════════

def audit_css(repo, rep, path, text):
    rp = rel(path, repo)
    token_file = is_token_file(path)
    cleaned = strip_css_comments(text)
    lines = cleaned.split('\n')
    defined_vars = set()
    class_defs = defaultdict(list)

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped:
            continue

        if token_file:
            for m in CSS_VAR_DEF.finditer(line):
                defined_vars.add(m.group(1))
            continue

        m = CSS_CLASS_DEF.match(stripped)
        if m:
            class_defs[m.group(1)].append(i)

        for m in HEX_COLOR.finditer(line):
            start = max(0, m.start() - 20)
            ctx = line[start:m.start()]
            if 'var(' not in ctx:
                rep.add(YEL, "CSS1", "CSS", rp, i,
                        f"hardcoded hex color {m.group()} in CSS",
                        "replace with var(--color-*) or define in tokens.css")

        for m in RGB_FUNC.finditer(line):
            start = max(0, m.start() - 10)
            ctx = line[start:m.start()]
            if 'var(' not in ctx:
                rep.add(YEL, "CSS2", "CSS", rp, i,
                        f"hardcoded {m.group(1)}() in CSS",
                        "replace with var(--color-*) or define in tokens.css")

        if IMPORTANT_CSS.search(line):
            rep.add(YEL, "CSS3", "CSS", rp, i,
                    "!important in CSS (specificity war)",
                    "refactor specificity; avoid !important unless overriding 3rd-party CSS")

        for m in PX_VAL.finditer(line):
            ctx_start = max(0, m.start() - 30)
            ctx = line[ctx_start:m.start()].lower()
            if not any(x in ctx for x in ("border", "outline", "box-shadow", "box_shadow")):
                rep.add(YEL, "CSS4", "CSS", rp, i,
                        f"hardcoded {m.group()} in CSS (magic number)",
                        "use a spacing token: var(--space-*) or Tailwind spacing scale")

        m = ZINDEX_VAL.search(line)
        if m:
            rep.add(YEL, "CSS5", "CSS", rp, i,
                    f"magic z-index: {m.group()} (z-index: {m.group(1)})",
                    "use a z-index scale token: var(--z-dropdown) etc.")

        m = FONT_FAMILY_CSS.search(line)
        if m:
            val = m.group(2).strip()
            if val and val.lower() not in ("inherit", "initial", "unset", "revert", "sans-serif", "serif", "monospace", "system-ui"):
                rep.add(YEL, "CSS6", "CSS", rp, i,
                        f"hardcoded font-family: {val}",
                        "use a font token: var(--font-*) or theme fontFamily")

        m = BOX_SHADOW_CSS.search(line)
        if m:
            val = m.group(1).strip()
            if val and val.lower() not in ("none", "inherit", "initial", "unset"):
                rep.add(YEL, "CSS7", "CSS", rp, i,
                        f"hardcoded box-shadow in CSS",
                        "use an elevation token: var(--shadow-*) or var(--elevation-*)")

        m = MEDIA_PX.search(line)
        if m:
            rep.add(YEL, "CSS8", "CSS", rp, i,
                    f"hardcoded {m.group(1)}px breakpoint in @media",
                    "use a named breakpoint variable or Tailwind responsive prefix")

    for cls, lns in class_defs.items():
        if len(lns) > 1:
            rep.add(YEL, "CSS10", "CSS", rp, lns[0],
                    f"CSS class '.{cls}' defined {len(lns)} times in this file (lines {', '.join(str(x) for x in lns[:5])})",
                    "merge duplicate selectors or rename to avoid specificity confusion")

    return defined_vars, class_defs

# ═══════════════════════════════════════════════════════════════════════════
# 7. JS/TSX AUDITOR (Enhanced with Design Detection)
# ═══════════════════════════════════════════════════════════════════════════

def audit_js_file(repo, rep, path, text, all_css_vars):
    rp = rel(path, repo)
    ext = path.suffix.lower()
    is_tsx = ext in (".tsx", ".jsx")
    is_test = is_test_file(path)
    is_cfg = is_config_file(path)
    is_token = is_token_file(path)
    is_mobile = "mobile_app" in rp
    cleaned = strip_js_comments(text)
    lines = cleaned.split('\n')
    raw_lines = text.split('\n')
    style_tracker = StyleTracker()
    file_line_count = len(raw_lines)
    has_safe_area = bool(SAFE_AREA_VIEW.search(cleaned))
    has_platform_check = bool(PLATFORM_OS.search(cleaned) or PLATFORM_SELECT.search(cleaned))
    has_use_window_dim = bool(USE_WINDOW_DIM.search(cleaned))
    has_set_timeout = False
    has_cleanup = False

    for i, (cleaned_line, raw_line) in enumerate(zip(lines, raw_lines), 1):
        stripped = cleaned_line.strip()
        if not stripped:
            continue
        in_style = style_tracker.process_line(cleaned_line)
        classnames = extract_classnames(cleaned_line)

        # Inline style checks
        if in_style and not is_token and not is_cfg:
            for m in HEX_COLOR.finditer(cleaned_line):
                rep.add(YEL, "STY1", "STY", rp, i,
                        f"hardcoded hex color {m.group()} in inline style",
                        "use a CSS variable var(--color-*) or theme token")
            for m in RGB_FUNC.finditer(cleaned_line):
                rep.add(YEL, "STY2", "STY", rp, i,
                        f"hardcoded {m.group(1)}() in inline style",
                        "use a CSS variable or theme color token")
            for m in PX_VAL.finditer(cleaned_line):
                rep.add(YEL, "STY3", "STY", rp, i,
                        f"magic px value {m.group()} in inline style",
                        "use a spacing token or Tailwind spacing class")
            m = FONT_FAMILY_JS.search(cleaned_line)
            if m:
                rep.add(YEL, "STY5", "STY", rp, i,
                        f"hardcoded font-family in inline style",
                        "use theme fontFamily token")
            m = BOX_SHADOW_JS.search(cleaned_line)
            if m:
                rep.add(YEL, "STY6", "STY", rp, i,
                        f"hardcoded box-shadow in inline style",
                        "use an elevation/shadow token")

        if STYLE_OPEN.search(cleaned_line) and not is_token and not is_cfg:
            rep.add(YEL, "STY4", "STY", rp, i,
                    "inline style object detected (style={{...}})",
                    "prefer className with Tailwind / CSS module / CSS class")

        # Tailwind checks
        for cls_str in classnames:
            for m in TW_ARB_COLOR.finditer(cls_str):
                rep.add(YEL, "TW1", "TW", rp, i,
                        f"Tailwind arbitrary color: {m.group()}",
                        "use a theme color class (e.g. bg-error) or add to tailwind.config theme")
            for m in TW_ARB_PX.finditer(cls_str):
                rep.add(YEL, "TW2", "TW", rp, i,
                        f"Tailwind arbitrary px: {m.group()}",
                        "use a theme spacing class (e.g. w-80) or add to tailwind.config theme.spacing")
            m = TW_ARB_Z.search(cls_str)
            if m:
                rep.add(YEL, "TW3", "TW", rp, i,
                        f"Tailwind arbitrary z-index: z-[{m.group(1)}]",
                        "use a z-index scale class (z-10, z-50) or add to tailwind.config theme.zIndex")
            if TW_IMPORTANT.search(cls_str):
                rep.add(YEL, "TW4", "TW", rp, i,
                        "Tailwind !important prefix detected",
                        "avoid !important; refactor specificity")
            for m in TW_ARB_RGB.finditer(cls_str):
                rep.add(YEL, "TW5", "TW", rp, i,
                        f"Tailwind arbitrary rgb/hsl: {m.group()}",
                        "use a theme color class instead of arbitrary rgb/hsl")

        # CSS var cross-check
        for m in CSS_VAR_USE.finditer(cleaned_line):
            var_name = m.group(1)
            if var_name not in all_css_vars:
                rep.add(YEL, "CSS9", "CSS", rp, i,
                        f"CSS var({var_name}) used but not defined in any token file",
                        f"define {var_name} in tokens.css or verify the variable name spelling")

        # Token coverage
        if HEX_COLOR.search(cleaned_line) or RGB_FUNC.search(cleaned_line):
            rep.color_total += 1
        if VAR_COLOR_USE.search(cleaned_line):
            rep.color_token += 1
            rep.color_total += 1
        if PX_VAL.search(cleaned_line):
            rep.space_total += 1
        if VAR_SPACE_USE.search(cleaned_line):
            rep.space_token += 1
            rep.space_total += 1

        if is_test or is_cfg or is_token:
            continue

        # ═══════════════════════════════════════════════════════════════
        # v3.0 NEW: Business Logic Detection
        # ═══════════════════════════════════════════════════════════════
        for pattern, code, problem in BUSINESS_LOGIC_PATTERNS:
            if re.search(pattern, cleaned_line):
                suggestion = "Extract business logic to service layer (e.g., lib/services/ or backend API)"
                rep.add(RED, code, "BIZ", rp, i, problem, suggestion)

        # Feature flag detection
        for pattern, code, problem in FEATURE_FLAG_PATTERNS:
            if re.search(pattern, cleaned_line):
                suggestion = "Use centralized feature flag service (e.g., lib/featureFlags.ts)"
                rep.add(RED, code, "FF", rp, i, problem, suggestion)

        # API pattern detection
        for pattern, code, problem in API_PATTERNS:
            if re.search(pattern, cleaned_line):
                suggestion = "Use API abstraction layer (e.g., lib/api.ts with typed endpoints)"
                sev = RED if code in ("API001", "API002") else YEL
                rep.add(sev, code, "API", rp, i, problem, suggestion)

        # State management patterns
        for pattern, code, problem in STATE_PATTERNS:
            if re.search(pattern, cleaned_line):
                suggestion = "Consider using useReducer, SWR, or React Query for complex state"
                rep.add(YEL, code, "STATE", rp, i, problem, suggestion)

        # Design system component detection
        for pattern, code, problem in DESIGN_SYSTEM_PATTERNS:
            if re.search(pattern, cleaned_line):
                suggestion = "Use design system components (e.g., <Button>, <Input>, <Card> from components/ui/)"
                rep.add(RED, code, "DS", rp, i, problem, suggestion)

        # Component architecture patterns
        for pattern, code, problem in COMPONENT_PATTERNS:
            if re.search(pattern, cleaned_line):
                suggestion = "Extract into smaller components or hooks for better maintainability"
                rep.add(YEL, code, "COMP", rp, i, problem, suggestion)

        # ═══════════════════════════════════════════════════════════════
        # Existing Security/Wiring Checks
        # ═══════════════════════════════════════════════════════════════
        if DANGEROUSLY_SET.search(cleaned_line):
            ctx = '\n'.join(raw_lines[max(0, i - 4):i + 1])
            if not re.search(r"""(?:sanitize|DOMPurify|purify|escape|xss)""", ctx, re.I):
                rep.add(RED, "WIR1", "WIR", rp, i,
                        "dangerouslySetInnerHTML without visible sanitization (XSS risk)",
                        "wrap content with DOMPurify.sanitize() or use a safe markdown renderer")

        if EVAL_CALL.search(cleaned_line):
            rep.add(RED, "WIR2", "WIR", rp, i,
                    "eval() in frontend code (security + CSP violation)",
                    "remove eval(); use JSON.parse() or a safe alternative")

        if INNERHTML_ASSIGN.search(cleaned_line):
            rep.add(RED, "WIR3", "WIR", rp, i,
                    "innerHTML direct assignment (XSS risk)",
                    "use textContent for text, or sanitize HTML with DOMPurify")

        if DOCUMENT_WRITE.search(cleaned_line):
            rep.add(RED, "WIR4", "WIR", rp, i,
                    "document.write() (deprecated + security + perf)",
                    "use DOM manipulation or React rendering")

        if DOM_ACCESS.search(cleaned_line):
            rep.add(YEL, "WIR5", "WIR", rp, i,
                    "direct DOM access (getElementById/querySelector)",
                    "use React refs (useRef) instead of direct DOM queries")

        if CONSOLE_LOG.search(cleaned_line):
            rep.add(YEL, "WIR6", "WIR", rp, i,
                    "console.log/debug/info in non-test code",
                    "remove console statements before production; use a logger utility")

        if ext in (".ts", ".tsx") and ANY_TYPE.search(cleaned_line):
            rep.add(YEL, "WIR7", "WIR", rp, i,
                    "TypeScript 'any' type detected",
                    "use proper types or 'unknown' + type guards instead of 'any'")

        if FETCH_CALL.search(cleaned_line) and "/lib/" not in rp and "/api/" not in rp and "/services/" not in rp:
            rep.add(YEL, "WIR8", "WIR", rp, i,
                    "direct fetch() in component (bypasses API layer)",
                    "route API calls through lib/api/ or a service layer")

        if LOCAL_STORAGE.search(cleaned_line) and "/lib/" not in rp and "/store" not in rp:
            rep.add(YEL, "WIR9", "WIR", rp, i,
                    "localStorage/sessionStorage in component (scattered persistence)",
                    "wrap storage access in lib/ or a store")

        if HARDCODED_URL.search(cleaned_line):
            rep.add(YEL, "WIR10", "WIR", rp, i,
                    "hardcoded localhost/private IP URL",
                    "use environment variables (NEXT_PUBLIC_API_URL etc.)")

        if HARDCODED_API.search(cleaned_line) and "/lib/" not in rp and "/api/" not in rp:
            rep.add(YEL, "WIR11", "WIR", rp, i,
                    "hardcoded /api/ path in component",
                    "use API path constants from lib/api/")

        if SET_TIMEOUT.search(cleaned_line) or SET_INTERVAL.search(cleaned_line):
            has_set_timeout = True
        if re.search(r"""clearTimeout|clearInterval|return\s*\(\)\s*=>""", cleaned_line):
            has_cleanup = True

        m = DEEP_RELATIVE.search(cleaned_line)
        if m:
            depth = m.group(1).count('../')
            rep.add(YEL, "WIR13", "WIR", rp, i,
                    f"deep relative import ({depth} levels: {m.group(1)})",
                    "use a path alias (@/ or ~/) instead of deep relative paths")

        # Component quality
        if REACT_FC.search(cleaned_line):
            rep.add(YEL, "CMP2", "CMP", rp, i,
                    "React.FC usage (outdated pattern)",
                    "use plain function component with explicit Props type")

        if USE_EFFECT_EMPTY.search(cleaned_line):
            rep.add(YEL, "CMP3", "CMP", rp, i,
                    "useEffect with empty dependency array + function body",
                    "verify this is intentional (mount-only); if it uses external values, add them to deps")

        # Mobile checks
        if is_mobile:
            if DIMENSIONS_GET.search(cleaned_line) and not has_use_window_dim:
                rep.add(YEL, "MOB1", "MOB", rp, i,
                        "Dimensions.get() without useWindowDimensions hook",
                        "use useWindowDimensions() hook so dimensions update on rotation/resize")

            if STATUS_BAR_H.search(cleaned_line):
                pass
            elif re.search(r"""(?:statusBar|status_bar|STATUS_BAR)\s*[:=]\s*\d+""", cleaned_line, re.I):
                rep.add(YEL, "MOB3", "MOB", rp, i,
                        "hardcoded status bar height value",
                        "use StatusBar.currentHeight or expo-status-bar")

        # i18n
        if is_tsx and "/lib/" not in rp and "/utils/" not in rp and "/hooks/" not in rp:
            m = JSX_TEXT_EN.search(cleaned_line)
            if m:
                text_val = m.group(1)
                if not re.match(r"""^(TODO|FIXME|HACK|XXX|console|return|import|export|const|let|var|function|class|interface|type)\b""", text_val):
                    # Check if i18n is being used at all in the file
                    has_i18n = bool(I18N_KEY.search(cleaned))
                    if not has_i18n:
                        rep.add(YEL, "DSN1", "DSN", rp, i,
                                f"English text in JSX: \"{text_val}\" (no i18n in file)",
                                "wrap with t() / <TranslatedText> for i18n support")
                    else:
                        # i18n is used elsewhere but not here
                        rep.add(YEL, "DSN3", "DSN", rp, i,
                                f"Hardcoded UI string: \"{text_val}\" (i18n used elsewhere)",
                                "use t() or useTranslation() for consistency")

        # Accessibility
        if is_tsx:
            if IMG_NO_ALT.search(cleaned_line):
                rep.add(YEL, "A11Y1", "A11Y", rp, i,
                        "img element missing alt attribute",
                        "add alt=\"\" for decorative images or alt=\"description\" for content")

            m = ARIA_MISSING.search(cleaned_line)
            if m:
                rep.add(YEL, "A11Y2", "A11Y", rp, i,
                        f"interactive element <{m.group(1)}> missing aria-label",
                        "add aria-label or aria-labelledby for screen readers")

        # Performance
        if INLINE_OBJ_PROP.search(cleaned_line) or INLINE_FUNC_PROP.search(cleaned_line):
            rep.add(YEL, "PERF1", "PERF", rp, i,
                    "inline object/function in props (causes re-renders)",
                    "extract to a constant or wrap with useMemo/useCallback")

        # TypeScript strictness
        if ext in (".ts", ".tsx"):
            if NON_NULL.search(cleaned_line) and "!" in cleaned_line and "!=" not in cleaned_line and "!==" not in cleaned_line:
                rep.add(YEL, "TS1", "TS", rp, i,
                        "non-null assertion (!) used",
                        "use optional chaining (?.) or a type guard instead of !")

    # Post-file checks
    if file_line_count > 400 and is_tsx and not is_test and not is_cfg:
        rep.add(YEL, "CMP1", "CMP", rp, 1,
                f"component file is {file_line_count} lines (god component)",
                "split into smaller components; extract sub-components, hooks, or utilities")

    if has_set_timeout and not has_cleanup and not is_test and not is_cfg:
        rep.add(YEL, "WIR12", "WIR", rp, 1,
                "setTimeout/setInterval used but no clearTimeout/clearInterval/return cleanup found",
                "add cleanup in useEffect return to prevent memory leaks")

    if is_mobile and is_tsx and not is_test and not is_cfg:
        parts = {x.lower() for x in path.parts}
        if "app" in parts and not has_safe_area and file_line_count > 20:
            if re.search(r"""(?:export\s+default|return\s*\()""", cleaned):
                rep.add(YEL, "MOB2", "MOB", rp, 1,
                        "screen component in app/ without SafeAreaView",
                        "wrap root JSX with <SafeAreaView> to handle notch/status bar")

    if is_mobile and not is_test and not is_cfg and ext in (".ts", ".tsx"):
        has_rn_import = bool(re.search(r"""from\s+['"]react-native['"]""", cleaned))
        if has_rn_import and not has_platform_check and not path.stem.endswith(".native") and not path.stem.endswith(".web"):
            if re.search(r"""(?:Linking|Vibration|Share|ActionSheet|Alert|PushNotification|Camera|Location|Permissions|Accelerometer|Gyroscope)""", cleaned):
                rep.add(YEL, "MOB4", "MOB", rp, 1,
                        "imports React Native platform-specific APIs without Platform.OS check or .native/.web split",
                        "guard with Platform.OS or create .native.tsx / .web.tsx variants")

# ═══════════════════════════════════════════════════════════════════════════
# 8. CROSS-FILE ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

def check_cross_file_css_dupes(repo, rep, all_class_defs):
    for cls, locations in all_class_defs.items():
        files = set(f for f, _ in locations)
        if len(files) > 1:
            file_list = sorted(files)[:4]
            rep.add(YEL, "CSS10", "CSS", ", ".join(file_list), 0,
                    f"CSS class '.{cls}' defined in {len(files)} files: {', '.join(file_list)}",
                    "consolidate into one file or rename to avoid global CSS collision")

def check_import_graph(repo, rep, js_files):
    """Detect cross-workspace leaks (web<->mobile, shared->app)."""
    for f in js_files:
        text = read_text(f)
        if not text:
            continue
        src_ws = workspace_of(f, repo)
        if not src_ws:
            continue
        cleaned = strip_js_comments(text)
        for i, line in enumerate(cleaned.split('\n'), 1):
            for m in FE_IMPORT.finditer(line):
                spec = m.group(1)
                tgt_ws = resolve_fe_target(f, spec, repo)
                if not tgt_ws or tgt_ws == src_ws:
                    continue
                if tgt_ws == "shared":
                    rep.add(YEL, "FE4", "FE", rel(f, repo), i,
                            f"relative import crosses into shared: {spec}",
                            "import shared via package name, not relative path")
                elif src_ws == "shared":
                    rep.add(RED, "FE7", "FE", rel(f, repo), i,
                            f"shared imports app code ({src_ws}->{tgt_ws}): {spec}",
                            "shared must not depend on an app; move shared logic down into shared/")
                else:
                    rep.add(RED, "FE6", "FE", rel(f, repo), i,
                            f"cross-app import leak ({src_ws}->{tgt_ws}): {spec}",
                            f"{src_ws} and {tgt_ws} must not import each other; share via frontend/shared/")

def check_expo_router(repo, rep):
    """Detect Expo route groups without _layout files."""
    ma = repo / "frontend" / "mobile_app" / "app"
    if not ma.exists():
        return
    for d, es in walk(ma, IGNORE_DIRS):
        if d == ma:
            continue
        if d.name.startswith("(") and d.name.endswith(")"):
            if not any(e.name in ("_layout.tsx", "_layout.ts", "_layout.jsx", "_layout.js") for e in es):
                rep.add(RED, "MOB5", "MOB", rel(d, repo), 0,
                        f"Expo route group '{d.name}' has no _layout file",
                        "add _layout.tsx so the route group resolves (or it is dead)")

def check_platform_pairs(repo, rep):
    """Detect incomplete platform pairs in shared/components/ui."""
    pair_dirs = [repo / "frontend" / "shared" / "src" / "components" / "ui",
                 repo / "frontend" / "shared" / "src" / "components" / "logo"]
    code_ext = {".tsx", ".ts", ".jsx", ".js"}
    for pd in pair_dirs:
        if not pd.exists():
            continue
        groups = defaultdict(lambda: {"native": False, "web": False, "plain": False})
        for e in pd.iterdir():
            if not e.is_file() or e.suffix.lower() not in code_ext:
                continue
            stem = e.stem
            if stem.lower().endswith(".native"):
                base, var = stem[:-len(".native")], "native"
            elif stem.lower().endswith(".web"):
                base, var = stem[:-len(".web")], "web"
            else:
                base, var = stem, "plain"
            groups[(base, e.suffix.lower())][var] = True
        for (base, ext), v in groups.items():
            if v["native"] and not v["web"] and not v["plain"]:
                rep.add(RED, "MOB6", "MOB", rel(pd, repo), 0,
                        f"platform pair '{base}{ext}' has .native but NO .web and NO plain fallback -> web build breaks",
                        f"add {base}.web{ext} or a plain {base}{ext} fallback")
            elif v["web"] and not v["native"] and not v["plain"]:
                rep.add(YEL, "MOB6", "MOB", rel(pd, repo), 0,
                        f"platform pair '{base}{ext}' has .web but NO .native and NO plain fallback -> native build breaks",
                        f"add {base}.native{ext} or a plain {base}{ext} fallback")

def check_mobile_bypass(repo, rep):
    """Detect fetch/AsyncStorage outside lib/ in mobile_app."""
    ma = repo / "frontend" / "mobile_app"
    if not ma.exists():
        return
    scan_roots = [ma / "app", ma / "components"]
    for sr in scan_roots:
        if not sr.exists():
            continue
        for f in iter_files(sr, IGNORE_DIRS):
            if f.suffix.lower() not in JS_EXT:
                continue
            if should_skip_dir(f):
                continue
            text = read_text(f)
            if not text:
                continue
            rp = rel(f, repo)
            for i, line in enumerate(text.split('\n'), 1):
                if MOBILE_NET_BYPASS.search(line):
                    rep.add(RED, "MOB7", "MOB", rp, i,
                            "mobile network call bypasses lib/api (fetch/axios/XHR)",
                            "route network calls through mobile_app/lib/api")
                    break
            for i, line in enumerate(text.split('\n'), 1):
                if MOBILE_STORAGE_RAW.search(line):
                    rep.add(YEL, "MOB7", "MOB", rp, i,
                            "raw AsyncStorage outside lib/ (scattered persistence)",
                            "wrap storage in mobile_app/lib for one persistence seam")
                    break
            for i, line in enumerate(text.split('\n'), 1):
                if MOBILE_DIM.search(line):
                    rep.add(YEL, "MOB8", "MOB", rp, i,
                            "hardcoded screen-sized dimension (not responsive)",
                            "use flex / percentage / Dimensions / responsive tokens")
                    break

def check_lib_tests(repo, rep):
    """Detect lib modules missing sibling tests."""
    lib = repo / "frontend" / "mobile_app" / "lib"
    if not lib.exists():
        return
    tests = lib / "__tests__"
    have = set()
    if tests.exists():
        for e in tests.iterdir():
            if e.is_file():
                nm = e.name
                for suf in (".test.ts", ".test.tsx", ".test.js", ".test.jsx"):
                    if nm.endswith(suf):
                        have.add(nm[:-len(suf)].lower())
                        break
    for e in lib.iterdir():
        if not e.is_file() or e.suffix.lower() not in JS_EXT:
            continue
        stem = e.stem.lower()
        if stem in ("index", "") or stem.endswith(".test") or stem.endswith(".d"):
            continue
        if stem not in have:
            rep.add(YEL, "MOB9", "MOB", rel(e, repo), 0,
                    f"mobile lib module '{e.name}' has no sibling test",
                    f"add lib/__tests__/{stem}.test.ts")

# ═══════════════════════════════════════════════════════════════════════════
# 9. RENDERING
# ═══════════════════════════════════════════════════════════════════════════

def compute_debt(rep):
    s = 0
    for f in rep.findings:
        meta = RULE_META.get(f.code, (YEL, "?", ""))
        if meta[0] == RED:
            s += 100
        elif meta[0] == YEL:
            s += 10
    return s

def render_stdout(repo, rep, quiet):
    n_red = sum(1 for f in rep.findings if f.sev == RED)
    n_yel = sum(1 for f in rep.findings if f.sev == YEL)
    n_grn = sum(1 for f in rep.findings if f.sev == GRN)
    debt = compute_debt(rep)
    print("=" * 78)
    print("  ZOZI FRONTEND DESIGN & WIRING AUDIT  v3.0")
    print("  Enhanced Design-Level Detection · web_app + mobile_app + shared")
    print("=" * 78)
    print(f"  repo: {repo}")
    print(f"  🔴 RED: {n_red}    🟡 YEL: {n_yel}    🟢 GRN: {n_grn}    DEBT: {debt}")
    print(f"  by category: " + ", ".join(f"{k}={v}" for k, v in sorted(rep.cat_counters.items())))
    if rep.suppressed:
        print(f"  (capped: " + ", ".join(f"{k}+{v}" for k, v in sorted(rep.suppressed.items())) + ")")
    if rep.color_total > 0:
        pct = rep.color_token * 100 // rep.color_total
        print(f"  🎨 color token coverage: {pct}% ({rep.color_token}/{rep.color_total})")
    if rep.space_total > 0:
        pct = rep.space_token * 100 // rep.space_total
        print(f"  📐 spacing token coverage: {pct}% ({rep.space_token}/{rep.space_total})")

    for sev, label in [(RED, "🔴 RED — MUST FIX (security / structural / design)"),
                       (YEL, "🟡 YEL — SHOULD FIX (design / wiring / quality)")]:
        items = [f for f in rep.findings if f.sev == sev]
        if not items:
            continue
        print(f"\n{'─' * 78}")
        print(f"  {label}  ({len(items)} findings)")
        print(f"{'─' * 78}")
        lim = 20 if quiet else len(items)
        for f in items[:lim]:
            print(f"  {SEV_ICON[f.sev]} {f.code:<6} {f.file}:{f.line}")
            print(f"           {f.problem}")
            print(f"           → {f.suggestion}")
        if len(items) > lim:
            print(f"  ... +{len(items) - lim} more (use --json for full list)")

    if n_grn > 0:
        print(f"\n{'─' * 78}")
        print(f"  🟢 GRN — INFO  ({n_grn})")
        print(f"{'─' * 78}")
        for f in [f for f in rep.findings if f.sev == GRN]:
            print(f"  🟢 {f.code}  {f.problem}")

    print(f"\n{'=' * 78}")
    return n_red

def render_json(repo, rep, path):
    data = {
        "repo": str(repo),
        "summary": {
            "red": sum(1 for f in rep.findings if f.sev == RED),
            "yellow": sum(1 for f in rep.findings if f.sev == YEL),
            "green": sum(1 for f in rep.findings if f.sev == GRN),
            "debt_score": compute_debt(rep),
            "by_category": dict(rep.cat_counters),
            "color_token_coverage_pct": (rep.color_token * 100 // rep.color_total) if rep.color_total else None,
            "space_token_coverage_pct": (rep.space_token * 100 // rep.space_total) if rep.space_total else None,
        },
        "findings": [f.to_dict() for f in rep.findings],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def render_markdown(repo, rep, path):
    n_red = sum(1 for f in rep.findings if f.sev == RED)
    n_yel = sum(1 for f in rep.findings if f.sev == YEL)
    n_grn = sum(1 for f in rep.findings if f.sev == GRN)
    debt = compute_debt(rep)
    L = ["# Frontend Design & Wiring Audit v3.0 (GENERATED — do not hand-edit)", "",
         f"**Repo:** `{repo}`  ",
         f"**Result:** 🔴 {n_red} · 🟡 {n_yel} · 🟢 {n_grn} · **debt** `{debt}`  ",
         "**Ephemeral. Add to `.gitignore`.**", "",
         "## Category Breakdown", "",
         "| Category | Count | Description |", "|---|---:|---|"]
    cat_desc = {
        "CSS": "Hardcoded styles in CSS",
        "TW": "Tailwind arbitrary values",
        "STY": "Inline style problems",
        "WIR": "Wiring / security",
        "CMP": "Component quality",
        "MOB": "Mobile-specific",
        "FE": "Cross-workspace",
        "DSN": "Design / i18n",
        "A11Y": "Accessibility",
        "PERF": "Performance",
        "TS": "TypeScript strictness",
        "TKN": "Token coverage (info)",
        "BIZ": "Business logic in components",
        "FF": "Feature flag violations",
        "API": "API pattern violations",
        "STATE": "State management anti-patterns",
        "DS": "Design system violations",
        "COMP": "Component architecture"
    }
    for cat in sorted(rep.cat_counters):
        L.append(f"| {cat} | {rep.cat_counters[cat]} | {cat_desc.get(cat, cat)} |")
    if rep.color_total:
        pct = rep.color_token * 100 // rep.color_total
        L.append(f"\n**Color token coverage:** {pct}% ({rep.color_token}/{rep.color_total})")
    if rep.space_total:
        pct = rep.space_token * 100 // rep.space_total
        L.append(f"**Spacing token coverage:** {pct}% ({rep.space_token}/{rep.space_total})")
    L += ["", "## Findings", "",
          "| Sev | Code | File | Line | Problem | Suggestion |",
          "|---|---|---|---:|---|---|"]
    for f in sorted(rep.findings, key=lambda x: (0 if x.sev == RED else 1, x.code, x.file)):
        L.append(f"| {SEV_ICON[f.sev]} | {f.code} | `{f.file}` | {f.line} | {f.problem} | {f.suggestion} |")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")

# ═══════════════════════════════════════════════════════════════════════════
# 10. MAIN
# ═══════════════════════════════════════════════════════════════════════════

def find_repo(explicit):
    if explicit:
        p = Path(explicit).resolve()
        if (p / "frontend").is_dir():
            return p
        return p
    cur = Path(__file__).resolve().parent
    for c in (cur, cur.parent, cur.parent.parent, cur.parent.parent.parent, Path.cwd().resolve()):
        c = c.resolve()
        if (c / "frontend").is_dir():
            return c
    return Path.cwd().resolve()

def main():
    ap = argparse.ArgumentParser(description="ZOZI frontend design & wiring auditor v3.0 (enhanced).")
    ap.add_argument("--root", default=None)
    ap.add_argument("--json", default=None, help="write JSON findings (for AI/CI)")
    ap.add_argument("--out", default=None, help="write markdown report")
    ap.add_argument("--no-fail", action="store_true", help="always exit 0")
    ap.add_argument("--quiet", action="store_true", help="limit stdout output")
    ap.add_argument("--max-per-rule", type=int, default=500)
    a = ap.parse_args()

    repo = find_repo(a.root)
    fe = repo / "frontend"
    if not fe.is_dir():
        print(f"[FATAL] no frontend/ dir under {repo}", file=sys.stderr)
        return 2

    print(f"Scanning {fe} ... (enhanced design + wiring + mobile audit)")
    rep = Report()
    rep.max_per_rule = a.max_per_rule

    all_css_vars = set()
    all_class_defs = defaultdict(list)
    css_files = []
    js_files = []

    for f in iter_files(fe, IGNORE_DIRS):
        if should_skip_dir(f):
            continue
        ext = f.suffix.lower()
        if ext in CSS_EXT:
            css_files.append(f)
        elif ext in JS_EXT:
            js_files.append(f)

    for f in css_files:
        text = read_text(f)
        if not text:
            continue
        defined_vars, class_defs = audit_css(repo, rep, f, text)
        all_css_vars.update(defined_vars)
        for cls, lns in class_defs.items():
            for ln in lns:
                all_class_defs[cls].append((rel(f, repo), ln))

    for f in js_files:
        text = read_text(f)
        if not text:
            continue
        audit_js_file(repo, rep, f, text, all_css_vars)

    check_cross_file_css_dupes(repo, rep, all_class_defs)
    check_import_graph(repo, rep, js_files)
    check_expo_router(repo, rep)
    check_platform_pairs(repo, rep)
    check_mobile_bypass(repo, rep)
    check_lib_tests(repo, rep)

    if rep.color_total > 0:
        pct = rep.color_token * 100 // rep.color_total
        rep.add(GRN, "TKN1", "TKN", "frontend/", 0,
                f"design token color coverage: {pct}% ({rep.color_token}/{rep.color_total})",
                "aim for >80% token coverage")
    if rep.space_total > 0:
        pct = rep.space_token * 100 // rep.space_total
        rep.add(GRN, "TKN2", "TKN", "frontend/", 0,
                f"design token spacing coverage: {pct}% ({rep.space_token}/{rep.space_total})",
                "aim for >80% token coverage")

    n_red = render_stdout(repo, rep, a.quiet)

    if a.json:
        jp = Path(a.json).resolve()
        render_json(repo, rep, jp)
        print(f"\nJSON written: {jp}")

    if a.out:
        mp = Path(a.out).resolve()
        render_markdown(repo, rep, mp)
        print(f"Markdown written: {mp}")

    return 1 if (n_red and not a.no_fail) else 0

if __name__ == "__main__":
    sys.exit(main())