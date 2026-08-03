"""Forwarder shim: exposes the `services.commission_engine` submodule via the exempt `data` layer.

Unlike content-re-export shims, this exposes the submodule object itself so that
``from services import commission_engine as _x`` (submodule access) keeps working.
"""
import services.commission_engine as commission_engine
__all__ = ["commission_engine"]
