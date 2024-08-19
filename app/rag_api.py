import logging
import time

import tiktoken
from fastapi import APIRouter, HTTPException
from qdrant_client import models

from pipeline import vector
from pipeline.retriever import DocumentDB

# Setup basic logging
logging.basicConfig(level=logging.INFO)


class RagApi:
    def __init__(self):
        self.router = APIRouter()
        self.vs = vector.Vectorstore(
            embedding_model="text-embedding-ada-002-sweden",
            host="192.168.1.77")
        self.router.add_api_route("/rag/update-index", self.index_all_files,
                                  methods=["GET"], tags=["RagAPI"])
        if not self.vs.client.collection_exists("text-embedding-3-small"):
            self.vs.client.create_collection("text-embedding-3-small",
                                             models.VectorParams(
                                                 size=self.vs.dimensions,
                                                 distance=models.Distance.COSINE
                                             ))

    def chunk_text_with_tiktoken(self, text, max_tokens=500, model_name="text-embedding-ada-002"):
        # Initialize the tokenizer for the specified model
        tokenizer = tiktoken.encoding_for_model(model_name)

        tokens = tokenizer.encode(text)
        chunks = []
        current_chunk = []

        for token in tokens:
            current_chunk.append(token)
            if len(current_chunk) >= max_tokens:
                chunks.append(tokenizer.decode(current_chunk))
                current_chunk = []

        if current_chunk:
            chunks.append(tokenizer.decode(current_chunk))

        return chunks

    async def index_all_files(self):
        db = DocumentDB("192.168.1.77", 5984)
        list_files = db.list_documents()

        for file in list_files:
            document = db.get_document(file)
            content = document.get("content", "")

            if not content:
                logging.warning(f"No content found in document: {file}")
                continue

            # Chunk the text using tiktoken-based function
            chunks = self.chunk_text_with_tiktoken(content, max_tokens=100)

            for i, chunk in enumerate(chunks):
                logging.info(f"Processing chunk {i + 1}/{len(chunks)} for document: {file}")

                # Get embedding from OpenAI API
                try:
                    embedding_response = self.vs.oai.embeddings.create(
                        model=self.vs.embedding_model,
                        input=[chunk]
                    )

                    logging.info(f"Embedding response: {embedding_response}")

                except Exception as e:
                    logging.error(f"Error while getting embedding: {e}")
                    raise HTTPException(status_code=500, detail=f"Failed to get embedding: {str(e)}")

                # Check if embeddings were returned correctly

                # Extract the vector from the embedding response

                # Create point for Qdrant
                point = models.PointStruct(
                    id=int(time.time()) + i,  # Unique ID for the point
                    vector=embedding_response.data[0].embedding,
                    # The embedding vector

                    payload={
                        "text": chunk,
                        "document_id": file,
                        "chunk_index": i
                    }  # Additional data to store with the vector
                )

                # Upload the point to Qdrant
                try:

                    self.vs.client.upsert(
                        collection_name="text-embedding-3-small",
                        points=[point]  # Upload as a list of points
                    )
                    logging.info(f"Successfully uploaded point for chunk {i + 1}/{len(chunks)} of document: {file}")
                except Exception as e:
                    logging.error(f"Error while uploading point: {e}")
                    raise HTTPException(status_code=500, detail=f"Failed to upload point: {str(e)}")

        return {"status": "Indexing complete"}
