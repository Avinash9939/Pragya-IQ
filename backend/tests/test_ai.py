import os
import shutil
import gc
from datetime import datetime, timezone
from typing import List, Optional
from app.infrastructure.llm.embeddings import FakeEmbeddingClient
from app.infrastructure.llm.gemini_client import FakeLLMClient
from app.infrastructure.vectorstore.faiss_store import FaissVectorStore
from app.domain.entities.chat import ChatSession, ChatMessage, MessageRole
from app.domain.interfaces.chat_repository import ChatRepositoryInterface
from app.services.ai_service import AIService, SessionOwnershipError


class InMemoryChatRepository(ChatRepositoryInterface):
    """Pure in-memory chat repository for test isolation."""

    def __init__(self):
        self._sessions = {}
        self._messages = {}
        self._next_session_id = 1
        self._next_message_id = 1

    def create_session(self, user_id: int, dataset_id: int) -> ChatSession:
        sid = self._next_session_id
        self._next_session_id += 1
        session = ChatSession(id=sid, user_id=user_id, dataset_id=dataset_id, created_at=datetime.now(timezone.utc))
        self._sessions[sid] = session
        self._messages[sid] = []
        return session

    def get_session(self, session_id: int) -> Optional[ChatSession]:
        return self._sessions.get(session_id)

    def add_message(self, session_id: int, role: MessageRole, message: str) -> ChatMessage:
        mid = self._next_message_id
        self._next_message_id += 1
        msg = ChatMessage(id=mid, session_id=session_id, role=role, message=message, created_at=datetime.now(timezone.utc))
        self._messages[session_id].append(msg)
        return msg

    def list_messages(self, session_id: int) -> List[ChatMessage]:
        return list(self._messages.get(session_id, []))


def robust_cleanup(path):
    gc.collect()
    if os.path.exists(path):
        import time
        for i in range(5):
            try:
                shutil.rmtree(path)
                return
            except PermissionError:
                gc.collect()
                time.sleep(0.1)


def _build_test_index(persist_dir: str):
    docs = [
        "Total revenue for Q1 2026 was 350000 USD across 1400 transactions.",
        "Average transaction amount: 250.0 USD. Peak day: 2026-03-15.",
        "Customer churn rate is 12 percent for the period.",
        "Top product by quantity: Widget A with 520 units sold.",
        "Anomaly detected on 2026-03-20: transaction spike of 3x normal volume."
    ]
    fake_embed = FakeEmbeddingClient(dimension=64)
    if os.path.exists(persist_dir):
        robust_cleanup(persist_dir)
    FaissVectorStore.build_index(documents=docs, embedding_client=fake_embed, persist_dir=persist_dir)
    return fake_embed


def _make_service(base_dir: str, embed_client=None):
    if embed_client is None:
        embed_client = FakeEmbeddingClient(dimension=64)
    llm_client = FakeLLMClient()
    repo = InMemoryChatRepository()
    service = AIService(
        embedding_client=embed_client,
        llm_client=llm_client,
        chat_repo=repo,
        storage_base_dir=base_dir
    )
    return service, llm_client, repo


def test_rag_context_appears_in_prompt():
    """
    Grounding test: the top FAISS chunk MUST appear inside the prompt
    sent to the LLM, proving the model is not called blind.
    """
    base_dir = "storage/test_ai_tmp1"
    persist_dir = f"{base_dir}/1/1/faiss_index"
    embed_client = _build_test_index(persist_dir)
    service, llm_client, _ = _make_service(base_dir, embed_client=embed_client)

    question = "What was the total revenue for Q1 2026?"
    answer, session_id = service.ask(dataset_id=1, user_id=1, question=question)

    assert answer == FakeLLMClient.CANNED_RESPONSE
    assert llm_client.last_prompt is not None
    assert "350000" in llm_client.last_prompt
    assert question in llm_client.last_prompt

    robust_cleanup(base_dir)


def test_messages_persisted_in_order():
    """
    Persistence test: after a single ask(), the repo must contain exactly
    [user, assistant] messages in that order with the correct content.
    """
    base_dir = "storage/test_ai_tmp2"
    persist_dir = f"{base_dir}/1/1/faiss_index"
    embed_client = _build_test_index(persist_dir)
    service, _, repo = _make_service(base_dir, embed_client=embed_client)

    question = "What was the churn rate?"
    answer, session_id = service.ask(dataset_id=1, user_id=1, question=question)

    messages = repo.list_messages(session_id)
    assert len(messages) == 2

    assert messages[0].role == MessageRole.USER
    assert messages[0].message == question

    assert messages[1].role == MessageRole.ASSISTANT
    assert messages[1].message == FakeLLMClient.CANNED_RESPONSE

    robust_cleanup(base_dir)


def test_session_ownership_raises_error():
    """
    Isolation test: asking with another user's session_id raises SessionOwnershipError.
    """
    base_dir = "storage/test_ai_tmp3"
    persist_dir = f"{base_dir}/99/1/faiss_index"
    embed_client = _build_test_index(persist_dir)
    service, _, repo = _make_service(base_dir, embed_client=embed_client)

    owner_session = repo.create_session(user_id=10, dataset_id=1)
    other_user_id = 99

    raised = False
    try:
        service.ask(
            dataset_id=1,
            user_id=other_user_id,
            question="What is the revenue?",
            session_id=owner_session.id
        )
    except SessionOwnershipError:
        raised = True

    assert raised, "Expected SessionOwnershipError when accessing another user session"

    robust_cleanup(base_dir)
