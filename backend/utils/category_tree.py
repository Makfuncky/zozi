"""Category materialized-path helpers (Phase 3a).

We use a **materialized path** rather than nested-set: category depth is shallow
(<=5) and changes rarely, while nested-set forces a full renumber on every insert.

``path`` is derived from ``parent_id`` and stored redundantly:
    top-level id=1        -> "/1/"
    child id=15 of 1      -> "/1/15/"
    grandchild id=42      -> "/1/15/42/"

``depth`` = number of ancestors.

Sub-tree queries use a LIKE on the leading path, e.g. descendants of id=1:
    WHERE path LIKE '/1/%'
No recursive CTE required.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from models import Category


def _chain_for(category: Category, by_id: dict[int, Category]) -> list[str]:
    """Return the ancestor id chain (root-first) for ``category``."""
    chain: list[str] = []
    guard = 0
    cur = category.parent_id
    while cur and guard < 64:
        chain.append(str(cur))
        node = by_id.get(cur)
        if node is None:
            break
        cur = node.parent_id
        guard += 1
    chain.reverse()
    return chain


def compute_category_path(category: Category, by_id: dict[int, Category]) -> tuple[str, int]:
    """Compute (path, depth) for a single category.

    ``path`` always includes the category's own id. ``depth`` is the number of
    ancestors (0 for a top-level category).
    """
    chain = _chain_for(category, by_id)
    chain.append(str(category.id))
    path = "/" + "/".join(chain) + "/"
    return path, len(chain) - 1


def rebuild_category_paths(db: Session) -> int:
    """Recompute ``path``/``depth`` for every category from ``parent_id``.

    Safe to call after any create/move. The catalog is small, so a full rebuild
    is simpler and less error-prone than incremental maintenance.
    """
    cats = db.query(Category).all()
    by_id = {c.id: c for c in cats}
    updated = 0
    for c in cats:
        # Repair dangling parent references before computing the path.
        if c.parent_id is not None and c.parent_id not in by_id:
            c.parent_id = None
        path, depth = compute_category_path(c, by_id)
        if c.path != path or c.depth != depth:
            c.path = path
            c.depth = depth
            updated += 1
    db.flush()
    return updated


def category_subtree_ids(category_id: int, db: Session) -> list[int]:
    """Return ids of all descendants of ``category_id`` (excludes the root)."""
    # Unanchored, segment-safe match: a nested path always begins with the
    # root id, so we cannot anchor with ``/id/%`` (SQLite LIKE is anchored to the
    # string start). ``%/id/%`` matches any path containing the ``/id/`` segment.
    pattern = f"%/{int(category_id)}/%"
    rows = (
        db.query(Category.id)
        .filter(Category.path.like(pattern))
        .filter(Category.id != int(category_id))
        .all()
    )
    return [r[0] for r in rows]


def category_subtree_ids_inclusive(category_id: int, db: Session) -> list[int]:
    """Return ids of the category and all of its descendants."""
    ids = category_subtree_ids(category_id, db)
    ids.append(int(category_id))
    return ids

