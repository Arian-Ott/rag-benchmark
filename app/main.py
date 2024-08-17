from fastapi import FastAPI
import uvicorn
from decouple import config
from openai import embeddings

from pipeline import vector, collection, embedding, retriever

app = FastAPI()
if __name__ == "__main__":
    r = retriever.Extractor("../data")
    r.extract()
    r.to_txt()
    # vectorstore = vector.Vectorstore("192.168.1.77", "text-embedding-3-small")

    # col = collection.Collection(vectorstore,"text-embedding-3-small")
    # emb = embedding.Embedding(vectorstore)
    # emb.add_text("Lol")

# result = emb.embedding()
# col.upload(result)
