import os
import io
import shutil
import gc
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from app.infrastructure.llm.embeddings import FakeEmbeddingClient
from app.infrastructure.vectorstore.faiss_store import FaissVectorStore

def robust_rmtree(path, max_retries=5, delay=0.1):
    import gc
    import time
    gc.collect()
    for i in range(max_retries):
        try:
            shutil.rmtree(path)
            return
        except PermissionError:
            if i == max_retries - 1:
                raise
            gc.collect()
            time.sleep(delay)


def test_faiss_vector_store_retrieval():
    docs = [
        "Apple is a premium fruit grown in orchards.",
        "Transaction amount: 15000.0 USD, Date: 2026-03-05. customer id: 102.",
        "Deep learning models require massive GPU clusters to converge efficiently.",
        "Isolation Forest identifies multi-dimensional outliers by isolating tree levels.",
        "FastAPI routes leverage Pydantic models for request validation schemas."
    ]
    fake_client = FakeEmbeddingClient(dimension=64)
    persist_dir = "storage/test_tmp/faiss_index"
    if os.path.exists(persist_dir):
        robust_rmtree(persist_dir)
    try:
        store = FaissVectorStore.build_index(
            documents=docs,
            embedding_client=fake_client,
            persist_dir=persist_dir
        )
        assert os.path.exists(persist_dir)
        assert os.path.exists(
            os.path.join(persist_dir, "index.faiss")
        )
        loaded_store = FaissVectorStore.load_index(
            embedding_client=fake_client,
            persist_dir=persist_dir
        )
        results = loaded_store.search(
            query="Transaction amount: 15000.0 USD, Date: 2026-03-05. customer id: 102.",
            embedding_client=fake_client,
            top_k=2
        )
        assert len(results) > 0
        top_doc, score = results[0]
        assert "customer id: 102" in top_doc
        assert score < 1e-4
    finally:
        if os.path.exists("storage/test_tmp"):
            robust_rmtree("storage/test_tmp")


def test_faiss_chunk_text():
    long_text = "A" * 1200
    chunks = FaissVectorStore.chunk_text(long_text, chunk_size=500, overlap=50)
    assert len(chunks) == 3
    for chunk in chunks:
        assert len(chunk) <= 500


def test_fake_embedding_client_deterministic():
    client = FakeEmbeddingClient(dimension=64)
    text = "Hello world"
    v1 = client.embed([text])[0]
    v2 = client.embed([text])[0]
    assert v1 == v2
    assert len(v1) == 64
    import math
    norm = math.sqrt(sum(x**2 for x in v1))
    assert abs(norm - 1.0) < 1e-6
