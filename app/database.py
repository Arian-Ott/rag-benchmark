"""API Router for the CouchDB interface"""

import hashlib
from typing import List

from dotenv import dotenv_values
from fastapi import APIRouter, Body, File, HTTPException, status, UploadFile
from fastapi.responses import JSONResponse

from pipeline import retriever
from .models import UserCreation


class DocumentDBRouter:
    """API Router for CouchDB functions"""

    def __init__(self, rag):
        self.router = APIRouter()
        self.doc_db = self._initialize_document_db()
        self.rag = rag
        self._register_routes()

    def _initialize_document_db(self):
        env_values = dotenv_values("../.env")
        host = env_values["COUCHDB_HOST"]
        port = int(env_values["COUCHDB_PORT"])
        return retriever.DocumentDB(host=host, port=port)

    def _register_routes(self):
        self.router.add_api_route("/files/upload_pdf", self.upload_file, methods=["POST"],
            tags=["Files"], deprecated=True,
        )
        self.router.add_api_route("/files/upload_pdfs/", self.upload_files, methods=["POST"],
            tags=["Files"], deprecated=True,
        )
        self.router.add_api_route(
            "/files/list_files", self.list_files, methods=["GET"], tags=["Files"]
        )
        self.router.add_api_route(
            "/files/get_file/{file_id}", self.get_file, methods=["GET"], tags=["Files"]
        )
        self.router.add_api_route(
            "/files/delete_file/{file_id}",
            self.delete_file,
            methods=["DELETE"],
            tags=["Files"], deprecated=True,
        )
        self.router.add_api_route(
            "/db/add_user", self.create_user, methods=["PUT"], tags=["CouchDB"]
        )

    def _check_bg_task(self):
        if self.rag.bg_running:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Currently running an indexing job. Please wait a few minutes.",
            )

    async def upload_files(self, files: List[UploadFile]):
        """## Bulk upload of PDF files
        This API endpoint has been deprecated to prevent unwanted change within the datastructure. Once the university project is graded, this endpoint becomes active.

        ## Funtion
        Uploads files to the couch db
        """
        self._check_bg_task()
        return [self.doc_db.add_document(file) for file in files]

    async def upload_file(self, file: UploadFile = File(...)):
        """
        ## Upload File

        This API endpoint has been deprecated until this university project is graded.

        Handles the uploading of a PDF file. Validates the file type, extracts content,
        stores it in CouchDB, and returns the checksum.

        ### Parameters:
        - `file` (UploadFile): The PDF file to be uploaded.

        ### Returns:
        - `JSONResponse`: A response with the document's details and checksum.

        ### Raises:
        - `HTTPException`: If the file is not a PDF.
        """
        self._check_bg_task()

        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are allowed.",
            )

        res = self.doc_db.add_document(file)
        return JSONResponse(content=res, status_code=status.HTTP_200_OK)

    async def list_files(self):
        """
        ## List Files

        Lists all the files in the CouchDB database.

        ### Returns:
        - `JSONResponse`: A response with a list of file names and the total number of files.
        """
        files = self.doc_db.list_documents()
        return JSONResponse(
            content={"file_names": files, "amount_files": len(files)},
            status_code=status.HTTP_200_OK,
        )

    async def get_file(self, file_id: str):
        """
        ## Get File

        Retrieves a file from the CouchDB database using the specified `file_id`.

        ### Parameters:
        - `file_id` (str): The ID of the file to retrieve.

        ### Returns:
        - `JSONResponse`: A response with the file content.

        ### Raises:
        - `HTTPException`: If the file is not found.
        """
        files = self.doc_db.list_documents()

        if file_id not in files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found. Your file ID was: {file_id}",
            )

        file = self.doc_db.get_document(file_id)
        return JSONResponse(
            content={"id": file_id, "content": file}, status_code=status.HTTP_200_OK
        )

    async def delete_file(self, file_id: str):
        """
        ## Delete File
        This API endpoint has been deprecated until this university project is graded.
        Deletes a file from the CouchDB database using the specified `file_id`.

        ### Parameters:
        - `file_id` (str): The ID of the file to delete.

        ### Returns:
        - `JSONResponse`: A response confirming the deletion.
        """
        self._check_bg_task()
        self.doc_db.delete_document(file_id)
        return JSONResponse(
            content={
                "message": f"Successfully deleted document {file_id} from CouchDB"
            },
            status_code=status.HTTP_200_OK,
        )

    async def create_user(self, data: UserCreation = Body(...)):
        """
        ## Create User

        Creates a new user in the CouchDB database.

        ### Parameters:
        - `data` (UserCreation): The user data including username, password, and authorization.

        ### Returns:
        - `JSONResponse`: A response confirming user creation.

        ### Raises:
        - `HTTPException`: If the authorization is invalid.
        """
        env_values = dotenv_values("../.env")
        if (hashlib.sha3_512(data.authorisation.encode("utf-8")).hexdigest() != env_values[
            "COUCH_DB_ACCESS_HASH"]
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials. Abort.",
            )

        self.doc_db.create_user(
            username=data.username, password=data.password, roles=["user"]
        )
        return JSONResponse(
            content={
                "message": f"User with the username {data.username} created successfully."
            },
            status_code=status.HTTP_201_CREATED,
        )
