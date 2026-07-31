from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


class MessageRole(str, Enum):
    """
    Enum for chat message authorship.
    Why: Distinguishes human turns from LLM assistant turns in conversation history.
    """
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class ChatSession:
    """
    Domain entity representing a conversational session tied to a dataset.
    Why: Groups all Q&A turns for a user/dataset pair into a replayable history.
    """
    id: Optional[int]
    user_id: int
    dataset_id: int
    created_at: datetime


@dataclass
class ChatMessage:
    """
    Domain entity representing a single turn in a chat session.
    Why: Persists the grounded question and answer so sessions are resumable.
    """
    id: Optional[int]
    session_id: int
    role: MessageRole
    message: str
    created_at: datetime
