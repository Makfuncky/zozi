"""S3 client factory for the storage provider.

Isolated here so ``storage_backend.py`` can import it without a circular
dependency through ``providers.storage.__init__``.
"""
from typing import Any, Optional

try:
    import boto3
    HAS_BOTO3 = True
    HAS_S3 = True
except ImportError:
    HAS_BOTO3 = False
    HAS_S3 = False
    boto3 = None  # type: ignore[assignment]


def create_s3_client(
    bucket: str,
    region: str,
    endpoint_url: str,
    access_key: str,
    secret_key: str,
) -> Any:
    """Lazily create and return a boto3 S3 client.
    
    Returns None when boto3 is not installed (Law 125: graceful degradation).
    """
    if not HAS_S3 or not HAS_BOTO3 or boto3 is None:
        return None
    return boto3.client(
        "s3",
        region_name=region if region not in ("", "auto") else None,
        endpoint_url=endpoint_url or None,
        aws_access_key_id=access_key or None,
        aws_secret_access_key=secret_key or None,
    )


def health_check() -> dict[str, Any]:
    return {
        "status": "ok" if HAS_S3 else "unavailable",
        "provider": "s3",
        "module": __name__,
        "has_s3": HAS_S3,
        "has_boto3": HAS_BOTO3,
    }


__all__ = ["create_s3_client", "HAS_S3", "HAS_BOTO3", "health_check"]
