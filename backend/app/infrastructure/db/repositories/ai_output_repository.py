from typing import Optional
from sqlalchemy.orm import Session
from app.domain.entities.ai_output import AiOutput
from app.domain.interfaces.ai_output_repository import AiOutputRepositoryInterface
from app.infrastructure.db.models.ai_output_model import AiOutputModel


class SQLAlchemyAiOutputRepository(AiOutputRepositoryInterface):
    """
    SQLAlchemy-based concrete implementation of AiOutputRepositoryInterface.
    Why: Handles mapping and database transactions for cached recommendation/summary outcomes.
    """
    def __init__(self, db: Session) -> None:
        self.db = db

    def _to_domain(self, model: AiOutputModel) -> AiOutput:
        """Helper to map SQLAlchemy DB model to pure domain AiOutput entity."""
        return AiOutput(
            id=model.id,
            dataset_id=model.dataset_id,
            output_type=model.output_type,
            content_json=model.content_json,
            generated_at=model.generated_at
        )

    def _to_model(self, domain: AiOutput) -> AiOutputModel:
        """Helper to map pure domain AiOutput entity to SQLAlchemy DB model."""
        model = AiOutputModel(
            dataset_id=domain.dataset_id,
            output_type=domain.output_type,
            content_json=domain.content_json,
            generated_at=domain.generated_at
        )
        if domain.id is not None:
            model.id = domain.id
        return model

    def create(self, ai_output: AiOutput) -> AiOutput:
        """Create or update cached AI output."""
        # Upsert: check if already exists to prevent duplicate types per dataset in the DB
        existing = self.db.query(AiOutputModel).filter(
            AiOutputModel.dataset_id == ai_output.dataset_id,
            AiOutputModel.output_type == ai_output.output_type
        ).first()

        if existing:
            existing.content_json = ai_output.content_json
            existing.generated_at = ai_output.generated_at
            self.db.commit()
            self.db.refresh(existing)
            return self._to_domain(existing)

        model = self._to_model(ai_output)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def get_latest_by_dataset_and_type(self, dataset_id: int, output_type: str) -> Optional[AiOutput]:
        """Lookup stored AI outcome matching parameters."""
        model = self.db.query(AiOutputModel).filter(
            AiOutputModel.dataset_id == dataset_id,
            AiOutputModel.output_type == output_type
        ).order_by(AiOutputModel.generated_at.desc()).first()
        if not model:
            return None
        return self._to_domain(model)
