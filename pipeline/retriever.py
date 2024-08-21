"""Module with all classes related to retrieving data from databases or PDFs."""

import base64
import hashlib
import os
import time
import zlib

import requests as re
from dotenv import dotenv_values
from fastapi import HTTPException
from pypdf import errors, PdfReader
from tqdm import tqdm


class DocumentDB:
    """Handles operations with CouchDB for storing and retrieving documents."""

    def __init__(self, host: str, port: int):
        """Initialize the DocumentDB with the specified host and port."""
        self.secrets = dotenv_values("../.env")
        self._user = self._get_env_variable("COUCH_DB_USER")
        self._password = self._get_env_variable("COUCH_DB_SECRET")
        self.host = host
        self.port = port
        self.url = self._construct_url()

    def _get_env_variable(self, key: str) -> str:
        try:
            return self.secrets[key]
        except KeyError as e:
            raise Exception(f"Missing environment variable: {key}") from e

    def _construct_url(self) -> str:
        """Construct the appropriate CouchDB URL based on the environment."""
        if bool(self.secrets.get("PROD")):
            return "https://couch-db.arianott.com"
        return f"http://{self.host}:{self.port}"

    def add_document(self, document) -> dict:
        """
        Adds a document to the CouchDB.

        :param document: Document file to be added to the database.
        :return: Meta-information about the added document.
        """
        try:
            doc_info = self._prepare_document(document)
            response = self._upload_document(doc_info)
            response.raise_for_status()
            return self._construct_response(doc_info)
        except re.RequestException as e:
            raise HTTPException(status_code=500, detail=str(e))

    def _prepare_document(self, document) -> dict:
        """Prepare document metadata and content for storage."""
        name = document.filename.replace(",", "-").replace(" ", "-")
        content = Extractor.from_bytes(document.file)
        compressed_content = base64.b64encode(zlib.compress(content.encode("utf-8"), 9)).decode("utf-8")

        return {
            "title": name,
            "content": compressed_content,
            "date": time.strftime("%Y-%m-%d-%H-%M-%S"),
            "checksum": hashlib.sha3_256(compressed_content.encode("utf-8")).hexdigest()
        }

    def _upload_document(self, document: dict):
        """Upload the prepared document to CouchDB."""
        return re.put(
            f'{self.url}/docs/{document["title"]}-{document["date"]}',
            json={
                "title": document["title"],
                "content": document["content"],
                "date": document["date"],
                "timestamp": int(time.time()),
                "checksum": document["checksum"],
            },
            auth=(self._user, self._password),
            timeout=int(self.secrets.get("DEFAULT_TIMEOUT", 30)),
        )

    def _construct_response(self, document: dict) -> dict:
        """Construct a response with metadata about the uploaded document."""
        return {
            "document_id": f'{document["title"]}-{document["date"]}',
            "db": "docs",
            "message": "Document successfully added to CouchDB",
            "timestamp": int(time.time()),
        }

    def get_document(self, doc_id: str) -> dict:
        """
        Retrieve a document from CouchDB using its ID.

        :param doc_id: Document ID.
        :return: The document data.
        """
        try:
            response = re.get(
                f"{self.url}/docs/{doc_id}",
                auth=(self._user, self._password),
                timeout=int(self.secrets.get("DEFAULT_TIMEOUT", 30)),
            )
            response.raise_for_status()
            document = response.json()
            document["content"] = self._decompress_content(document["content"])
            return document
        except re.RequestException as e:
            raise HTTPException(status_code=500, detail=f"An error occurred while retrieving the document: {e}")

    def _decompress_content(self, content: str) -> str:
        """Decompress and decode the document content."""
        return zlib.decompress(base64.b64decode(content)).decode("utf-8")

    def list_documents(self) -> list:
        """List all document IDs in CouchDB."""
        try:
            response = re.get(
                f"{self.url}/docs/_all_docs",
                auth=(self._user, self._password),
                timeout=int(self.secrets.get("DEFAULT_TIMEOUT", 30)),
            )
            response.raise_for_status()
            return [row["id"] for row in response.json().get("rows", [])]
        except re.RequestException as e:
            raise HTTPException(status_code=500, detail=f"An error occurred while listing documents: {e}")

    def delete_document(self, doc_id: str):
        """Delete a document from CouchDB."""
        if doc_id not in self.list_documents():
            raise HTTPException(
                status_code=404,
                detail="Document not found. Cannot delete a non-existing document.",
            )
        rev = self.get_document(doc_id)["_rev"]
        try:
            re.delete(
                f"{self.url}/docs/{doc_id}?rev={rev}",
                auth=(self._user, self._password),
                timeout=int(self.secrets.get("DEFAULT_TIMEOUT", 30)),
            )
        except re.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete document: {e}")

    def create_user(self, username: str, password: str, roles: list | tuple):
        """Create a new user in CouchDB."""
        if self._user_exists(username):
            raise HTTPException(status_code=409, detail="User already exists. Abort.")
        self._add_user_to_db(username, password, roles)

    def _user_exists(self, username: str) -> bool:
        try:
            response = re.get(
                f"{self.url}/_users/org.couchdb.user:{username}",
                auth=(self._user, self._password),
                timeout=int(self.secrets.get("DEFAULT_TIMEOUT", 30)),
            )
            return response.json().get("name") == username
        except re.RequestException:
            return False

    def _add_user_to_db(self, username: str, password: str, roles: list | tuple):
        try:
            data = {"name": username, "password": password, "roles": roles, "type": "user"}
            headers = {"Accept": "application/json", "Content-Type": "application/json"}
            re.put(
                f"{self.url}/_users/org.couchdb.user:{username}",
                json=data,
                headers=headers,
                auth=(self._user, self._password),
                timeout=int(self.secrets.get("DEFAULT_TIMEOUT", 30)),
            )
        except re.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Failed to create user: {e}")


