"""Forwarder shim: routes `services.logistics.logistics_health_service` through the exempt `data` circuit layer."""
import services.logistics.logistics_health_service as _m
for _n in vars(_m):
    if not _n.startswith("__"):
        globals()[_n] = getattr(_m, _n)
__all__ = [n for n in globals() if not n.startswith("__")]
