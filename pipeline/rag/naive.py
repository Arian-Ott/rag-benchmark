import json
import logging
from typing import List

from fastapi import APIRouter, HTTPException
from openai import AzureOpenAI
from qdrant_client import models

from passwords.pw import gpt_password, gpt_sweden
from pipeline import vector

logging.basicConfig(level=logging.INFO)


class NaiveRagGPT4:
    def __init__(
            self, embedding_model="text-embedding-ada-002-sweden", gpt_model="gpt-4o"
    ):
        self.router = APIRouter()
        self.vs = vector.Vectorstore(embedding_model=embedding_model)
        self.gpt_model = gpt_model

        self.client = AzureOpenAI(
            api_key=gpt_password,
            azure_endpoint=gpt_sweden,
            api_version="2023-03-15-preview",
        )

        if not self.vs.client.collection_exists("text-embedding-3-small"):
            self.vs.client.create_collection(
                "text-embedding-3-small",
                models.VectorParams(
                    size=self.vs.dimensions, distance=models.Distance.COSINE
                ),
            )

        self.router.add_api_route(
            "/rag/query", self.query, methods=["POST"], tags=["NaiveRag"]
        )

    def embed_text(self, text: str) -> List[float]:
        """Embed text using the vectorstore's embedding model."""
        embedding_response = self.vs.oai.embeddings.create(
            model=self.vs.embedding_model, input=[text]
        )
        return embedding_response.data[0].embedding

    def retrieve_documents(
            self, query_embedding: List[float], top_k: int = 5
    ) -> List[models.ScoredPoint]:
        """Retrieve top K documents from Qdrant based on the query embedding."""
        search_result = self.vs.client.search(
            collection_name="text-embedding-3-small",
            query_vector=query_embedding,
            limit=top_k,
        )
        return search_result

    def generate_response(self, query: str, context: str) -> str:
        """Generate a response using GPT-4."""
        prompt = f"Context: {context}\n\nQuery: {query}\n\nAnswer:"

        try:
            response = self.client.chat.completions.create(
                temperature=0.1,
                model="gpt-4o-sweden",
                messages=[
                    {"role": "user", "content": prompt},
                ],
            )
            a = dict(json.loads(response.to_json()))

            print(response)

            a = a["choices"][0]["message"]

            print(a)

            return a
        except Exception as e:
            logging.error(f"Failed to generate response using GPT-4: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate response.")

    async def query(self, query_text: str):
        """Handle a query by performing the full RAG process."""
        logging.info(f"Received query: {query_text}")

        try:
            query_embedding = self.embed_text(query_text)
        except Exception as e:
            logging.error(f"Failed to embed query: {e}")
            raise HTTPException(status_code=500, detail="Failed to embed query.")

        try:
            search_results = self.retrieve_documents(query_embedding)
            logging.info(f"Retrieved {len(search_results)} relevant documents.")
        except Exception as e:
            logging.error(f"Failed to retrieve documents: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve documents.")

        context = " ".join([result.payload["text"] for result in search_results])

        try:
            response = self.generate_response(query_text, context)
            logging.info(f"Generated response: {response}")
        except Exception as e:
            logging.error(f"Failed to generate response: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate response.")

        return {"query": query_text, "response": response}