class Extractor:
    """Handles PDF extraction operations."""

    def __init__(self, input_path: str):
        self.cur = 0
        self.input_path = input_path
        self.pdf_files = self._get_pdf_files()
        self.extracted_pdfs = []
        self.paths_to_extract = []
        self.files = []

    def _get_pdf_files(self) -> list:
        """Retrieve all PDF files from the specified directory."""
        if not os.path.exists(self.input_path):
            raise RuntimeError("Given Path does not exist!")

        pdf_files = []
        for root, _, files in os.walk(self.input_path):
            pdfs = [f for f in files if f.lower().endswith(".pdf")]
            if pdfs:
                pdf_files.append((root, pdfs))
        return pdf_files

    @staticmethod
    def from_bytes(inp: bytes) -> str:
        """Extract text from a PDF provided as bytes."""
        reader = PdfReader(inp)
        return "".join(page.extract_text() for page in reader.pages)

    def extract(self):
        """Extract text from the collected PDF files."""
        if not self.pdf_files:
            raise RuntimeError("No PDF files found!")
        self.paths_to_extract = [
            os.path.join(pdf_file[0], pdf)
            for pdf_file in self.pdf_files
            for pdf in pdf_file[1]
        ]
        for path in tqdm(self.paths_to_extract, total=len(self.paths_to_extract), desc="Extracting PDFs..."):
            extracted_text = self._extract_text_from_pdf(path)
            self.extracted_pdfs.append(extracted_text)

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from a single PDF file."""
        try:
            with open(pdf_path, "rb") as file:
                reader = PdfReader(file)
                return "".join(page.extract_text() for page in reader.pages)
        except (FileNotFoundError, errors.ParseError) as e:
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

    def to_txt(self, output_dir="../data/out"):
        """Write extracted text to text files."""
        os.makedirs(output_dir, exist_ok=True)
        for _, new_name, text in tqdm(self.files, desc="Writing to text files..."):
            new_name = new_name.replace(".pdf", "")
            with open(os.path.join(output_dir, f"{new_name}.txt"), "w") as file:
                file.write(text)
