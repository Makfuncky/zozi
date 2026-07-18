"""File upload router."""
from __future__ import annotations
import os, uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from utils.dependencies import get_current_user
from utils.config import settings
from utils.file_validation import validate_upload_image, validate_upload_document
from models import User

router = APIRouter()

ALLOWED_FOLDERS = {"products", "banners", "avatars", "documents", "suppliers"}
MAX_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

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
    filepath = os.path.join(settings.UPLOAD_DIR, folder, filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(content)
    return {"url": f"/uploads/{folder}/{filename}", "filename": filename}

