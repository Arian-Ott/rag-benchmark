"""Module related to Vector Embedding."""
import time

from qdrant_client import models

from .vector import Vectorstore


class Embedding:
    """Class for handling text embeddings and managing a vector store."""

    def __init__(self, vector_store: Vectorstore):
        """Initialize the Embedding class with a vector store instance."""
        self.vector_store = vector_store
        self._text_queue = []

    def add_text(self, text: str):
        """Add text to the embedding queue.

        :param text: The text to be added to the queue.
        :type text: str
        """
        self._text_queue.append(text)

    def embed(self, text=None):
        """Embed text from the queue or directly from the provided input.

        :param text: Text to be embedded. If None, the method will use texts from the queue.
                     Can be a single string or a list of strings.
        :type text: str | list[str] | None
        :return: A list of VectorPoints representing the embedded text.
        :rtype: list[models.PointStruct]
        """
        texts_to_embed = self._text_queue if text is None else self._ensure_list(text)

        if not texts_to_embed:
            raise ValueError("No text provided for embedding.")

        embedding_results = self.vector_store.oai.embeddings.create(
            input=texts_to_embed,
            model=self.vector_store.embedding_model
        )

        points = self._create_vector_points(embedding_results.data, texts_to_embed)
        self._clear_queue()
        return points

    def _ensure_list(self, text):
        """Ensure the text input is a list."""
        return [text] if isinstance(text, str) else text

    def _create_vector_points(self, embedding_data, texts):
        """Create a list of vector points from embedding data and texts."""
        return [
            models.PointStruct(
                id=int(time.time() * 1000),  # More precise unique IDs
                vector=data.embedding,
                payload={"text": text},
            )
            for data, text in zip(embedding_data, texts)
        ]

    def _clear_queue(self):
        """Clear the text queue after embedding."""
        self._text_queue = []
