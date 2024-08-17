import pytest

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
    v = Vectorstore("192.168.1.77", strinp)
    if strinp is "text-embedding-3-large":

        assert v.dimensions == 3072, "Wrong dimensions"
    else:
        assert v.dimensions == 1536, "Wrong dimensions"
    assert v.embedding_model in (
        "text-embedding-3-small",
        "text-embedding-3-large",
        "text-embedding-ada-002",
    ), "Wrong embedding model"


if __name__ == "__main__":
    pytest.main([__file__])
