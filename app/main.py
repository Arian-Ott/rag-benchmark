"""Main module. Here will be the entry point of the application."""

import uvicorn
from fastapi import FastAPI

from chat import Chat
from database import DocumentDB

app = FastAPI()
cht = Chat()
db = DocumentDB()
app.include_router(cht.router)
app.include_router(db.router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6969)
