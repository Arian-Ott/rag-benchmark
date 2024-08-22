"""Main module. Here will be the entry point of the application."""

import uvicorn
from fastapi import FastAPI

from pipeline.rag import AdvancedRAG, ModularRag, NaiveRagGPT4
from .chat import Chat
from .database import DocumentDBRouter
from .rag_api import RagApi

app = FastAPI()
#
cht = Chat()
#
rapi = RagApi()
gpt4 = NaiveRagGPT4()
adv = AdvancedRAG()
#
db = DocumentDBRouter(rapi)
mod = ModularRag()
#
app.include_router(cht.router)
#
app.include_router(db.router)
#
app.include_router(rapi.router)
app.include_router(gpt4.router)
app.include_router(adv.router)
app.include_router(mod.router)
# Start the automatic rate limit handler
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6969, workers=4)
