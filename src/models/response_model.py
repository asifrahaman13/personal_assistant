from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    filename: str
    message: str
