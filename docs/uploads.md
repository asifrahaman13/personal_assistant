# File Router API

Handles file uploads and processing.

## Endpoints

### POST `/upload-file/`
- **Description:** Upload a file and process embeddings.
- **Form Data:**
  - `file`: File to upload
  - `file_type`: Type of the file
  - `description`: Optional description
- **Auth:** Requires organization authentication
- **Response:** `FileUploadResponse`
  - `filename`: Name of the uploaded file
  - `message`: Status message
- **Errors:** Returns HTTP 500 on failure