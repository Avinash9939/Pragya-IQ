from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_current_user, require_role
from app.domain.entities.user import User, UserRole
from app.infrastructure.db.session import get_db
from app.infrastructure.db.repositories.dataset_repository import SQLAlchemyDatasetRepository
from app.infrastructure.db.repositories.chat_repository import SQLAlchemyChatRepository
from app.infrastructure.llm.embeddings import EmbeddingClient
from app.infrastructure.llm.gemini_client import GeminiClient
from app.core.config import settings
from app.services.ai_service import AIService, IndexNotFoundError, SessionNotFoundError, SessionOwnershipError
from app.schemas.ai import ChatRequest, ChatResponse, MessageOut, RecommendationsResponse, ExecutiveSummaryResponse, BusinessExplanationRequest, BusinessExplanationResponse

router = APIRouter()


def get_ai_service(db: Session = Depends(get_db)) -> AIService:
    """
    Dependency injector for AIService.
    Why: Wires production embedding/LLM clients and the SQL repositories.
    """
    from app.infrastructure.llm.embeddings import EmbeddingClient, FakeEmbeddingClient
    from app.infrastructure.llm.gemini_client import GeminiClient, FakeLLMClient

    if not settings.gemini_api_key or settings.gemini_api_key == "your_gemini_api_key_here":
        embedding_client = FakeEmbeddingClient(dimension=64)
        llm_client = FakeLLMClient()
    else:
        embedding_client = EmbeddingClient(
            api_key=settings.gemini_api_key,
            model_name=settings.embedding_model_name
        )
        llm_client = GeminiClient(
            api_key=settings.gemini_api_key,
            model_name="gemini-1.5-flash"
        )
    chat_repo = SQLAlchemyChatRepository(db)

    from app.infrastructure.db.repositories.kpi_result_repository import SQLAlchemyKpiResultRepository
    from app.infrastructure.db.repositories.ml_repository import SQLAlchemyMlRunRepository, SQLAlchemyMlPredictionRepository
    from app.infrastructure.db.repositories.ai_output_repository import SQLAlchemyAiOutputRepository

    kpi_repo = SQLAlchemyKpiResultRepository(db)
    ml_run_repo = SQLAlchemyMlRunRepository(db)
    ml_pred_repo = SQLAlchemyMlPredictionRepository(db)
    ai_output_repo = SQLAlchemyAiOutputRepository(db)

    return AIService(
        embedding_client=embedding_client,
        llm_client=llm_client,
        chat_repo=chat_repo,
        kpi_repo=kpi_repo,
        ml_run_repo=ml_run_repo,
        ml_pred_repo=ml_pred_repo,
        ai_output_repo=ai_output_repo
    )


@router.post(
    "/{dataset_id}/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK
)
def chat_with_dataset(
    dataset_id: int,
    body: ChatRequest,
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    service: AIService = Depends(get_ai_service)
):
    """
    POST /ai/{dataset_id}/chat
    Accepts a natural language question, retrieves FAISS context, and returns a grounded LLM answer.
    """
    # Ensure dataset is cleaned or featured
    dataset_repo = SQLAlchemyDatasetRepository(db)
    dataset = dataset_repo.get_by_id(dataset_id)
    if not dataset or dataset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )
    from app.domain.entities.dataset import DatasetStatus
    if dataset.status not in (DatasetStatus.CLEANED, DatasetStatus.FEATURED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data preparation is required before analysis. Please clean the active dataset first."
        )

    try:
        answer, session_id = service.ask(
            dataset_id=dataset_id,
            user_id=current_user.id,
            question=body.question,
            session_id=body.session_id
        )
    except IndexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SessionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SessionOwnershipError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return ChatResponse(answer=answer, session_id=session_id)


