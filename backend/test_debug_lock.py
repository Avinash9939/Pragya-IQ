import os
import shutil
import gc
import sys
from app.infrastructure.llm.embeddings import FakeEmbeddingClient
from app.infrastructure.llm.gemini_client import FakeLLMClient
from app.infrastructure.vectorstore.faiss_store import FaissVectorStore
from app.domain.entities.chat import ChatSession, ChatMessage, MessageRole
from app.services.ai_service import AIService
from tests.test_ai import InMemoryChatRepository

PERSIST_DIR = "storage/test_ai_tmp/1/1/faiss_index"

def _build_test_index():
    docs = [
        "Total revenue for Q1 2026 was 350000 USD across 1400 transactions.",
        "Average transaction amount: 250.0 USD. Peak day: 2026-03-15.",
        "Customer churn rate is 12 percent for the period.",
        "Top product by quantity: Widget A with 520 units sold.",
        "Anomaly detected on 2026-03-20: transaction spike of 3x normal volume."
    ]
    fake_embed = FakeEmbeddingClient(dimension=64)
    if os.path.exists(PERSIST_DIR):
        shutil.rmtree(PERSIST_DIR)
    FaissVectorStore.build_index(documents=docs, embedding_client=fake_embed, persist_dir=PERSIST_DIR)
    return fake_embed

def _make_service(embed_client):
    llm_client = FakeLLMClient()
    repo = InMemoryChatRepository()
    service = AIService(
        embedding_client=embed_client,
        llm_client=llm_client,
        chat_repo=repo,
        storage_base_dir="storage/test_ai_tmp"
    )
    return service, llm_client, repo

def run():
    print("Building index...")
    embed_client = _build_test_index()
    service, llm_client, repo = _make_service(embed_client)

    print("Running ask...")
    answer, session_id = service.ask(dataset_id=1, user_id=1, question="What was the total revenue?")

    print("Checking gc objects before clean...")
    # Let's inspect objects in gc.get_objects() that are FAISS or FaissVectorStore
    for obj in gc.get_objects():
        try:
            if "Faiss" in type(obj).__name__ or "FAISS" in type(obj).__name__:
                print(f"Found alive object in GC: {type(obj)} at {hex(id(obj))}")
                referrers = gc.get_referrers(obj)
                print(f"  Referrers count: {len(referrers)}")
                for r in referrers:
                    if isinstance(r, dict):
                        print(f"    Referrer keys: {list(r.keys())[:5]}")
                    else:
                        print(f"    Referrer type: {type(r)}")
        except Exception:
            pass

    print("Running gc.collect()...")
    num_collected = gc.collect()
    print(f"Collected {num_collected} objects.")

    print("Attempting to delete directory...")
    try:
        shutil.rmtree("storage/test_ai_tmp")
        print("DELETE SUCCESSFUL!")
    except Exception as e:
        print("DELETE FAILED:", e)

run()
