import hashlib
import time

from fastapi import APIRouter, File, HTTPException, status, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from pipeline import retriever


class FileResponse(BaseModel):
    file_id: str


class DocumentDB:
    def __init__(self):
        self.router = APIRouter(prefix="/files", tags=["Files"])

        # Register the upload_file route
        self.router.add_api_route("/upload_pdf", self.upload_file, methods=["POST"])
        self.router.add_api_route("/list_files", self.list_files, methods=["GET"])
        self.router.add_api_route("/get_file/{file_id}", self.get_file, methods=["GET"])
        self.router.add_api_route(
            "/delete_file/{file_id}", self.delete_file, methods=["DELETE"]
        )

    async def upload_file(self, file: UploadFile = File(...)):
        """
                ## Upload File

        This method handles the uploading of a PDF file. It performs the following operations:

        1. **File Type Validation:** Checks if the uploaded file is a PDF. If not, it raises an HTTP exception.
        2. **Content Extraction:** Uses a `retriever.Extractor` to extract content from the PDF file.
        3. **Database Storage:** Stores the extracted content in a CouchDB database.
        4. **Checksum Generation:** Computes a SHA-3-256 checksum of the stored document to ensure data integrity.
        5. **Response:** Returns a JSON response containing the result and checksum.

        ### Parameters:

        - ``file` (UploadFile): The file being uploaded. The method expects this to be a PDF file.

        ### Returns:

        - `JSONResponse`: A response object with the status code 200 and the document's details including its checksum.

        ### Raises:

        - `HTTPException`: If the file is not a PDF, an HTTP 400 exception is raised.
        """
        # Check if the uploaded file is a PDF
        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are allowed.",
            )

        ret = retriever.Extractor.from_bytes(file.file)
        doc = retriever.DocumentDB("192.168.1.77", 5984)
        docum = {
            "title": file.filename.replace(" ", "-"),
            "content": ret,
            "date": time.strftime("%Y-%m-%d-%H-%M-%S"),
        }
        res = doc.add_document(docum)
        res["checksum"] = hashlib.sha3_256(str(res).encode()).hexdigest()

        return JSONResponse(content=res, status_code=status.HTTP_200_OK)

    async def list_files(self):
        """## List Files

        Lists all the files in the CouchDB database.

        """
        files = retriever.DocumentDB("192.168.1.77", 5984).list_documents()
        return JSONResponse(
            content={"file_names": files, "amount_files": len(files)},
            status_code=status.HTTP_200_OK,
        )

    async def get_file(self, file_id):
        """## Get File

        Returns a file from the CouchDB database, using the specified `file_id`.
        If there is no valid document, the method raises an HTTP exception with the status code 404.
        """

        files = retriever.DocumentDB("192.168.1.77", 5984).list_documents()

        if file_id not in files:
            raise HTTPException(404, f"File not found. Your file ID was: {file_id}")
        file = retriever.DocumentDB("192.168.1.77", 5984).get_document(file_id)
        res = {"id": file_id, "content": file}
        return JSONResponse(content=res, status_code=status.HTTP_200_OK)

    async def delete_file(self, file_id):
        retriever.DocumentDB("192.168.1.77", 5984).delete_document(file_id)
        return JSONResponse(
            content={
                "message": f"Successfully deleted document {file_id} from CouchDB"
            },
            status_code=status.HTTP_200_OK,
        )
