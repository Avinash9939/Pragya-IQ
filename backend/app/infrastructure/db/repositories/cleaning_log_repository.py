from typing import List
from sqlalchemy.orm import Session
from app.domain.entities.cleaning_log import CleaningLog
from app.domain.interfaces.cleaning_log_repository import CleaningLogRepositoryInterface
from app.infrastructure.db.models.cleaning_log_model import CleaningLogModel

class SQLAlchemyCleaningLogRepository(CleaningLogRepositoryInterface):
    """
    SQLAlchemy-based concrete implementation of CleaningLogRepositoryInterface.
    Why: Handles mapping and database transactions for audits logic.
    """
    def __init__(self, db: Session) -> None:
        self.db = db

    def _to_domain(self, model: CleaningLogModel) -> CleaningLog:
        """Helper to map SQLAlchemy DB model to pure domain CleaningLog entity."""
        return CleaningLog(
            id=model.id,
            dataset_id=model.dataset_id,
            operation=model.operation,
            details=model.details,
            executed_at=model.executed_at
        )

    def _to_model(self, domain: CleaningLog) -> CleaningLogModel:
        """Helper to map pure domain CleaningLog entity to SQLAlchemy DB model."""
        model = CleaningLogModel(
            dataset_id=domain.dataset_id,
            operation=domain.operation,
            details=domain.details,
            executed_at=domain.executed_at
        )
        if domain.id is not None:
            model.id = domain.id
        return model

    def create(self, log: CleaningLog) -> CleaningLog:
        """Create a new cleaning log audit record."""
        model = self._to_model(log)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def get_by_dataset_id(self, dataset_id: int) -> List[CleaningLog]:
        """Lookup all cleaning log events recorded for a specific dataset."""
        models = self.db.query(CleaningLogModel).filter(CleaningLogModel.dataset_id == dataset_id).all()
        return [self._to_domain(model) for model in models]
