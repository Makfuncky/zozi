"""File upload router."""
from __future__ import annotations
import os, uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from utils.dependencies import get_current_user
from utils.config import settings
from utils.file_validation import validate_upload_image, validate_upload_document
from models import User
from services.storage import storage as _storage

router = APIRouter()

ALLOWED_FOLDERS = {"products", "banners", "avatars", "documents", "suppliers"}
MAX_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


class PresignedUploadRequest(BaseModel):
    folder: str
    filename: str
    content_type: str = "application/octet-stream"


class PresignedUploadResponse(BaseModel):
    url: str
    key: str
    expires_in: int


@router.post("/presign", response_model=PresignedUploadResponse)
async def presign_upload(
    payload: PresignedUploadRequest,
    current_user: User = Depends(get_current_user),
):
    if payload.folder not in ALLOWED_FOLDERS:
        raise HTTPException(400, "Invalid folder")
    ext = os.path.splitext(payload.filename)[1] or ".bin"
    filename = f"{uuid.uuid4().hex}{ext}"
    key = f"{payload.folder}/{filename}"
    url = _storage.presign_put(key, content_type=payload.content_type)
    if not url:
        raise HTTPException(400, "Presigned uploads are not available for the current storage backend")
    return PresignedUploadResponse(url=url, key=key, expires_in=getattr(_storage, "presign_ttl", 900))


@router.post("/{folder}")
async def upload_file(folder: str, file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    if folder not in ALLOWED_FOLDERS:
        raise HTTPException(400, "Invalid folder")
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(400, f"File too large (max {settings.MAX_UPLOAD_SIZE_MB}MB)")
    if folder == "documents":
        validate_upload_document(content, file.filename or "upload")
    else:
        validate_upload_image(content, file.filename or "upload")
    ext = file.filename.rsplit(".", 1)[-1] if "." in (file.filename or "") else "bin"
    filename = f"{uuid.uuid4().hex}.{ext}"
    key = f"{folder}/{filename}"
    url = _storage.save(key, content, content_type=file.content_type)
    return {"url": url, "filename": filename}

