import uvicorn
from fastapi import FastAPI

from chat import Chat
from database import FileUpload

app = FastAPI()
cht = Chat()
db = FileUpload()
app.include_router(cht.router)
app.include_router(db.router)
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    # r = retriever.Extractor("../data")
    # r.extract()
    # r.to_txt()
    # vectorstore = vector.Vectorstore("192.168.1.77", "text-embedding-3-small")

    # col = collection.Collection(vectorstore, "text-embedding-3-small")
    # emb = embedding.Embedding(vectorstore)
    #emb.add_text("Ich esse einen Apfel")

    # result = emb.embedding()
    #col.upload(result)
