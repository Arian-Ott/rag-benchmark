import base64
import os
import time
import zlib

import requests as re
from dotenv import dotenv_values
from fastapi import HTTPException
from pypdf import PdfReader
from tqdm import tqdm


class DocumentDB:
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
        try:
            document["content"] = base64.b64encode(
                zlib.compress(document["content"].encode("utf-8"), 9)
            ).decode("utf-8")
            response = re.put(
                self.url + f'/docs/{document["title"]}-{document["date"]}',
                json={
                    "title": document["title"],
                    "content": document["content"],
                    "date": document["date"],
                },
                auth=(self._user, self._password),
            )
            response.raise_for_status()
        except re.RequestException as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            return {
                "document_id": f"{document['title']}-{document['date']}",
                "db": "docs",
                "message": "Document successfully added to CouchDB",
                "timestamp": int(time.time()),
            }

    def get_document(self, doc_id):
        try:
            response = re.get(
                self.url + f"/docs/{doc_id}", auth=(self._user, self._password)
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
                self.url + "/docs/_all_docs", auth=(self._user, self._password)
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
        if not doc_id in self.list_documents():
            raise HTTPException(
                status_code=404,
                detail="Document not found. Cannot delete a non-existing document.",
            )
        rev = self.get_document(doc_id)["_rev"]
        re.delete(
            self.url + f"/docs/{doc_id}?rev={rev}", auth=(self._user, self._password)
        )


class Extractor:
    def __init__(self, inp):
        self.cur = 0
        self.nex = 1
        self.input_path = inp

        if not os.path.exists(self.input_path) and type(inp) == str:
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
        reader = PdfReader(inp)
        pdf_text = ""
        for page in reader.pages:
            pdf_text += page.extract_text()
        return pdf_text

    def extract(self):
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
            try:
                extracted_text = self._extract_text_from_pdf(path)
                self.extracted_pdfs.append(extracted_text)
            except Exception as e:
                print(f"Failed to extract {path}: {e}")

    def _extract_text_from_pdf(self, pdf_path):
        text = ""
        try:
            with open(pdf_path, "rb") as file:
                reader = PdfReader(file)
                # Iterate over each page
                for page in reader.pages:
                    text += page.extract_text() or ""
        except Exception as e:
            raise RuntimeError(f"Failed to read PDF {pdf_path}: {e}")
        self.files.append(
            (pdf_path, os.path.basename(pdf_path).replace(" ", "-"), text)
        )
        return text

    def to_txt(self):
        if not os.path.exists("../data/out"):
            os.mkdir("../data/out")

        for pdf_path, new_name, text in tqdm(
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
