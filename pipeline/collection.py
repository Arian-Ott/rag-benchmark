from qdrant_client import models

from .vector import  Vectorstore

class Collection:
    """The `collection` class manages Qdrant collections and is used as a
        layer of abstraction to simplify and streamline Qdrant Collections.
        """



    def __init__(self, vector_store:Vectorstore, collection_name):
        """Instantiate a new Collection.
        This class is a wrapper around the Qdrant Collection API to simplify the API access.

        :param vector_store: Previously instantiated Vectorstore object.
        :type vector_store: Vectorstore
        :param collection_name: Name of the collection.
        :type collection_name: str
        :raises RuntimeError: If the collection does not exist.

        """
        if not vector_store.client.collection_exists(collection_name):
            vector_store.client.create_collection(collection_name,
                                                  vectors_config=models.VectorParams(size=vector_store.dimensions,distance=models.Distance.COSINE))

        self.dimensions = vector_store.dimensions
        self.name = collection_name
        self.client = vector_store.client

    def upload(self, points: list | tuple):
        """Upload a list of points to this collection.

        :param points: List or tuple of points
        :type points: list|tuple
        """
        self.client.upload_points(self.name, points)

    def __str__(self):
        """Returns the name of the collection as a string."""
        return self.name



    def __repr__(self):
        """Returns a string representation of the object."""
        return f"Collection(client={self.client},collection_name={self.name})"
