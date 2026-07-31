from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.chat import ChatSession, ChatMessage, MessageRole


class ChatRepositoryInterface(ABC):
    """
    Abstract interface for ChatSession and ChatMessage persistence.
    Why: Decouples AI service logic from SQLAlchemy so an in-memory fake can
         be injected during unit tests without needing a DB connection.
    """

    @abstractmethod
    def create_session(self, user_id: int, dataset_id: int) -> ChatSession:
        """Create and persist a new ChatSession."""
        pass

    @abstractmethod
    def get_session(self, session_id: int) -> Optional[ChatSession]:
        """Retrieve a ChatSession by its primary key, or None if not found."""
        pass

    @abstractmethod
    def add_message(
        self,
        session_id: int,
        role: MessageRole,
        message: str
    ) -> ChatMessage:
        """Append a ChatMessage to an existing session."""
        pass

    @abstractmethod
    def list_messages(self, session_id: int) -> List[ChatMessage]:
        """Return all messages for a session ordered by creation time."""
        pass
