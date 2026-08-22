"""Re-export shim for ``infrastructure.security.key_rotation``.

The canonical implementation now lives at ``domains._key_rotation`` (neutral
platform-utility home, consistent with ``domains._seed`` / ``_async_workers`` /
``_image_tools``). Retained as a sanctioned re-export shim (P6 single-source
pattern, no-delete policy) so any legacy importer keeps resolving with zero
edits. P6 AST raw count is a backlog signal, not a per-edit gate (see RESOLVER.md §5).
"""
from domains._key_rotation import *  # noqa: F401,F403
# Explicit re-export of private symbols that downstream shims import by name.
# `import *` excludes underscore-prefixed names, which broke the
# `infrastructure.utils.key_rotation` shim's `from ... import _build_registry`.
# Re-exporting them here keeps the shim chain intact (Law-1 sanctioned bridge).
from domains._key_rotation import (  # noqa: F401
    logger,
    BATCH_SIZE,
    _build_registry,
    rotate_encryption_key,
)
