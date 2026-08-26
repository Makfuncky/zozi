# ========================== MEMORY MANAGEMENT (br_08) ==========================

import gc
from typing import Optional


class MemoryManager:
    """Lightweight memory management utilities (br_08)."""

    @staticmethod
    def cleanup() -> None:
        gc.collect()

    @staticmethod
    def get_available_memory_mb() -> float:
        try:
            import psutil
            return psutil.virtual_memory().available / 1024 / 1024
        except ImportError:
            return 4096

    @staticmethod
    def get_total_memory_mb() -> float:
        try:
            import psutil
            return psutil.virtual_memory().total / 1024 / 1024
        except ImportError:
            return 8192

