"""Class with functions related to retrieving data from the database or pdfs"""

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
    """Use-Case specific class to connect to the CouchDB"""
    def __init__(self, host, port):
        try:
            self.secrets = dotenv_values("../.env")
            self._user = self.secrets["COUCH_DB_USER"]
            self._password = self.secrets["COUCH_DB_SECRET"]
        except KeyError as e:
            raise Exception("Missing environment variable") from e

        self.host = host
        self.port = port
        self.url = f"http://{self.host}:{self.port}"

    def add_document(self, document):
        """Adds a document to the CouchDB.
        This function generates a unique id for each document.
        The uid consists out of two parts:
        `<title>-<current-timestamp>`

        Since it is highly unlikely that someone will upload two identical documents at exactly the same time
        I decided to use `time.time()` as a timestamp.

        :param document: Document to be added to the CouchDB
        :type document: file
        :return: Meta-information about the added document
        :rtype: dict
        """
        try:
            name = str(document.filename).replace(",", "-").replace(" ", "-")
            ret = Extractor.from_bytes(document.file)
            document = {"title": name, "content": ret}

            document["content"] = base64.b64encode(
                zlib.compress(document["content"].encode("utf-8"), 9)
            ).decode("utf-8")
            document["date"] = time.strftime("%Y-%m-%d-%H-%M-%S")
            document["checksum"] = hashlib.sha3_256(document["content"].encode("utf-8")).hexdigest()
            response = re.put(
                self.url + f'/docs/{document["title"]}-{document["date"]}',
                json={
                    "title": document["title"],
                    "content": document["content"],
                    "date": document["date"],
                    "timestamp": int(time.time()),
                    "checksum": document["checksum"]
                },
                auth=(self._user, self._password),
                timeout=int(self.secrets.get("DEFAULT_TIMEOUT"))
            )
            response.raise_for_status()
        except re.RequestException as e:
            raise HTTPException(status_code=500, detail=str(e))

        return {
                "document_id": f"{document['title']}-{document['date']}",
                "db": "docs",
                "message": "Document successfully added to CouchDB",
                "timestamp": int(time.time()),
            }

    def get_document(self, doc_id):
        """Gets a document from the CouchDB using a document id.

        :param doc_id: The document id (<title>-<current-timestamp>)
        :type doc_id: str
        :return: The document from the CouchDB
        :rtype: dict
        """


        try:
            response = re.get(
                self.url + f"/docs/{doc_id}", auth=(self._user, self._password), timeout=int(self.secrets.get("DEFAULT_TIMEOUT"))
            )
            response.raise_for_status()
            document = response.json()

            # Decode and decompress the content
            document["content"] = zlib.decompress(
                base64.b64decode(document["content"])
            ).decode("utf-8")

            return document
        except re.exceptions.RequestException as e:
            print(f"An error occurred while retrieving the document: {e}")
            return None

    def list_documents(self):
        try:
            response = re.get(
                self.url + "/docs/_all_docs", auth=(self._user, self._password), timeout=int(self.secrets.get("DEFAULT_TIMEOUT"))
            )
            response.raise_for_status()
            docs = response.json()

            # Extract and return the list of document IDs
            doc_ids = [row["id"] for row in docs["rows"]]
            return doc_ids
        except re.exceptions.RequestException as e:
            print(f"An error occurred while listing documents: {e}")
            return []

    def delete_document(self, doc_id):
        """Deletes a document from the CouchDB.

        :param doc_id: Document id (<title>-<current-timestamp>)
        :type doc_id: str

        :raise HTTPException: If the document is not found
        """
        if doc_id not in self.list_documents():
            raise HTTPException(
                status_code=404,
                detail="Document not found. Cannot delete a non-existing document.",
            )
        rev = self.get_document(doc_id)["_rev"]
        re.delete(
            self.url + f"/docs/{doc_id}?rev={rev}", auth=(self._user, self._password), timeout=int(self.secrets.get("DEFAULT_TIMEOUT")),
        )

    def create_user(self, username, password, roles: list | tuple):
        """Creates a new user in the CouchDB.


        :param username: username of the user
        :type username: str
        :param password: password of the user
        :type password: str
        :param roles: a list of roles (most likely you want it to be empty)
        :type roles: tuple|list

        :raise HTTPException 409: If the user already exists
        :raise HTTPException 500: If something unexpected happens
        """
        try:
            d = dict(
                re.get(
                    self.url + f"/_users/org.couchdb.user:{username}",
                    auth=(self._user, self._password),
                    timeout=int(self.secrets.get("DEFAULT_TIMEOUT"))
                ).json()
            )

            if d["name"] == username:
                raise HTTPException(
                    status_code=409, detail="User already exists. Abort."
                )

            headers = {"Accept": "application/json", "Content-Type": "application/json"}
            data = {
                "name": username,
                "password": password,
                "roles": roles,
                "type": "user",
            }

            re.put(
                self.url + f"/_users/org.couchdb.user:{username}",
                json=data,
                headers=headers,
                auth=(self._user, self._password),
                timeout=int(self.secrets.get("DEFAULT_TIMEOUT"))
            )

        except re.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail={"message": str(e)})


