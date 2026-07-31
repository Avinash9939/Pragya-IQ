from typing import List, Optional
from sqlalchemy.orm import Session
from app.domain.entities.ml import MlRun, MlPrediction
from app.domain.interfaces.ml_repository import MlRunRepositoryInterface, MlPredictionRepositoryInterface
from app.infrastructure.db.models.ml_model import MlRunModel, MlPredictionModel

class SQLAlchemyMlRunRepository(MlRunRepositoryInterface):
    """
    SQLAlchemy concrete repository implementing MlRunRepositoryInterface.
    Why: Decouples database transactions from domain definitions for ML forecast runs.
    """
    def __init__(self, db: Session) -> None:
        self.db = db

    def _to_domain(self, model: MlRunModel) -> MlRun:
        return MlRun(
            id=model.id,
            dataset_id=model.dataset_id,
            model_type=model.model_type,
            params_json=model.params_json,
            metrics_json=model.metrics_json,
            created_at=model.created_at
        )

    def _to_model(self, domain: MlRun) -> MlRunModel:
        model = MlRunModel(
            dataset_id=domain.dataset_id,
            model_type=domain.model_type,
            params_json=domain.params_json,
            metrics_json=domain.metrics_json,
            created_at=domain.created_at
        )
        if domain.id is not None:
            model.id = domain.id
        return model

    def create(self, run: MlRun) -> MlRun:
        model = self._to_model(run)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def get_by_id(self, run_id: int) -> Optional[MlRun]:
        model = self.db.query(MlRunModel).filter(MlRunModel.id == run_id).first()
        if not model:
            return None
        return self._to_domain(model)

    def list_by_dataset_id(self, dataset_id: int) -> List[MlRun]:
        models = self.db.query(MlRunModel).filter(MlRunModel.dataset_id == dataset_id).all()
        return [self._to_domain(m) for m in models]

class SQLAlchemyMlPredictionRepository(MlPredictionRepositoryInterface):
    """
    SQLAlchemy concrete repository implementing MlPredictionRepositoryInterface.
    Why: Handles batch inserting predictions into the database efficiently.
    """
    def __init__(self, db: Session) -> None:
        self.db = db

    def _to_domain(self, model: MlPredictionModel) -> MlPrediction:
        return MlPrediction(
            id=model.id,
            ml_run_id=model.ml_run_id,
            entity_ref=model.entity_ref,
            prediction=model.prediction,
            shap_values_json=model.shap_values_json
        )

    def _to_model(self, domain: MlPrediction) -> MlPredictionModel:
        model = MlPredictionModel(
            ml_run_id=domain.ml_run_id,
            entity_ref=domain.entity_ref,
            prediction=domain.prediction,
            shap_values_json=domain.shap_values_json
        )
        if domain.id is not None:
            model.id = domain.id
        return model

    def create_batch(self, predictions: List[MlPrediction]) -> List[MlPrediction]:
        models = [self._to_model(p) for p in predictions]
        self.db.add_all(models)
        self.db.commit()
        for m in models:
            self.db.refresh(m)
        return [self._to_domain(m) for m in models]

    def list_by_run_id(self, ml_run_id: int) -> List[MlPrediction]:
        models = self.db.query(MlPredictionModel).filter(MlPredictionModel.ml_run_id == ml_run_id).all()
        return [self._to_domain(m) for m in models]
