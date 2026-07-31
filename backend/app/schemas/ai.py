from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Request body for POST /ai/{dataset_id}/chat."""
    question: str
    session_id: Optional[int] = None


class ChatResponse(BaseModel):
    """Response for a successful chat turn."""
    answer: str
    session_id: int


class MessageOut(BaseModel):
    """Serialized representation of a single ChatMessage turn."""
    id: int
    role: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


class RecommendationsResponse(BaseModel):
    """Response body for recommendations request."""
    dataset_id: int
    recommendations: List[str]
    generated_at: datetime


class ExecutiveSummaryResponse(BaseModel):
    """Response body for executive summary request."""
    dataset_id: int
    summary: str
    generated_at: datetime


class BusinessExplanationRequest(BaseModel):
    prompt: str


class BusinessExplanationResponse(BaseModel):
    explanation: str

