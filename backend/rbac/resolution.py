"""rbac/resolution.py - effective feature-set resolution (spec).

Merges role defaults + DB grants + per-user overrides + country scope, expanding
wildcards against the catalog.
"""
from typing import Iterable, Optional, Set

def expand_wildcards(features: Iterable[str], catalog: dict) -> Set[str]:
    out: Set[str] = set()
    for f in features:
        if f == "*":
            out.update(catalog.keys())
        elif f.endswith(".*"):
            prefix = f[:-2]
            out.update(k for k in catalog if k.startswith(prefix))
        else:
            out.add(f)
    return out

def effective_features(
    role_features: Iterable[str] = (),
    db_grants: Iterable[str] = (),
    overrides: Iterable[str] = (),
    catalog: Optional[dict] = None,
) -> Set[str]:
    feats = set(role_features) | set(db_grants) | set(overrides)
    return expand_wildcards(feats, catalog or {})
