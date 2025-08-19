from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from src.auth.tokens import get_current_org
from src.controllers.file_controller import FileController
from src.models.response_model import FileUploadResponse

file_router = APIRouter()
file_controller = FileController()


@file_router.post("/upload-file/", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...), current_org=Depends(get_current_org)):
    try:
        response = await file_controller.process_embeddings(current_org, file)
        if response is False:
            raise HTTPException(status_code=500, detail="Some error occurred while uploading")

        if file.filename is None:
            raise HTTPException(status_code=500, detail="Some error occurred while uploading")

        return FileUploadResponse(filename=file.filename, message="File is uploaded successfully.")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
