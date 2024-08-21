"""Main module. Here will be the entry point of the application."""

import uvicorn
from fastapi import FastAPI

from chat import Chat
from database import DocumentDBRouter
from pipeline.rag.naive import NaiveRagGPT4
from rag_api import RagApi

app = FastAPI()
#
cht = Chat()
#
rapi = RagApi()
gpt4 = NaiveRagGPT4()
#
db = DocumentDBRouter(rapi)

#
app.include_router(cht.router)
#
app.include_router(db.router)
#
app.include_router(rapi.router)
app.include_router(gpt4.router)

# Start the automatic rate limit handler
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6969)