@router.get(
    "/{dataset_id}/chat/{session_id}/history",
    response_model=List[MessageOut],
    status_code=status.HTTP_200_OK
)
def get_chat_history(
    dataset_id: int,
    session_id: int,
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    GET /ai/{dataset_id}/chat/{session_id}/history
    Returns all messages for the session. Enforces that the session belongs to the requesting user.
    """
    chat_repo = SQLAlchemyChatRepository(db)
    session = chat_repo.get_session(session_id)
    if session is None or session.dataset_id != dataset_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found.")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted.")
    messages = chat_repo.list_messages(session_id)
    return [
        MessageOut(
            id=m.id,
            role=m.role.value,
            message=m.message,
            created_at=m.created_at
        )
        for m in messages
    ]


@router.get(
    "/{dataset_id}/recommendations",
    response_model=RecommendationsResponse,
    status_code=status.HTTP_200_OK
)
def get_recommendations(
    dataset_id: int,
    regenerate: bool = False,
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    db: Session = Depends(get_db),
    service: AIService = Depends(get_ai_service)
):
    """
    GET /ai/{dataset_id}/recommendations
    Returns grounded, concrete business recommendations calculated from KPIs and ML outputs.
    """
    # 1. Verify dataset ownership
    dataset_repo = SQLAlchemyDatasetRepository(db)
    dataset = dataset_repo.get_by_id(dataset_id)
    if not dataset or dataset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )
    from app.domain.entities.dataset import DatasetStatus
    if dataset.status not in (DatasetStatus.CLEANED, DatasetStatus.FEATURED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data preparation is required before analysis. Please clean the active dataset first."
        )

    recommendations = service.generate_recommendations(dataset_id, regenerate=regenerate)
    
    # Resolve generation timestamp
    cached = service.ai_output_repo.get_latest_by_dataset_and_type(dataset_id, "recommendations")
    generated_at = cached.generated_at if cached else datetime.now(timezone.utc)

    return RecommendationsResponse(
        dataset_id=dataset_id,
        recommendations=recommendations,
        generated_at=generated_at
    )


@router.get(
    "/{dataset_id}/executive-summary",
    response_model=ExecutiveSummaryResponse,
    status_code=status.HTTP_200_OK
)
def get_executive_summary(
    dataset_id: int,
    regenerate: bool = False,
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    db: Session = Depends(get_db),
    service: AIService = Depends(get_ai_service)
):
    """
    GET /ai/{dataset_id}/executive-summary
    Returns a grounded, plain-English summary suitable for business operations.
    """
    # 1. Verify dataset ownership
    dataset_repo = SQLAlchemyDatasetRepository(db)
    dataset = dataset_repo.get_by_id(dataset_id)
    if not dataset or dataset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )
    from app.domain.entities.dataset import DatasetStatus
    if dataset.status not in (DatasetStatus.CLEANED, DatasetStatus.FEATURED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data preparation is required before analysis. Please clean the active dataset first."
        )

    summary = service.generate_executive_summary(dataset_id, regenerate=regenerate)
    
    # Resolve generation timestamp
    cached = service.ai_output_repo.get_latest_by_dataset_and_type(dataset_id, "summary")
    generated_at = cached.generated_at if cached else datetime.now(timezone.utc)

    return ExecutiveSummaryResponse(
        dataset_id=dataset_id,
        summary=summary,
        generated_at=generated_at
    )


@router.post(
    "/{dataset_id}/performance-intelligence/explain",
    response_model=BusinessExplanationResponse,
    status_code=status.HTTP_200_OK
)
def generate_business_explanation(
    dataset_id: int,
    body: BusinessExplanationRequest,
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    db: Session = Depends(get_db),
    service: AIService = Depends(get_ai_service)
):
    """
    POST /ai/{dataset_id}/performance-intelligence/explain
    Returns an AI generated business explanation based on the performance intelligence UI context.
    """
    # 1. Verify dataset ownership
    dataset_repo = SQLAlchemyDatasetRepository(db)
    dataset = dataset_repo.get_by_id(dataset_id)
    if not dataset or dataset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )
    
    explanation = service.llm_client.generate(body.prompt).strip()
    return BusinessExplanationResponse(explanation=explanation)
