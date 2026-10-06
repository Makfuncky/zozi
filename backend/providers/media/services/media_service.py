from __future__ import annotations

from typing import Optional
from sqlalchemy.orm import Session
from providers.media.models.media_asset import MediaAsset, UploadSession

MAX_BODY_BYTES = 10 * 1024 * 1024
MAX_QUERY_ITEMS = 100
MAX_REQUEST_SECONDS = 30


class MediaService:
    @staticmethod
    def enforce_limits(
        body_size: Optional[int] = None,
        query_count: Optional[int] = None,
        elapsed: Optional[float] = None,
    ) -> None:
        if body_size is not None and body_size > MAX_BODY_BYTES:
            raise ValueError("Request body exceeds 10 MB limit")
        if query_count is not None and query_count > MAX_QUERY_ITEMS:
            raise ValueError("Query exceeds 100 items limit")
        if elapsed is not None and elapsed > MAX_REQUEST_SECONDS:
            raise ValueError("Request time exceeds 30 s limit")

    @staticmethod
    def create_asset(
        db: Session,
        storage_key: str,
        url: str,
        content_type: Optional[str] = None,
        size_bytes: Optional[int] = None,
        country_code: Optional[str] = None,
    ) -> MediaAsset:
        MediaService.enforce_limits(body_size=size_bytes)
        asset = MediaAsset(
            storage_key=storage_key,
            url=url,
            content_type=content_type,
            size_bytes=size_bytes,
            country_code=country_code,
        )
        db.add(asset)
        db.flush()
        return asset

    @staticmethod
    def create_upload_session(
        db: Session,
        upload_token: str,
        country_code: Optional[str] = None,
    ) -> UploadSession:
        session = UploadSession(upload_token=upload_token, country_code=country_code)
        db.add(session)
        db.flush()
        return session
