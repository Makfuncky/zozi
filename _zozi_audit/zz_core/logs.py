"""Run logging: JSONL streams, checkpoint state, run metadata."""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path


class RunLog:
    def __init__(self, out_dir: Path, run_id: str):
        self.dir = Path(out_dir) / "logs"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id
        self.started = time.time()
        self._handles: dict[str, object] = {}

    # -- paths -------------------------------------------------------------- #
    def path(self, name: str) -> Path:
        return self.dir / name

    # -- metadata ----------------------------------------------------------- #
    def run_metadata(self, ctx, extra: dict | None = None) -> dict:
        meta = {
            "run_id": self.run_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "root": str(ctx.root),
            "fast": ctx.fast,
            "workers": ctx.workers,
            "options": {k: v for k, v in ctx.options.items() if k != "dsn"},
            "file_counts": {
                "python": len(ctx.py_files),
                "typescript": len(ctx.ts_files),
                "all": len(ctx.all_files),
            },
        }
        if extra:
            meta.update(extra)
        self.write("run.json", meta)
        return meta

    # -- generic writers ----------------------------------------------------- #
    def write(self, name: str, data) -> None:
        path = self.path(name)
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    def append_jsonl(self, name: str, rows) -> int:
        path = self.path(name)
        count = 0
        with path.open("a", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, default=str) + "\n")
                count += 1
        return count

    def write_jsonl(self, name: str, rows) -> int:
        path = self.path(name)
        count = 0
        with path.open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, default=str) + "\n")
                count += 1
        return count

    # -- checkpoint ---------------------------------------------------------- #
    def checkpoint(self, phase: str, phase_number: int, files_processed: int,
                   findings_written: int, next_file: str = "",
                   pass_no: int = 2, run_number: int = 1) -> None:
        data = {
            "phase": phase,
            "phase_number": phase_number,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "files_processed": files_processed,
            "findings_written": findings_written,
            "next_file": next_file or None,
            "pass": pass_no,
            "run_number": run_number,
            "run_id": self.run_id,
        }
        self.write("checkpoint.json", data)

    def load_checkpoint(self) -> dict:
        path = self.path("checkpoint.json")
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def clear_checkpoint(self) -> None:
        path = self.path("checkpoint.json")
        if path.exists():
            try:
                path.unlink()
            except Exception:
                pass

    # -- tool ledger ---------------------------------------------------------- #
    def write_tool_ledger(self, tools: dict) -> None:
        rows = []
        for name, res in (tools or {}).items():
            rows.append({
                "name": name,
                "cmd": getattr(res, "cmd", ""),
                "status": getattr(res, "status", "?"),
                "exit_code": getattr(res, "exit_code", None),
                "duration_s": getattr(res, "duration_s", 0),
                "skipped_reason": getattr(res, "skipped_reason", ""),
                "stderr_tail": getattr(res, "stderr_tail", "")[:4000],
            })
        self.write("tool_ledger.json", rows)
