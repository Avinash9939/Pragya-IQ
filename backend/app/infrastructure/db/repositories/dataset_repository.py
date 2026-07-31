from typing import List, Optional
from sqlalchemy.orm import Session
from app.domain.entities.dataset import Dataset, DatasetStatus
from app.domain.interfaces.dataset_repository import DatasetRepositoryInterface
from app.infrastructure.db.models.dataset_model import DatasetModel

class SQLAlchemyDatasetRepository(DatasetRepositoryInterface):
    """
    SQLAlchemy-based concrete implementation of DatasetRepositoryInterface.
    Why: Handles mapping and transaction context details.
    """
    def __init__(self, db: Session) -> None:
        self.db = db

    def _to_domain(self, model: DatasetModel) -> Dataset:
        """Helper to map SQLAlchemy DB model to pure domain Dataset entity."""
        return Dataset(
            id=model.id,
            user_id=model.user_id,
            filename=model.filename,
            storage_path=model.storage_path,
            row_count=model.row_count,
            column_count=model.column_count,
            status=model.status,
            uploaded_at=model.uploaded_at,
            column_mapping=model.column_mapping
        )

    def _to_model(self, domain: Dataset) -> DatasetModel:
        """Helper to map pure domain Dataset entity to SQLAlchemy DB model."""
        model = DatasetModel(
            user_id=domain.user_id,
            filename=domain.filename,
            storage_path=domain.storage_path,
            row_count=domain.row_count,
            column_count=domain.column_count,
            status=domain.status,
            uploaded_at=domain.uploaded_at,
            column_mapping=domain.column_mapping
        )
        if domain.id is not None:
            model.id = domain.id
        return model

    def create(self, dataset: Dataset) -> Dataset:
        """Inserts a dataset configuration record in DB."""
        model = self._to_model(dataset)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def get_by_id(self, dataset_id: int) -> Optional[Dataset]:
        """Pulls a single dataset tracking record matching ID."""
        model = self.db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
        return self._to_domain(model) if model else None

    def list_by_user(self, user_id: int) -> List[Dataset]:
        """Lookup details for all uploads bound to user ID key."""
        models = self.db.query(DatasetModel).filter(DatasetModel.user_id == user_id).all()
        return [self._to_domain(model) for model in models]

    def update(self, dataset: Dataset) -> Dataset:
        """Update an existing dataset record inside DB."""
        model = self.db.query(DatasetModel).filter(DatasetModel.id == dataset.id).first()
        if not model:
            raise ValueError(f"Dataset with id {dataset.id} not found")
        model.filename = dataset.filename
        model.storage_path = dataset.storage_path
        model.row_count = dataset.row_count
        model.column_count = dataset.column_count
        model.status = dataset.status
        model.column_mapping = dataset.column_mapping
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def update_status(self, dataset_id: int, status: DatasetStatus) -> Optional[Dataset]:
        """Update dataset status profile field matching primary key."""
        model = self.db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
        if model:
            model.status = status
            self.db.commit()
            self.db.refresh(model)
            return self._to_domain(model)
        return None

    def delete(self, dataset_id: int) -> bool:
        """Delete dataset configuration record from DB."""
        model = self.db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
        if model:
            self.db.delete(model)
            self.db.commit()
            return True
        return False
