from fastapi import APIRouter, File, HTTPException, status, UploadFile
from fastapi.responses import JSONResponse


class FileUpload:
    def __init__(self):
        self.router = APIRouter(prefix="/files", tags=["files"])
        # Register the upload_file route
        self.router.add_api_route("/upload_pdf", self.upload_file, methods=[
            "GET"])

    async def upload_file(self, file: UploadFile = File(...)):
        # Check if the uploaded file is a PDF
        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are allowed."
            )

        # Here you would typically process the file, e.g., save it or parse it
        # For now, we'll just return a success message

        return JSONResponse(content={"message": "PDF uploaded successfully"}, status_code=status.HTTP_200_OK)
