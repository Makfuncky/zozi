# ========================== SESSION MANAGEMENT ==========================

import threading
from typing import Optional, Dict, Any, List


class _SessionManager:
    """Thread-safe rembg session cache with memory-aware limits."""
    _sessions: Dict[str, Any] = {}
    _disabled_models: set = set()
    _availability_cache: Dict[str, bool] = {}
    _lock = threading.Lock()
    _birefnet_globally_disabled = False
    _max_cached_sessions: int = 1
    _access_order: List[str] = []

    @classmethod
    def _adaptive_max_sessions(cls) -> int:
        try:
            available_mb = MemoryManager.get_available_memory_mb()
            if available_mb < 2048:
                return 0
            if available_mb < 4096:
                return 1
            return 1
        except Exception:
            return 1

    @classmethod
    def get_session(cls, model_name: str) -> Optional[Any]:
        cls._update_birefnet_availability()
        if model_name in cls._disabled_models:
            return None
        with cls._lock:
            cls._max_cached_sessions = cls._adaptive_max_sessions()
            if model_name in cls._availability_cache and not cls._availability_cache[model_name]:
                return None
            if model_name not in cls._sessions:
                try:
                    _ensure_rembg()
                    if new_session is None:
                        return None
                    logger.info("Loading rembg model: %s", model_name)
                    cls._sessions[model_name] = new_session(model_name)
                    cls._availability_cache[model_name] = True
                    cls._access_order.append(model_name)
                    cls._enforce_session_limit()
                except Exception as exc:
                    logger.warning("Failed to load model %s: %s", model_name, exc)
                    cls._disabled_models.add(model_name)
                    cls._availability_cache[model_name] = False
                    return None
            else:
                if model_name in cls._access_order:
                    cls._access_order.remove(model_name)
                cls._access_order.append(model_name)
            return cls._sessions[model_name]

    @classmethod
    def _enforce_session_limit(cls) -> None:
        while len(cls._sessions) > cls._max_cached_sessions:
            oldest = cls._access_order.pop(0)
            if oldest in cls._sessions:
                del cls._sessions[oldest]

    @classmethod
    def release_session(cls, model_name: str) -> None:
        with cls._lock:
            if model_name in cls._sessions:
                del cls._sessions[model_name]
            if model_name in cls._access_order:
                cls._access_order.remove(model_name)

    @classmethod
    def has_session(cls, model_name: str) -> bool:
        cls._update_birefnet_availability()
        if model_name in cls._disabled_models:
            return False
        with cls._lock:
            cls._max_cached_sessions = cls._adaptive_max_sessions()
            if model_name in cls._availability_cache and not cls._availability_cache[model_name]:
                return False
            if model_name not in cls._sessions:
                try:
                    _ensure_rembg()
                    if new_session is None:
                        cls._availability_cache[model_name] = False
                        return False
                    cls._sessions[model_name] = new_session(model_name)
                    cls._availability_cache[model_name] = True
                    cls._access_order.append(model_name)
                    cls._enforce_session_limit()
                except Exception as exc:
                    logger.debug("Model %s unavailable: %s", model_name, exc)
                    cls._disabled_models.add(model_name)
                    cls._availability_cache[model_name] = False
                    return False
            else:
                if model_name in cls._access_order:
                    cls._access_order.remove(model_name)
                cls._access_order.append(model_name)
            return True

    @classmethod
    def _update_birefnet_availability(cls) -> None:
        if cls._birefnet_globally_disabled:
            return
        try:
            available_mb = MemoryManager.get_available_memory_mb()
            if available_mb < 2048:
                logger.warning("Low available memory, disabling BiRefNet globally")
                cls._birefnet_globally_disabled = True
        except Exception:
            pass

    @classmethod
    def reset(cls) -> None:
        with cls._lock:
            cls._sessions.clear()
            cls._disabled_models.clear()
            cls._availability_cache.clear()
            cls._birefnet_globally_disabled = False
            cls._access_order.clear()

