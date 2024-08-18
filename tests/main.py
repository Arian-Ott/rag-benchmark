import pytest
import qdrant_client
from qdrant_client import models

from pipeline import Vectorstore


@pytest.mark.parametrize(
    "strinp",
    [
        "text-embedding-3-large",
        "text-embedding-3-small",
        "text-embedding-ada-002",
    ],
)
def test_db(strinp):
    """Checks for the Dimensions of the DB"""
    print("Initialise vector store")
    v = Vectorstore("192.168.1.77", strinp)
    print("test for dimensions")
    if strinp is "text-embedding-3-large":

        assert v.dimensions == 3072, "Wrong dimensions"
    else:
        assert v.dimensions == 1536, "Wrong dimensions"
    assert v.embedding_model in (
        "text-embedding-3-small",
        "text-embedding-3-large",
        "text-embedding-ada-002",
    ), "Wrong embedding model"
    print("Test qdrant client")
    client = qdrant_client.QdrantClient("192.168.1.77")
    client.create_collection(collection_name="test", vectors_config=models.VectorParams(
        size=100, distance=models.Distance.COSINE))
    assert client.collection_exists("test") == True, ("Collection does not "
                                                      "exist")

    client.delete_collection("test")
    assert client.collection_exists("test") == False, ("Collection does "
                                                       "still exist")


if __name__ == "__main__":
    pytest.main([__file__])
