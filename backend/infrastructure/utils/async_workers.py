"""Re-export shim for ``infrastructure.utils.async_workers``.

The canonical implementation now lives at ``domains._async_workers`` (neutral
platform-utility home, consistent with ``domains._seed`` / ``_key_rotation`` /
``_image_tools``). Retained as a sanctioned re-export shim (P6 single-source
pattern, no-delete policy) so any legacy importer keeps resolving with zero
edits. P6 AST raw count is a backlog signal, not a per-edit gate (see RESOLVER.md §5).
"""
from domains._async_workers import *  # noqa: F401,F403
