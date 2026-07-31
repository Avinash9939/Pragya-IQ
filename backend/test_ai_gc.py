import os
import shutil
import gc
from app.infrastructure.llm.embeddings import FakeEmbeddingClient
from app.infrastructure.vectorstore.faiss_store import FaissVectorStore

PERSIST_DIR = "storage/test_ai_tmp_gc/1/1/faiss_index"

def run_test():
    docs = ["Hello world from test"]
    fake_embed = FakeEmbeddingClient(dimension=64)
    if os.path.exists(PERSIST_DIR):
        try:
            shutil.rmtree("storage/test_ai_tmp_gc")
        except Exception:
            pass

    # Build
    store = FaissVectorStore.build_index(documents=docs, embedding_client=fake_embed, persist_dir=PERSIST_DIR)
    
    # Load and search
    store2 = FaissVectorStore.load_index(embedding_client=fake_embed, persist_dir=PERSIST_DIR)
    print("Search result:", store2.search("Hello", fake_embed))

    # Try deleting it now
    print("Pre-GC delete attempt...")
    try:
        shutil.rmtree("storage/test_ai_tmp_gc")
        print("Pre-GC Delete: Success!")
    except Exception as e:
        print("Pre-GC Delete failed:", e)

    # Let's delete the references and do GC
    del store
    del store2
    gc.collect()

    print("Post-GC delete attempt...")
    try:
        shutil.rmtree("storage/test_ai_tmp_gc")
        print("Post-GC Delete: Success!")
    except Exception as e:
        print("Post-GC Delete failed:", e)

run_test()
