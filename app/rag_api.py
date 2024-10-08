import logging
import os
import uuid
from asyncio import gather, sleep, to_thread
from http import HTTPStatus

import tiktoken
from dotenv import dotenv_values
from fastapi import APIRouter, BackgroundTasks, HTTPException
from httpx import HTTPStatusError
from qdrant_client import models
from starlette import status

from pipeline import vector
from pipeline.retriever import DocumentDB

# Setup basic logging
log_file = "rag_api.log"
if os.path.exists(log_file):
    os.remove(log_file)
logging.basicConfig(level=logging.INFO, filename=log_file)


class RagApi:
    def __init__(self):
        self.bg_running = False
        self.router = APIRouter()
        self.vs = vector.Vectorstore(embedding_model="text-embedding-ada-002-sweden")
        self._initialize_routes()
        self._initialize_vectorstore()
        self.chunk_size = os.environ.get("CHUNK_SIZE", 300)

    def _initialize_routes(self):
        self.router.add_api_route("/rag/update-index", self.index_all_files, methods=["GET"],
            tags=["RagAPI"], deprecated=True, )
        self.router.add_api_route("/rag/check-background", self.check_background, methods=["GET"],
            tags=["RagAPI"], status_code=200, )
        self.router.add_api_route("/rag/create-index", self.create_qdrant, methods=["POST"],
            tags=["RagAPI"], status_code=HTTPStatus.CREATED, deprecated=True, )
        self.router.add_api_route("/rag/delete-index", self.delete_qdrant, methods=["DELETE"],
            tags=["RagAPI"], status_code=HTTPStatus.NO_CONTENT, deprecated=True,
        )

    def _initialize_vectorstore(self):
        if not self.vs.client.collection_exists("text-embedding-3-small"):
            self.vs.client.create_collection(
                "text-embedding-3-small",
                models.VectorParams(
                    size=self.vs.dimensions, distance=models.Distance.COSINE
                ),
            )

    def _chunk_text(self, text, max_tokens, model_name="text-embedding-ada-002"):
        tokenizer = tiktoken.encoding_for_model(model_name)
        tokens = tokenizer.encode(text)
        return [tokenizer.decode(tokens[i: i + max_tokens]) for i in
            range(0, len(tokens), max_tokens)]

    async def index_all_files(self, background_tasks: BackgroundTasks):
        """## Index all documents
        This API route has been deprecated until this university project has been graded to prevent unwanted changes within the data structure.
        """
        if self.bg_running:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "This server has an active indexing job running on multiple threads in the background, "
                    "involving different internal APIs and databases. To prevent a server crash and avoid "
                    "concurrency issues, this request has been blocked. Please try again later."
                ),
            )

        logging.info("Initializing background job for indexing files.")
        self.bg_running = True
        background_tasks.add_task(self._background_task)
        return {
            "status": "Initialized a background job to index all files. This can take some minutes."
        }

    async def _background_task(self):
        """## Background task for indexing files."""
        try:
            self.bg_running = True
            logging.info("Obtaining documents")
            db = DocumentDB(
                host=dotenv_values("../.env").get("COUCHDB_HOST"),
                port=int(dotenv_values("../.env").get("COUCHDB_PORT")),
            )

            list_files = await to_thread(db.list_documents)
            tasks = [self._process_document(db, file) for file in list_files]
            await gather(*tasks)
        finally:
            self.bg_running = False

    def _gen_points(self, chunk_batch, file):
        try:
            embedding_response = self.vs.oai.embeddings.create(
                model=self.vs.embedding_model, input=chunk_batch, timeout=10
            )

            points = [
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding.embedding,
                    payload={"text": chunk, "document_id": file, "chunk_index": index},
                )
                for index, (chunk, embedding) in enumerate(
                    zip(chunk_batch, embedding_response.data)
                )
            ]
            return points
        except Exception as e:
            logging.error(f"Failed to generate embeddings: {e}")
            return []

    async def _process_chunk_batch(self, points, file):
        try:
            await to_thread(
                self.vs.client.upsert,
                collection_name="text-embedding-3-small",
                points=points,
            )
            logging.debug(
                f"Successfully uploaded {len(points)} points for document: {file}"
            )
        except HTTPStatusError as e:
            if e.response.status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", 1))
                logging.warning(
                    f"Rate limit exceeded, retrying in {retry_after} seconds..."
                )
                await sleep(retry_after)
                await self._process_chunk_batch(points, file)  # Retry the batch
            else:
                logging.error(
                    f"Error while processing batch of chunks for document: {file}: {e}"
                )
                raise HTTPException(
                    status_code=500, detail=f"Failed to process chunk batch: {str(e)}"
                )
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to process chunk batch: {str(e)}"
            )

    async def _process_document(self, db, file):
        document = await to_thread(db.get_document, file)
        content = document.get("content", "")

        if not content:
            logging.warning(f"No content found in document: {file}")
            return

        chunks = self._chunk_text(content, max_tokens=int(os.environ.get("CHUNK_SIZE", 300)))

        batch_size = 4  # Adjust this based on your API's capacity

        for i in range(0, len(chunks), batch_size):
            chunk_batch = chunks[i: i + batch_size]
            points = self._gen_points(chunk_batch, file)
            if points:
                await self._process_chunk_batch(points, file)

        logging.info(f"Document processing completed for: {file}")

    async def delete_qdrant(self):
        """
        ## Delete Qdrant collection
        This endpoint has been deprecated until the university project has been graded to prevent unwanted changes within the data structure.
        ## Function:
        Delete Qdrant collection and reinitialise it.
        """
        if self.vs.client.collection_exists("text-embedding-3-small"):
            self.vs.client.delete_collection("text-embedding-3-small")

        self.vs.client.create_collection("text-embedding-3-small",
            models.VectorParams(size=self.vs.dimensions, distance=models.Distance.COSINE), )
        return {
            "message": "Deleted Qdrant collection"
        }

    async def create_qdrant(self):
        """Create Qdrant collection."""
        if self.vs.client.collection_exists("text-embedding-3-small"):
            raise HTTPException(status_code=400, detail="Collection already exists")
        self.vs.client.create_collection("text-embedding-3-small",
            models.VectorParams(size=self.vs.dimensions, distance=models.Distance.COSINE), )
        return {
            "status": "Created Qdrant collection"
        }

    async def check_background(self):
        """Check if a background task is running."""
        if self.bg_running:
            raise HTTPException(409, detail="Indexing in progress...")
        return {
            "status": "No background task running!"
        }
