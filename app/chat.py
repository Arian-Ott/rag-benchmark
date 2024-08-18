from fastapi import APIRouter


class Chat:

    def __init__(self):
        self.router = APIRouter(prefix="/chat", tags=["Chat"])
        self.router.add_api_route("/test/", self.hello, methods=["GET"])

    async def hello(self, name: str):
        return f"Hello {name}"
