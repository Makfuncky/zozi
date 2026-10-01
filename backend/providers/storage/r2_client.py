"""R2 (Cloudflare R2 / S3-compatible) client factory for the storage provider.

R2 exposes the S3 API so we use boto3 under the hood — only the function and
file naming change. Isolated here so ``storage_backend.py`` can import it
without a circular dependency through ``providers.storage.__init__``.
"""
from typing import Any

try:
    import boto3
    HAS_R2 = True
except ImportError:
    HAS_R2 = False
    boto3 = None  # type: ignore[assignment]


def create_r2_client(
    bucket: str,
    region: str,
    endpoint_url: str,
    access_key: str,
    secret_key: str,
) -> Any:
    """Lazily create and return a boto3 S3-compatible client (Cloudflare R2 in prod).

    R2 is S3-API compatible, so boto3 is the right client. The endpoint URL
    must point at the R2 account's S3 endpoint (e.g.
    ``https://<ACCOUNT_ID>.r2.cloudflarestorage.com``).

    When ``HAS_R2`` is False (boto3 not installed), returns ``None`` so callers
    can degrade gracefully instead of catching ImportError.
    """
    if not HAS_R2:
        return None
    import boto3

    return boto3.client(
        "s3",
        region_name=region if region not in ("", "auto") else None,
        endpoint_url=endpoint_url or None,
        aws_access_key_id=access_key or None,
        aws_secret_access_key=secret_key or None,
    )


# Backward-compatibility aliases for one minor version (ADR-027 rename sweep).
create_s3_client = create_r2_client
HAS_S3 = HAS_BOTO3 = HAS_R2