"""WAL-aware SQLite backup helper.

Once ``db/database.py`` enables ``PRAGMA journal_mode=WAL``, live data can
reside in ``zozi.db-wal`` / ``zozi.db-shm`` in addition to the main file. A
plain ``shutil.copyfile(zozi.db, dst)`` therefore omits any committed-but-not-
checkpointed rows, and restoring such a copy silently drops data.

This helper checkpoints the WAL into the main database and copies the WAL/SHM
companions too, so every script backup is consistent.
"""

import datetime as _dt
import os
import shutil
import sqlite3


def backup_database(db_path: str, suffix: str = "bak") -> str:
    """Return the path of a consistent backup of ``db_path``.

    Checkpoints pending WAL frames into the main file, then copies the main
    file plus its ``-wal``/``-shm`` companions (when present).
    """
    try:
        conn = sqlite3.connect(db_path)
        try:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        finally:
            conn.close()
    except Exception:  # pragma: no cover - best-effort; copy still proceeds
        pass

    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = f"{db_path}.{suffix}_{ts}"
    shutil.copyfile(db_path, dst)
    for ext in ("-wal", "-shm"):
        comp = db_path + ext
        if os.path.exists(comp):
            shutil.copyfile(comp, dst + ext)
    return dst

