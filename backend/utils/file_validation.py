from typing import Set
"""
File content validation using magic bytes.

Relying solely on file extension or Content-Type header is insecure because
both can be trivially spoofed by an attacker. This module reads the raw bytes
at the start of the file and compares them against known "magic" signatures to
confirm the actual file type, independent of whatever the client claimed.

Supported image types: JPEG, PNG, GIF, WebP, AVIF, BMP
Supported video types: MP4, WebM
Supported document types: CSV (text/utf-8), PDF
"""
from fastapi import HTTPException

# Magic byte signatures for common file types
# Format: (start_offset, expected_bytes_prefix)
_IMAGE_MAGIC: dict[str, tuple[int, bytes]] = {
    "jpeg": (0, b"\xFF\xD8\xFF"),
    "png":  (0, b"\x89PNG\r\n\x1a\n"),
    "gif":  (0, b"GIF8"),
    # WebP: bytes 0-3 are "RIFF", bytes 8-11 are "WEBP"
    # Handled separately below.
}

_EXT_TO_ALLOWED_MIMES: dict[str, set[str]] = {
    ".jpg":  {"image/jpeg", "image/jpg"},
    ".jpeg": {"image/jpeg", "image/jpg"},
    ".png":  {"image/png"},
    ".gif":  {"image/gif"},
    ".webp": {"image/webp"},
    ".avif": {"image/avif"},
    ".bmp":  {"image/bmp", "image/x-ms-bmp"},
    ".mp4":  {"video/mp4"},
    ".webm": {"video/webm"},
    ".csv":  {"text/csv", "text/plain", "application/csv"},
    ".pdf":  {"application/pdf"},
}

# Set of extensions that must be images
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif", ".bmp"}
VIDEO_EXTENSIONS = {".mp4", ".webm"}


def _sniff_image_type(data: bytes) -> str | None:
    """Return a normalised image type string or None if not a known image."""
    if len(data) < 2:
        return None
    if data[:2] == b"BM":
        return "bmp"
    if len(data) < 12:
        return None
    if data[:3] == b"\xFF\xD8\xFF":
        return "jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:4] in (b"GIF8", b"GIF9"):
        return "gif"
    # WebP: "RIFF????WEBP"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    # AVIF: ISO BMFF with avif/avis brand
    if data[4:8] == b"ftyp" and data[8:12] in (b"avif", b"avis"):
        return "avif"
    return None


def validate_image_bytes(data: bytes, filename: str) -> None:
    """
    Raise HTTP 400 if *data* does not start with a recognised image signature.

    This check is intentionally strict: even if the extension looks right,
    non-image content is rejected.
    """
    image_type = _sniff_image_type(data)
    if image_type is None:
        raise HTTPException(
            status_code=400,
            detail=(
                f"File '{filename}' does not appear to be a valid image. "
                "Only JPEG, PNG, GIF, WebP, AVIF, and BMP files are accepted."
            ),
        )


def validate_image_extension(filename: str) -> str:
    """
    Validate that the filename has an allowed image extension.
    Returns the lowercased extension (e.g. '.jpg').
    Raises HTTP 400 on invalid extension.
    """
    import os
    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{ext}'. Allowed: {', '.join(sorted(IMAGE_EXTENSIONS))}",
        )
    return ext


def validate_upload_image(data: bytes, filename: str) -> str:
    """
    Combined extension + magic byte check for uploaded images.
    Returns the validated extension.
    Call this before writing any uploaded file to disk.
    """
    ext = validate_image_extension(filename)
    validate_image_bytes(data, filename)
    return ext


def _sniff_video_type(data: bytes) -> str | None:
    """Return a normalised video type string or None if not a known video."""
    if len(data) >= 12 and data[4:8] == b"ftyp":
        return "mp4"
    if len(data) >= 32 and data[:4] == b"\x1A\x45\xDF\xA3" and b"webm" in data[:32].lower():
        return "webm"
    return None


def validate_video_bytes(data: bytes, filename: str) -> None:
    """Raise HTTP 400 if *data* does not look like an allowed video file."""
    video_type = _sniff_video_type(data)
    if video_type is None:
        raise HTTPException(
            status_code=400,
            detail=(
                f"File '{filename}' does not appear to be a valid video. "
                "Only MP4 and WebM files are accepted."
            ),
        )


def validate_video_extension(filename: str) -> str:
    """Validate that the filename has an allowed video extension."""
    import os

    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{ext}'. Allowed: {', '.join(sorted(VIDEO_EXTENSIONS))}",
        )
    return ext


def validate_upload_video(data: bytes, filename: str) -> str:
    """Combined extension + magic byte check for uploaded videos."""
    ext = validate_video_extension(filename)
    validate_video_bytes(data, filename)
    return ext


def validate_csv_bytes(data: bytes, filename: str) -> None:
    """
    Basic sanity check for CSV uploads.
    Rejects files that start with obvious binary magic bytes.
    """
    dangerous_signatures = [
        b"\xFF\xD8\xFF",      # JPEG
        b"\x89PNG",            # PNG
        b"GIF8",               # GIF
        b"%PDF",               # PDF
        b"PK\x03\x04",        # ZIP / XLSX
        b"\xd0\xcf\x11\xe0",  # OLE2 (doc/xls)
    ]
    for sig in dangerous_signatures:
        if data[:len(sig)] == sig:
            raise HTTPException(
                status_code=400,
                detail=f"File '{filename}' does not appear to be a valid CSV.",
            )


# Documents allowed: images + PDF
_DOCUMENT_EXTENSIONS = IMAGE_EXTENSIONS | {".pdf"}


def validate_upload_document(data: bytes, filename: str) -> str:
    """
    Validate a KYC / supplier document upload (image or PDF).

    Accepts JPEG, PNG, WebP, GIF (as images) and PDF.
    Performs both extension and magic-byte checks.
    Returns the lowercased extension (e.g. '.pdf', '.jpg').
    """
    import os

    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in _DOCUMENT_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid document type '{ext}'. "
                f"Allowed: {', '.join(sorted(_DOCUMENT_EXTENSIONS))}"
            ),
        )

    if ext == ".pdf":
        if not data[:4] == b"%PDF":
            raise HTTPException(
                status_code=400,
                detail=f"File '{filename}' does not appear to be a valid PDF.",
            )
    else:
        # image validation (uses magic bytes)
        validate_image_bytes(data, filename)

    return ext

