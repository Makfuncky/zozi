"""Optional, independently-runnable audit integrations.

Each probe degrades gracefully when its dependency (Playwright stack, Ollama,
database driver, live server) is unavailable. None of them can abort the main
audit.
"""
from __future__ import annotations

__all__ = ["browser_probe", "ollama_probe", "db_probe", "load_probe"]
