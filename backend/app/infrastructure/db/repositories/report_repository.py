from typing import Optional
from sqlalchemy.orm import Session
from app.domain.entities.report import Report
from app.domain.interfaces.report_repository import ReportRepositoryInterface
from app.infrastructure.db.models.report_model import ReportModel


class SQLAlchemyReportRepository(ReportRepositoryInterface):
    """
    SQLAlchemy-based concrete implementation of ReportRepositoryInterface.
    Why: Handles mapping and database transactions for generated PDF report metadata.
    """
    def __init__(self, db: Session) -> None:
        self.db = db

    def _to_domain(self, model: ReportModel) -> Report:
        """Helper to map SQLAlchemy DB model to pure domain Report entity."""
        return Report(
            id=model.id,
            dataset_id=model.dataset_id,
            file_path=model.file_path,
            generated_at=model.generated_at
        )

    def _to_model(self, domain: Report) -> ReportModel:
        """Helper to map pure domain Report entity to SQLAlchemy DB model."""
        model = ReportModel(
            dataset_id=domain.dataset_id,
            file_path=domain.file_path,
            generated_at=domain.generated_at
        )
        if domain.id is not None:
            model.id = domain.id
        return model

    def create(self, report: Report) -> Report:
        """Create a new report metadata entry."""
        model = self._to_model(report)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def get_by_id(self, report_id: int) -> Optional[Report]:
        """Lookup stored report metadata matching target id."""
        model = self.db.query(ReportModel).filter(ReportModel.id == report_id).first()
        if not model:
            return None
        return self._to_domain(model)
