from typing import Dict, Optional
from fastapi import APIRouter, Depends, File, UploadFile

from ..models.api_model import APIResponseModel
from ..models.auth_model import UserPayload
from ..services.file_service import FileService
from ..utils.security import get_current_user

router = APIRouter(
    prefix = "/api/file",
    tags = ["file"]
)

file_service = FileService()


@router.post("/upload", response_model = APIResponseModel[Optional[Dict[str, str]]])
async def upload_file(
    file: UploadFile = File(...),
    current_user: UserPayload = Depends(get_current_user)
):
    file_bytes = await file.read()
    return file_service.upload_file(
        file_bytes = file_bytes,
        original_filename = file.filename or "uploaded_file",
        content_type = file.content_type or "application/octet-stream"
    )

