"""Module for chat api"""

import requests as re
import xkcd
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, Response

from .models import Prompt


class Chat:
    """Chat class"""

    def __init__(self):
        self.router = APIRouter()
        self.router.add_api_route(
            "/chat/hello", self.hello, methods=["GET"], tags=["Chat"]
        )
        self.router.add_api_route("/chat/prompt", self.prompt, methods=["POST"], tags=["Chat"],
            deprecated=True, include_in_schema=False, )
        self.router.add_api_route("/chat/xkcd", self.xkcd_meme, tags=["Chat"], methods=["GET"],
            responses={
                200: {
                    "content": {
                        "image/png": {}
                    }
                }
            }, response_class=Response, )

    async def xkcd_meme(self):
        """## xkcd meme
        This endpoint is a small implementation of the famous cartoonist xkcd. Everyone knows their cartoons.
        Check the headers of the response for more information.

        """
        meme = xkcd.getRandomComic()

        img = re.get(meme.getImageLink(), timeout=300).content
        return Response(content=img.__bytes__(), media_type="image/png", headers={
            "x-image_name": meme.imageName,
            "x-image-url": meme.getImageLink(),
            "x-get-explaination": meme.getExplanation(),
            "x-get-link": meme.link,
            "x-disclaimer": "All rights belong to their respective owner.",
        }, )

    async def hello(self, name: str):
        return JSONResponse({"mesage": f"Hello, {name}!"})

    async def prompt(self, req: Prompt):
        """## Prompt
        The prompt endpoint handles all API requests towards the RAG Pipeline. In the example JSON, I obtained short text passages from [elswhere.org](https://www.elsewhere.org/journal/pomo/).
        ### Parameters
        - `"prompt"`: Initial prompt. Max 2.000 characters.
        - `"context"`: Additional context provided by the user as a list. (optional -->  meaning you can only pass on an empty list)
        - `"rag_mode"`: Defines the RAG mode. valid options: "no-rag", "naive", "advanced", "modular"
        - `"advanced_stats"`: Defines advanced stats mode. If this mode is enabled, the server will respond with more statistics (default: false)
        - `"use_for_future_rag"`: Whether or not the request will be stored in the Vector database to optimise the search quality. The server will return additionally a unique `prompt_id` which can be referred to later.  (true/false)

        """
        match req.rag_mode.strip():
            case "no-rag":
                # TODO: Add a direct pass-through to OpenAI
                print("No Rag SELECTED")
            case "naive":
                # TODO: Add a connection to `pipeline.rag.chunk` to chunk and do the rest
                print("Naive SELECTED")
            case "advanced":
                # TODO: Add a connection to chunk and Advanced RAG
                print("Advanced SELECTED")
            case "modular":
                # TODO: Add a connection to Chunk and Modular RAG
                print("Modular SELECTED")
            case _:
                raise HTTPException(
                    422,
                    f"Invalid Rag Mode. Valid RAG modes are ['no-rag', 'naive', 'advanced', 'modular']. Your selection was: {req.rag_mode}. Rag mode must be lower case and without any leading or tailing spaces.",
                )

        return req
