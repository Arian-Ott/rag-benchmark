from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)
from qdrant_client.models import VectorParams, Distance

if not client.collection_exists("my_collection"):
   client.create_collection(
      collection_name="my_collection",
      vectors_config=VectorParams(size=100, distance=Distance.COSINE),
   )