import pytest
import qdrant_client
from qdrant_client import models

from pipeline import Vectorstore
from pipeline.rag.chunk import Chunking


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
    if strinp == "text-embedding-3-large":
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
    client.create_collection(
        collection_name="test",
        vectors_config=models.VectorParams(size=100, distance=models.Distance.COSINE),
    )
    assert client.collection_exists("test"), "Collection does not exist"

    client.delete_collection("test")
    assert not client.collection_exists("test"), "Collection still exists"


def test_chunking():
    print("Setup")
    chunk_1 = Chunking()
    chunk_2 = Chunking()
    t1 = ""
    t2 = ""
    print("Read example texts")
    with open("../data/out/Libretto-von-Die-Walküre-von-Richard-Wagner_.txt", "r") as f:
        t1 += f.read()
    with open("../data/out/Libretto-von-Siegfried-von-Richard-Wagner_.txt", "r") as g:
        t2 += g.read()
    print("Check if example texts are not equal")
    assert t1 != t2, "Different texts are supposed to be different"
    print("Start tokenisation")
    chunk_1.tokenise(t1)
    chunk_2.tokenise(t2)
    print("TEST: Equality Check")
    assert (chunk_1 != chunk_2
    ), "Different Chunk Objects are supposed to be different with different input text"
    print("TEST: Check for readable function")
    chunk_1.chunk()
    j = chunk_1.to_readable()

    assert isinstance(j, str), "Readable Chunks must be type string"


if __name__ == "__main__":
    pytest.main(["-vv", "-s"])
