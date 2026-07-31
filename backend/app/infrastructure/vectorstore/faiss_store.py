import os
from typing import List, Tuple, Any
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings

class LangchainEmbeddingsAdapter(Embeddings):
    """
    Adapter bridging custom EmbeddingClientInterface with LangChain's Embeddings base class.
    Why: FAISS requires a proper LangChain Embeddings subclass so similarity_search_with_score
         can call embed_query() correctly at search time.
    """
    def __init__(self, client: Any) -> None:
        self.client = client

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.client.embed(texts)

    def embed_query(self, text: str) -> List[float]:
        return self.client.embed([text])[0]


class FaissVectorStore:
    """
    Vector Store wrapper persisting document chunks to disk.
    Why: Enables semantic context lookup for RAG querying pipelines.
    """
    def __init__(self, index: FAISS, adapter: LangchainEmbeddingsAdapter) -> None:
        self.index = index
        self.adapter = adapter

    @classmethod
    def chunk_text(cls, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Splits a document text string into fixed-size chunks with overlap."""
        if not text:
            return []
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            if end >= len(text):
                break
            start += (chunk_size - overlap)
        return chunks

    @classmethod
    def build_index(
        cls,
        documents: List[str],
        embedding_client: Any,
        persist_dir: str
    ) -> "FaissVectorStore":
        """
        Splits, embeds, indexes documents, and persists FAISS index files to disk.
        """
        # 1. Break into chunks
        all_chunks = []
        for doc in documents:
            all_chunks.extend(cls.chunk_text(doc))

        if not all_chunks:
            all_chunks = ["Empty dataset index placeholder."]

        # 2. Build FAISS index with a proper LangChain Embeddings adapter
        adapter = LangchainEmbeddingsAdapter(embedding_client)
        index = FAISS.from_texts(texts=all_chunks, embedding=adapter)

        # 3. Save to disk
        os.makedirs(persist_dir, exist_ok=True)
        index.save_local(persist_dir)

        return cls(index, adapter)

    @classmethod
    def load_index(cls, embedding_client: Any, persist_dir: str) -> "FaissVectorStore":
        """Loads a FAISS index from files at directory path."""
        if not os.path.exists(persist_dir):
            raise FileNotFoundError(f"FAISS index not found at dir {persist_dir}")
        adapter = LangchainEmbeddingsAdapter(embedding_client)
        index = FAISS.load_local(persist_dir, adapter, allow_dangerous_deserialization=True)
        return cls(index, adapter)

    def search(self, query: str, embedding_client: Any, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Runs similarity queries using L2 distance.
        Returns: List of tuples (chunk_text, score) — lower score = closer match.
        """
        results = self.index.similarity_search_with_score(query, k=top_k)
        return [(doc.page_content, float(score)) for doc, score in results]
