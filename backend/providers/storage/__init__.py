"""Storage Provider
================
Centralises the S3/boto3 (and AWS SSM) client creation so services no longer
import boto3 directly. Object backends (LocalStorage / S3Storage) and the public
``StorageBackend`` contract stay in the service layer; only the SDK call moves
here, mirroring the pattern used for other external integrations.
"""
from typing import Any, Optional


def create_s3_client(
    bucket: str,
    region: str,
    endpoint_url: str,
    access_key: str,
    secret_key: str,
) -> Any:
    """Lazily create and return a boto3 S3 client.

    Mirrors a local ``import boto3`` so the dependency stays optional — an
    ImportError is raised (and surfaces to the caller) when boto3 is absent.
    """
    import boto3

    return boto3.client(
        "s3",
        region_name=region if region not in ("", "auto") else None,
        endpoint_url=endpoint_url or None,
        aws_access_key_id=access_key or None,
        aws_secret_access_key=secret_key or None,
    )


def create_ssm_client(region: str) -> Any:
    """Lazily create and return a boto3 SSM client for secrets resolution.

    Keeps the AWS SDK import out of ``infrastructure.utils.config``; raises ImportError when
    boto3 is absent.
    """
    import boto3

    return boto3.client("ssm", region_name=region or None)


__all__ = ["create_s3_client", "create_ssm_client"]
