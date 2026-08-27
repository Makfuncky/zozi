"""S3 client factory for the storage provider.

Isolated here so ``storage_backend.py`` can import it without a circular
dependency through ``providers.storage.__init__``.
"""
from typing import Any, Optional

try:
    import boto3
    HAS_S3 = True
except ImportError:
    HAS_S3 = False
    boto3 = None  # type: ignore[assignment]


def create_s3_client(
    bucket: str,
    region: str,
    endpoint_url: str,
    access_key: str,
    secret_key: str,
) -> Any:
    """Lazily create and return a boto3 S3 client."""
    import boto3

    return boto3.client(
        "s3",
        region_name=region if region not in ("", "auto") else None,
        endpoint_url=endpoint_url or None,
        aws_access_key_id=access_key or None,
        aws_secret_access_key=secret_key or None,
    )
