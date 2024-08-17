import time
import uuid

from .vector import Vectorstore
from qdrant_client.models import PointStruct
class Embedding:
    def __init__(self, vector_store:Vectorstore):
        self.vector_store = vector_store
        self._temp_text = []

    def add_text(self, text: str):
        self._temp_text.append(text)

    def embedding(self, text: str | None = None):
        if text is None:
            texts = self._temp_text
        else:
            texts = text

        result = self.vector_store.oai.embeddings.create(
            input=texts, model=self.vector_store.embedding_model
        )

        points = [
            PointStruct(
                id=int(time.time()),
                vector=data.embedding,
                payload={"text": text},
            )
            for  data, text in zip(result.data, texts)
        ]
        self._temp_text = []
        return points
