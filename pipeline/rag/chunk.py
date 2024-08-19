from hashlib import sha3_256

from dotenv import dotenv_values
from langchain_text_splitters import TokenTextSplitter
from tiktoken import get_encoding


class Chunking:
    def __init__(self):
        # Load chunk size from environment variable, with a default value if not set
        self.chunk_size = int(dotenv_values("../../.env").get("CHUNK_SIZE", 1000))
        self.chunk_overlap = int(dotenv_values("../../.env").get("CHUNK_OVERLAP", 2))
        self.chunks = []
        self.reminder = 0
        self.encoding = get_encoding("cl100k_base")
        self.text = ""
        self.text_encoded = []
        self._checksum = ""

    def to_readable(self):
        if len(self.chunks) == 0:
            raise RuntimeError("No chunks found!")
        return self.text

    def tokenise(self, text):
        """Tokenize a string or a list/tuple of strings into tokens."""

        if isinstance(text, str):
            self.text = text
            self.text_encoded = self.encoding.encode(text)
        elif isinstance(text, (list, tuple)):
            self.text = str(map("".join, text))
            self.text_encoded = self.encoding.encode(self.text)

        else:
            raise TypeError("Input must be a str, list, or tuple")

    def chunk(self):
        self.from_tokens(self.text_encoded)

    def from_tokens(self, tokens):
        """Chunk tokens using Langchain's TokenTextSplitter."""
        if not isinstance(tokens, (list, tuple)):
            raise TypeError("Tokens must be a list or tuple")

        # Convert tokens to a single string with a space separating them (since the splitter works with strings)
        combined_text = " ".join(map(str, tokens))

        # Use TokenTextSplitter to split based on token count
        text_splitter = TokenTextSplitter(
            chunk_size=self.chunk_size,
            encoding_name="cl100k_base",
            chunk_overlap=self.chunk_overlap,
            allowed_special="all",
        )
        self.chunks = text_splitter.split_text(combined_text)

        return self.chunks

    def __iter__(self):
        return iter(self.chunks)

    def __len__(self):
        return len(self.chunks)

    def __getitem__(self, index):
        return self.chunks[index]

    def __next__(self):
        if self.reminder >= len(self.chunks):
            self.reminder = 0
            raise StopIteration
        result = self.chunks[self.reminder]
        self.reminder += 1
        return result

    def append(self, chunk):
        if isinstance(chunk, Chunking):
            self.chunks.append(chunk.chunks)
        else:
            return NotImplemented

    def __str__(self):
        return self.text

    def __hash__(self):
        return int(sha3_256(str(self.text).encode("utf-8")).hexdigest(), 16)

    def __eq__(self, other):
        if isinstance(other, Chunking):
            return hash(self) == hash(other)
        if isinstance(other, str):
            return self.text == other
        if isinstance(other, (list, tuple)):
            return self.chunks == other
        return NotImplemented