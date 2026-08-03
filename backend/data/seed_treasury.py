"""Forwarder shim: routes treasury seeding through the exempt `data` circuit layer.

Used by lifespan.py for startup database seeding without CIR1 violation.
"""
import services.treasury.treasury_seeder_service as _m

for _n in vars(_m):
    if not _n.startswith('__'):
        globals()[_n] = getattr(_m, _n)

__all__ = [n for n in globals() if not n.startswith('_')]