class Extractor:
    """Extracts data from a PDF."""
    def __init__(self, inp):
        self.cur = 0
        self.nex = 1
        self.input_path = inp

        if not isinstance(os.path.exists(self.input_path), str):
            raise RuntimeError("Given Path does not exist!")

        # Filter out only PDF files
        self.pdf_files = []
        for root, _, files in os.walk(self.input_path):
            pdfs = [f for f in files if f.lower().endswith(".pdf")]
            if pdfs:
                self.pdf_files.append((root, pdfs))

        self.extracted_pdfs = []
        self.paths_to_extract = []
        self.files = []

    @staticmethod
    def from_bytes(inp):
        """Converts a PDF from bytes to a str.
        :param inp: PDF content
        :type inp: bytes|str
        :return: Converted PDF content
        :rtype: str
        """
        reader = PdfReader(inp)
        pdf_text = ""
        for page in reader.pages:
            pdf_text += page.extract_text()
        return pdf_text

    def extract(self):
        """Extracts data from the previously added pdfs to text.


        """
        if not self.pdf_files:
            raise RuntimeError("No PDF files found!")

        self.paths_to_extract = [
            os.path.join(pdf_file[0], pdf)
            for pdf_file in self.pdf_files
            for pdf in pdf_file[1]
        ]

        for path in tqdm(
            self.paths_to_extract,
            total=len(self.paths_to_extract),
            desc="Extracting PDFs...",
        ):
            extracted_text = self._extract_text_from_pdf(path)
            self.extracted_pdfs.append(extracted_text)



    def _extract_text_from_pdf(self, pdf_path):
        text = ""
        try:
            with open(pdf_path, "rb") as file:
                reader = PdfReader(file)
                # Iterate over each page
                for page in reader.pages:
                    text += page.extract_text() or ""
            self.files.append(
                (pdf_path, os.path.basename(pdf_path).replace(" ", "-"), text)
            )
            return text

        except FileNotFoundError as e:

            raise HTTPException(status_code=404, detail=f"File not found. Stack trace {e}")
        except errors.ParseError as e:

            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:

            raise HTTPException(status_code=500, detail=str(e))



    def to_txt(self):
        """Writes extracted data to a text file."""
        if not os.path.exists("../data/out"):
            os.mkdir("../data/out")

        for _, new_name, text in tqdm(
            self.files, desc="writing to " "text files..."
        ):
            new_name = new_name.replace(".pdf", "")
            with open(f"../data/out/{new_name}" + ".txt", "w") as file:
                file.write(text)

    def __iter__(self):
        return iter(self.extracted_pdfs)

    def __len__(self):
        return len(self.extracted_pdfs)

    def __next__(self):
        if self.cur >= len(self.extracted_pdfs):
            raise StopIteration
        self.cur += 1

        return self.extracted_pdfs[self.cur]
