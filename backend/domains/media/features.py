"""Media domain — feature atoms (Law 4)."""

FEATURES = {
    "media.asset.upload": "Upload media assets via presigned URL",
    "media.asset.read": "Read media asset metadata and URLs",
    "media.asset.delete": "Delete media assets from object storage",
    "media.upload_session.create": "Create a new upload session",
}

__all__ = ["FEATURES"]
