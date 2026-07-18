"""Launcher for the standalone Zozi IP/location tracking server.

Usage:
    cd backend
    python run_location_server.py            # listens on :8005 by default
    PORT=8010 python run_location_server.py  # custom port
"""

from __future__ import annotations

import os

import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("LOCATION_PORT", "8005"))
    # Ensure the module is importable when launched directly from backend/.
    import sys

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    uvicorn.run("location_service.main:app", host="0.0.0.0", port=port, reload=False, log_level="info")

