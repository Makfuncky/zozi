"""rbac/dependencies.py - FastAPI gates (spec).

require_feature(...) / require_module(...) are dependency factories used by module
routers. Wiring to the resolved auth context + resolution.effective_features is
completed in the RBAC-swap phase.
"""
from fastapi import Depends, HTTPException

def require_feature(feature: str):
    def dep() -> None:
        # TODO: resolve actor/module/country and check resolution.effective_features
        return None
    return dep

def require_module(module: str):
    def dep() -> None:
        return None
    return dep
