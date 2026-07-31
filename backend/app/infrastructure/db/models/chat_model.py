from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.base import Base
from app.domain.entities.chat import MessageRole


class ChatSessionModel(Base):
    """
    SQLAlchemy ORM model for the chat_sessions table.
    Why: Persists a user/dataset conversation context for multi-turn Q&A.
    """
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        sa.Integer,
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    dataset_id: Mapped[int] = mapped_column(
        sa.Integer,
        sa.ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class ChatMessageModel(Base):
    """
    SQLAlchemy ORM model for the chat_messages table.
    Why: Stores individual turns (user question + assistant answer) per session.
    """
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    chat_session_id: Mapped[int] = mapped_column(
        sa.Integer,
        sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role: Mapped[str] = mapped_column(
        sa.Enum(MessageRole, name="messagerole"),
        nullable=False
    )
    message: Mapped[str] = mapped_column(sa.Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
