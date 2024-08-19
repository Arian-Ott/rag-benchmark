"""Module for chat api"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class Prompt(BaseModel):
    prompt: str = "The quick brown fox jumps over the lazy dog"
    context: list | None = [
        "“Language is part of the fatal flaw of art,” says Lacan; however, according to Brophy[5].",
        "it is not so much language that is part of the fatal flaw of art, but rather the rubicon of language.",
        "The primary theme of the works of Burroughs is the role of the observer as artist.",
        "If modernism holds, the works of Burroughs are postmodern.",
        " Thus, Sartre promotes the use of Derridaist reading to deconstruct and analyse art.",
        "Debord uses the term ‘capitalist theory’ to denote a postcultural reality.",
        "It could be said that Foucault promotes the use of semioticist narrative to deconstruct class divisions.",
    ]
    rag_mode: str = "no-rag"
    advanded_stats: bool = False
    use_for_future_rag: bool = True


class Chat:
    """Chat class"""

    def __init__(self):
        self.router = APIRouter()
        self.router.add_api_route(
            "/chat/hello", self.hello, methods=["GET"], tags=["Chat"]
        )
        self.router.add_api_route(
            "/chat/prompt", self.prompt, methods=["POST"], tags=["Chat"]
        )

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
