from fastapi import APIRouter
from openai import AzureOpenAI
from pydantic import BaseModel

from passwords.pw import api_version, gpt_password, gpt_sweden
from pipeline.vector import Vectorstore


class ModularRagPrompt(BaseModel):
    prompt: str = "Wer ist Siglinde?"
    top_k: int = 5
    language: str = "German"


class ModularRag:
    def __init__(self):
        self.user_prompt = ""
        self.vs = Vectorstore("text-embedding-ada-002-sweden")
        self.client = AzureOpenAI(api_key=gpt_password, azure_endpoint=gpt_sweden,
            api_version=api_version,
            azure_deployment="https://ai-team-dbs-sweden.openai.azure.com/openai/deployments/gpt-4o-sweden/chat/completions?api-version=2023-03-15-preview", )
        self.router = APIRouter()
        self.router.add_api_route("/rag/modular-rag", self.modular, methods=["POST"],
                                  tags=["ModularRag"])
        self.language = "German"

    def set_user_prompt(self, prompt):
        """Set the user prompt for the current session."""
        self.user_prompt = prompt

    def refine_prompt(self, prompt):
        """Refine the input prompt to be more specific and clear for LLMs."""
        refined_prompt = f"Reformulate the following prompt to make it more precise and specific for a large language model: '{prompt}'"
        response = self.client.chat.completions.create(model="gpt-4o", temperature=0.3, messages=[{
                                                                                                      "role": "user",
                                                                                                      "content": refined_prompt
                                                                                                  }], )
        return response.choices[0].message.content

    def extract_features(self, text):
        """Extract important features and key information from the given text."""
        prompt = f"Extract all relevant features and key information from the following text, listed item by item: '{text}'"
        response = self.client.chat.completions.create(model="gpt-4o", temperature=0.3, messages=[{
                                                                                                      "role": "user",
                                                                                                      "content": prompt
                                                                                                  }], )
        return response.choices[0].message.content

    def filter_and_adjust_features(self, text, original_prompt):
        """Filter and adjust features to align with the original prompt."""
        prompt = f"Based on the following prompt, extract all relevant information from the text. If none is relevant, respond with 'None'. Text: '{text}' Prompt: '{original_prompt}'"
        response = self.client.chat.completions.create(model="gpt-4o", temperature=0.01, messages=[{
                                                                                                       "role": "user",
                                                                                                       "content": prompt
                                                                                                   }], )
        answer = response.choices[0].message.content

        if "none" in answer.lower():
            for _ in range(5):
                reformulate_prompt = (
                    f"Based on the given information and the original prompt, reformulate the prompt to better match the available data. "
                    f"Original Prompt: '{original_prompt}', Extracted Features: '{answer}'")
                response = self.client.chat.completions.create(model="gpt-4o", temperature=0.01,
                    messages=[{
                                  "role": "user",
                                  "content": reformulate_prompt
                              }], )
                new_prompt = response.choices[0].message.content

                if "none" not in new_prompt.lower():
                    original_prompt = new_prompt
                    break

        return {
            "prompt": original_prompt,
            "features": answer
        }

    def generate_answer(self, prompt, information):
        """Generate a final answer using the refined prompt and information."""
        final_prompt = (
            f"Using the information provided, generate a response to the following prompt. "
            f"Prompt: '{prompt}', Information: '{information}', Language: '{self.language}'")
        response = self.client.chat.completions.create(model="gpt-4o", temperature=0.01, messages=[{
                                                                                                       "role": "user",
                                                                                                       "content": final_prompt
                                                                                                   }], )
        return response.choices[0].message.content

    def create_embedding(self, text):
        """Generate an embedding for the provided text."""
        embedding_response = self.vs.oai.embeddings.create(model=self.vs.embedding_model,
            input=[text])
        return embedding_response.data[0].embedding

    def retrieve_top_k(self, embedding, k):
        """Retrieve the top K most relevant documents based on the provided embedding."""
        return self.vs.client.search(query_vector=embedding, limit=k,
            collection_name="text-embedding-3-small")

    async def modular(self, req: ModularRagPrompt):
        """Main method for processing the modular RAG request."""
        self.language = req.language
        self.set_user_prompt(req.prompt)
        refined_prompt = self.refine_prompt(self.user_prompt)
        prompt_embedding = self.create_embedding(refined_prompt)
        retrieved_docs = self.retrieve_top_k(prompt_embedding, req.top_k)
        extracted_features = self.extract_features(retrieved_docs)
        filtered_features = self.filter_and_adjust_features(extracted_features, refined_prompt)

        return self.generate_answer(filtered_features["prompt"], filtered_features["features"])
