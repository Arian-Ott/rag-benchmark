from typing import List

from pydantic import BaseModel, Field


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


class UserCreation(BaseModel):
    """Pydantic model for creating a user"""

    username: str
    password: str
    authorisation: str


class FileMetadata(BaseModel):
    category: str = Field(default="Wagner")
    tags: list[str] = Field(default_factory=list)


class Files(BaseModel):
    meta_data: List[FileMetadata]


class FileResponse(BaseModel):
    """Pydantic model for returning a file id"""

    file_id: str
