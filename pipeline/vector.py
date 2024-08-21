"""Module with all classes related to Vector operations."""

import openai
from decouple import config
from dotenv import dotenv_values
from qdrant_client import QdrantClient

from passwords import pw


class Vectorstore:
    """Handles operations with Qdrant databases, supporting OpenAI embedding models."""

    def __init__(self, embedding_model: str):
        """
        Initialize a Vectorstore instance.

        :param embedding_model: The name of the embedding model to use. Supported models include:
            - 'text-embedding-3-small'
            - 'text-embedding-ada-002'
            - 'text-embedding-3-large'
            - 'text-embedding-ada-002-sweden'
        :raises ValueError: If an unsupported embedding model is provided.
        """
        self.embedding_model = embedding_model
        self.dimensions = self._get_model_dimensions(embedding_model)
        self.client = self._initialize_qdrant_client()
        self.oai = self._initialize_openai_client()

    def _get_model_dimensions(self, embedding_model: str) -> int:
        """Retrieve the number of dimensions for the given embedding model."""
        model_dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-ada-002": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002-sweden": 1536,
        }
        try:
            return model_dimensions[embedding_model]
        except KeyError:
            raise ValueError(f"Unknown embedding model: {embedding_model}")

    def _initialize_qdrant_client(self) -> QdrantClient:
        """Initialize and return a Qdrant client instance."""
        qdrant_host = dotenv_values("../.env").get("QDRANT_HOST")
        return QdrantClient(host=qdrant_host, api_key=pw.access_token_qdrant, port=443)

    def _initialize_openai_client(self):
        """Initialize and return an OpenAI client instance based on the selected embedding model."""
        if self.embedding_model == "text-embedding-ada-002-sweden":
            azure_env = dotenv_values("../azure.env")
            return openai.AzureOpenAI(
                azure_endpoint=azure_env.get("URL"),
                api_key=azure_env.get("AOAI_ADA_KEY"),
                api_version=azure_env.get("API_VERSION"),
            )
        else:
            return openai.OpenAI(api_key=config("EMBEDDING"))
