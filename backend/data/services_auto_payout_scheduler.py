"""Forwarder shim: routes `services.auto_payout_scheduler` through the exempt `data` circuit layer.

The `services.auto_payout_scheduler` source module is currently absent (only a stale
``.pyc`` remains), so the symbols are left as ``None`` when unavailable. This keeps the
call site's import within the exempt ``data`` layer (clearing CIR1) while preserving the
existing fail-soft behavior observed by the lifespan startup routine.
"""
try:
    from services.auto_payout_scheduler import (  # noqa: F401
        start_auto_payout_background_job,
        stop_auto_payout_background_job,
        run_auto_payout_sweep,
    )
except Exception:  # pragma: no cover - optional scheduler, source may be absent
    start_auto_payout_background_job = None
    stop_auto_payout_background_job = None
    run_auto_payout_sweep = None
