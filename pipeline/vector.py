"""Module with all classes about Vector"""

import openai
from decouple import config
from qdrant_client import QdrantClient


class Vectorstore:
    """The `Vectorstore` class handles different Qdrant databases. It has
    the ability to connect to different hosts. Currently it only supports
    OpenAI Embedding models."""

    def __init__(self, host, embedding_model, port=6333):
        """Instantiate a new Vectorstore object.


        :param host: IP address or domain name of the Qdrant server.
        :type host: str
        :param port: Port of the Qdrant server. Typically it is `6333`
        :type port: int
        :param embedding_model: Name of the embedding model. You can choose
        between `text-embedding-3-small`, `text-embedding-3-large`, `text-embedding-ada-002`
        :type embedding_model: str
        :raises ValueError: If `host` is not a valid host name.
        :raise InformationOnly: If `collection` is added
        """

        match embedding_model:
            case "text-embedding-3-small":
                self.dimensions = 1536
            case "text-embedding-ada-002":
                self.dimensions = 1536
            case "text-embedding-3-large":
                self.dimensions = 3072
            case _:
                raise ValueError("Unknown embedding model")
        self.embedding_model = embedding_model

        self.client = QdrantClient(host=host, port=port)
        self.oai = openai.OpenAI(
            api_key=config("EMBEDDING"),
        )
