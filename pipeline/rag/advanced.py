from datetime import datetime

from fastapi import APIRouter, Body
from openai import AzureOpenAI
from pydantic import BaseModel

from passwords.pw import api_version, gpt_password, gpt_sweden
from pipeline.vector import Vectorstore


class Prompt(BaseModel):
    prompt: str = ("Wie ist der kontinuierliche Verbesserungsprozess der Volksbank Heilbronn?")
    top_k: int = 5
    language: str = "German"


class AdvancedRAG:
    def __init__(self):
        self.router = APIRouter()
        self.router.add_api_route("/rag/advanced-rag", self.wrapper, methods=["POST"],
            tags=["AdvancedRAG"])
        self.clien = AzureOpenAI(api_key=gpt_password, azure_endpoint=gpt_sweden,
            api_version=api_version,
            azure_deployment="https://ai-team-dbs-sweden.openai.azure.com/openai/deployments/gpt-4o-sweden/chat/completions?api-version=2023-03-15-preview", )

        self.clien.chat.completions.create(messages=[{
                                                         "role": "user",
                                                         "content": "Lol"
                                                     }], model="gpt-4o-sweden")

        self.user_prompt = ""
        self.new_prompt = ""
        self.embedded_prompt = ""
        self.docs = []
        self.language = "German"

    def add_prompt(self, prompt, language):
        p1 = (f"please answer with one Word: Which language is this prompt? "
              f"Prompt: {prompt}")
        prmt = f"Reformulate the following prompt so that it is more precise and specific Prompt suitable for a LLM to understand. Prompt: {prompt}"
        self.language = language
        self.new_prompt = (
            self.clien.chat.completions.create(temperature=0.1, model="gpt-4o-sweden", messages=[{
                "role": "user",
                "content": prmt
            }, ], ).choices[0].message.content)
        print(self.new_prompt)
        self.embedded_prompt = self.embed_text(self.new_prompt)

    def retrieve_top_k(self, k):
        vs = Vectorstore("text-embedding-ada-002-sweden")
        docs = vs.client.search(collection_name="text-embedding-3-small",
            query_vector=self.embedded_prompt, limit=k, with_vectors=False, with_payload=True, )
        docs = list(docs)
        t = []
        for doc in docs:
            a = doc.payload.get("text")
            a = a.strip()
            a = a.replace("...", "")
            a = " ".join(a.split())
            t.append(a)

        self.docs = t

    def embed_text(self, text: str):
        """Embed text using the vectorstore's embedding model."""
        vs = Vectorstore("text-embedding-ada-002-sweden")

        embedding_response = vs.oai.embeddings.create(model=vs.embedding_model, input=[text])
        return embedding_response.data[0].embedding

    def new_prompting(self):
        promptt = (
            f"Based on this old prompt and this old data, improve the prompt for an LLM to understand better. Formulate the new prompt in the same language as the old one"
            f"Old Prompt: {self.new_prompt},"
            f"Old Data: {self.docs}")

        self.new_prompt = (
            self.clien.chat.completions.create(temperature=0.1, model="gpt-4o-sweden", messages=[{
                                                                                                     "role": "user",
                                                                                                     "content": promptt
                                                                                                 }], ).choices[
                0].message.content)

    def answer(self):
        prompt = (f"System: Please answer following prompt based on the "
                  f"provided context. Select relevant facts only. Your answer should be in plain text only."
                  f"Prompt: {self.new_prompt}"
                  f"Context: {self.docs}"
                  f"Current Date: {datetime.today()}"
                  f"Target language: {self.language}")
        print(prompt)

        return (self.clien.chat.completions.create(temperature=0.3, model="gpt-4o-sweden",
            messages=[{
                          "role": "user",
                          "content": prompt
                      }], ).choices[0].message.content)

    async def wrapper(self, request: Prompt = Body(...)):
        """## Advanced RAG endpoint
        This represents the advanced RAG implementation.
        Since the data goes through a decent amount of stages can a request take about 3 minutes.

        Please be patient.
        """
        self.add_prompt(request.prompt, request.language)
        self.retrieve_top_k(request.top_k)
        self.new_prompting()
        return self.answer()
