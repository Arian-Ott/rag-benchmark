"""Module related to Vector Embedding."""
import time

from qdrant_client import models

from .vector import Vectorstore


class Embedding:
    """Embedding class."""

    def __init__(self, vector_store: Vectorstore):
        self.vector_store = vector_store
        self._temp_text = []

    def add_text(self, text: str):
        """Add text to the embedding queue.
        :param text: text to be added
        :type text: str
        """
        self._temp_text.append(text)

    def embedding(self, text):
        """Embed text from the embedding queue.

        :param text: If you want to embed text directly, you can use this parameter to do so.
            Most of the time, it is supposed to be `None`
        :type text: str | list | None
        :return: list of VectorPoints of the embedded text
        :rtype: list
        """
        if text is None:
            texts = self._temp_text
        else:
            texts = text

        result = self.vector_store.oai.embeddings.create(
            input=text, model=self.vector_store.embedding_model
        )
        points = [
            models.PointStruct(
                id=int(time.time()),
                vector=data.embedding,
                payload={"text": text},

            )
            for data, text in zip(result.data, texts)
        ]
        self._temp_text = []
        return points
