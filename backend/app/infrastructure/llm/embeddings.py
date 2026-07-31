import hashlib
import numpy as np
from typing import List
from abc import ABC, abstractmethod
from langchain_google_genai import GoogleGenerativeAIEmbeddings


class EmbeddingClientInterface(ABC):
    """
    Abstract interface for generating text embeddings.
    Why: Swappable for fake implementations during isolated unit tests.
    """
    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        pass


class LLMClientInterface(ABC):
    """
    Abstract interface for generating LLM text completions.
    Why: Swappable for FakeLLMClient during isolated unit tests.
    """
    @abstractmethod
    def generate(self, prompt: str) -> str:
        pass


class EmbeddingClient(EmbeddingClientInterface):
    """
    Production embedding client wrapping Google GenAI embeddings using LangChain.
    Why: Creates semantic representation vectors using Google's embedding model.
    """
    def __init__(self, api_key: str, model_name: str = "models/embedding-001") -> None:
        self.embeddings = GoogleGenerativeAIEmbeddings(
            google_api_key=api_key,
            model=model_name
        )

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Invokes Gemini Embedding API for the list of texts."""
        return self.embeddings.embed_documents(texts)


class FakeEmbeddingClient(EmbeddingClientInterface):
    """
    Deterministic Mock embedding client for unit test isolation.
    Why: Prevents external network calls while returning consistent vector dimensions.
    """
    def __init__(self, dimension: int = 768) -> None:
        self.dimension = dimension

    def embed(self, texts: List[str]) -> List[List[float]]:
        results = []
        for txt in texts:
            h = hashlib.sha256(txt.encode("utf-8")).digest()
            seed = int.from_bytes(h[:4], "big")
            rng = np.random.default_rng(seed)
            vec = rng.normal(size=self.dimension)
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            results.append(vec.tolist())
        return results
