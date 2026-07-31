from typing import List, Optional
from sqlalchemy.orm import Session
from app.domain.entities.kpi_result import KpiResult
from app.domain.interfaces.kpi_result_repository import KpiResultRepositoryInterface
from app.infrastructure.db.models.kpi_result_model import KpiResultModel

class SQLAlchemyKpiResultRepository(KpiResultRepositoryInterface):
    """
    SQLAlchemy-based concrete implementation of KpiResultRepositoryInterface.
    Why: Handles mapping and database transactions for KPI result outcomes.
    """
    def __init__(self, db: Session) -> None:
        self.db = db

    def _to_domain(self, model: KpiResultModel) -> KpiResult:
        """Helper to map SQLAlchemy DB model to pure domain KpiResult entity."""
        return KpiResult(
            id=model.id,
            dataset_id=model.dataset_id,
            kpi_type=model.kpi_type,
            value_json=model.value_json,
            computed_at=model.computed_at
        )

    def _to_model(self, domain: KpiResult) -> KpiResultModel:
        """Helper to map pure domain KpiResult entity to SQLAlchemy DB model."""
        model = KpiResultModel(
            dataset_id=domain.dataset_id,
            kpi_type=domain.kpi_type,
            value_json=domain.value_json,
            computed_at=domain.computed_at
        )
        if domain.id is not None:
            model.id = domain.id
        return model

    def create(self, result: KpiResult) -> KpiResult:
        """Create or update KPI result."""
        # Upsert: check if already exists to prevent duplicate types per dataset in the DB
        existing = self.db.query(KpiResultModel).filter(
            KpiResultModel.dataset_id == result.dataset_id,
            KpiResultModel.kpi_type == result.kpi_type
        ).first()

        if existing:
            existing.value_json = result.value_json
            existing.computed_at = result.computed_at
            self.db.commit()
            self.db.refresh(existing)
            return self._to_domain(existing)
        
        model = self._to_model(result)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def get_by_dataset_id_and_type(self, dataset_id: int, kpi_type: str) -> Optional[KpiResult]:
        """Lookup stored KPI outcome matching parameters."""
        model = self.db.query(KpiResultModel).filter(
            KpiResultModel.dataset_id == dataset_id,
            KpiResultModel.kpi_type == kpi_type
        ).first()
        if not model:
            return None
        return self._to_domain(model)

    def list_by_dataset_id(self, dataset_id: int) -> List[KpiResult]:
        """List all KPI metrics computed for a target dataset."""
        models = self.db.query(KpiResultModel).filter(KpiResultModel.dataset_id == dataset_id).all()
        return [self._to_domain(model) for model in models]
