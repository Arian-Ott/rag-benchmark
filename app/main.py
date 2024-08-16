from fastapi import FastAPI
import uvicorn
from decouple import config

app = FastAPI()


if __name__ == "__main__":
    uvicorn.run(app, host=config("HOST"), port=int(config("PORT")))
