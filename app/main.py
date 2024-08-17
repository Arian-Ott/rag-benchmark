from fastapi import FastAPI

from pipeline import collection, embedding, retriever, vector

app = FastAPI()

if __name__ == "__main__":
    r = retriever.Extractor("../data")
    r.extract()
    r.to_txt()
    vectorstore = vector.Vectorstore("192.168.1.77", "text-embedding-3-small")

    col = collection.Collection(vectorstore, "text-embedding-3-small")
    emb = embedding.Embedding(vectorstore)
    emb.add_text("Das Wertpapierhaus der Sparkassen")

    result = emb.embedding()
    col.upload(result)
