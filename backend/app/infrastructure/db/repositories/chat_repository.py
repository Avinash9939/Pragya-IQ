from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.domain.entities.chat import ChatSession, ChatMessage, MessageRole
from app.domain.interfaces.chat_repository import ChatRepositoryInterface
from app.infrastructure.db.models.chat_model import ChatSessionModel, ChatMessageModel


class SQLAlchemyChatRepository(ChatRepositoryInterface):
    """
    SQLAlchemy-based concrete implementation of ChatRepositoryInterface.
    Why: Handles ORM mapping and DB transactions for chat sessions and messages.
    """
    def __init__(self, db: Session) -> None:
        self.db = db

    def _session_to_domain(self, m: ChatSessionModel) -> ChatSession:
        return ChatSession(id=m.id, user_id=m.user_id, dataset_id=m.dataset_id, created_at=m.created_at)

    def _message_to_domain(self, m: ChatMessageModel) -> ChatMessage:
        return ChatMessage(
            id=m.id,
            session_id=m.chat_session_id,
            role=MessageRole(m.role),
            message=m.message,
            created_at=m.created_at
        )

    def create_session(self, user_id: int, dataset_id: int) -> ChatSession:
        """Create and persist a new ChatSession row."""
        model = ChatSessionModel(
            user_id=user_id,
            dataset_id=dataset_id,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._session_to_domain(model)

    def get_session(self, session_id: int) -> Optional[ChatSession]:
        """Retrieve a ChatSession by primary key."""
        model = self.db.query(ChatSessionModel).filter(
            ChatSessionModel.id == session_id
        ).first()
        return self._session_to_domain(model) if model else None

    def add_message(self, session_id: int, role: MessageRole, message: str) -> ChatMessage:
        """Append a message turn to an existing session."""
        model = ChatMessageModel(
            chat_session_id=session_id,
            role=role,
            message=message,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._message_to_domain(model)

    def list_messages(self, session_id: int) -> List[ChatMessage]:
        """Return all messages for a session ordered by created_at."""
        models = self.db.query(ChatMessageModel).filter(
            ChatMessageModel.chat_session_id == session_id
        ).order_by(ChatMessageModel.created_at).all()
        return [self._message_to_domain(m) for m in models]
