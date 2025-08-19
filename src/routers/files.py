from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from src.auth.tokens import get_current_org
from src.controllers.file_controller import FileController
from src.logs.logs import logger
from src.models.response_model import FileUploadResponse

file_router = APIRouter()
file_controller = FileController()


@file_router.post("/upload-file/", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    file_type: str = Form(...),
    description: Optional[str] = Form(...),
    current_org=Depends(get_current_org),
):
    try:
        logger.info(f"The data received is: {file_type}")
        logger.info(f"The data received is: {description}")

        response = await file_controller.process_embeddings(
            current_org, file, file_type, description
        )
        if response is False:
            raise HTTPException(status_code=500, detail="Some error occurred while uploading")

        if file.filename is None:
            raise HTTPException(status_code=500, detail="Some error occurred while uploading")

        return FileUploadResponse(filename=file.filename, message="File is uploaded successfully.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
