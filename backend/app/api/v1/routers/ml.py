from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_current_user, require_role
from app.domain.entities.user import User, UserRole
from app.infrastructure.db.session import get_db
from app.infrastructure.db.repositories.dataset_repository import SQLAlchemyDatasetRepository
from app.infrastructure.db.repositories.ml_repository import SQLAlchemyMlRunRepository, SQLAlchemyMlPredictionRepository
from app.infrastructure.storage.local_storage import LocalStorage
from app.services.ml_service import MlService
from app.services.kpi_service import MissingColumnMappingError

router = APIRouter()

class ForecastRequest(BaseModel):
    horizon_days: int = Field(..., gt=0, description="Number of days to forecast into the future")
    model_type: str = Field(..., description="Model to fit: prophet, xgboost, or both")
    cross_val: bool = Field(True, description="Enable cross validation")

class SegmentRequest(BaseModel):
    n_clusters: int = Field(4, gt=0, description="Number of customer segments/clusters to fit")

class ChurnRequest(BaseModel):
    recency_threshold_days: int | None = Field(None, gt=0, description="Optional custom churn recency threshold in days")

class AnomalyRequest(BaseModel):
    contamination: float = Field(0.05, gt=0.0, le=0.5, description="Expected proportion of outliers in the data")

def get_ml_service(db: Session = Depends(get_db)) -> MlService:
    """Dependency injector to construct MlService."""
    dataset_repo = SQLAlchemyDatasetRepository(db)
    ml_run_repo = SQLAlchemyMlRunRepository(db)
    ml_pred_repo = SQLAlchemyMlPredictionRepository(db)
    storage = LocalStorage()
    return MlService(dataset_repo, ml_run_repo, ml_pred_repo, storage)

@router.post("/{dataset_id}/forecast", status_code=status.HTTP_200_OK)
def run_forecast_endpoint(
    dataset_id: int,
    body: ForecastRequest,
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    db: Session = Depends(get_db),
    service: MlService = Depends(get_ml_service)
):
    """
    POST route triggering Prophet/XGBoost demand forecasting pipelines.
    Why: Rejects if permissions or columns mapping are invalid.
    """
    # 1. Verify dataset ownership
    dataset_repo = SQLAlchemyDatasetRepository(db)
    dataset = dataset_repo.get_by_id(dataset_id)
    if not dataset or dataset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )

    # 2. Run service calculations
    try:
        results = service.run_forecast(dataset_id, body.horizon_days, body.model_type, body.cross_val)
        from app.services.activity_log_service import log_activity
        log_activity(db, current_user.id, "ml_run_trained", f"model_type=forecast&dataset_id={dataset_id}")
        return results
    except MissingColumnMappingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during forecasting: {str(e)}"
        )

@router.post("/{dataset_id}/segment", status_code=status.HTTP_200_OK)
def run_segmentation_endpoint(
    dataset_id: int,
    body: SegmentRequest = SegmentRequest(n_clusters=4),
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    db: Session = Depends(get_db),
    service: MlService = Depends(get_ml_service)
):
    """
    POST route triggering KMeans customer segmentation over dataset.
    Why: Rejects if permissions or columns mapping are invalid.
    """
    # 1. Verify dataset ownership
    dataset_repo = SQLAlchemyDatasetRepository(db)
    dataset = dataset_repo.get_by_id(dataset_id)
    if not dataset or dataset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )

    # 2. Run service calculations
    try:
        results = service.run_segmentation(dataset_id, body.n_clusters)
        from app.services.activity_log_service import log_activity
        log_activity(db, current_user.id, "ml_run_trained", f"model_type=segmentation&dataset_id={dataset_id}")
        return results
    except MissingColumnMappingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during customer segmentation: {str(e)}"
        )


@router.post("/{dataset_id}/churn", status_code=status.HTTP_200_OK)
def run_churn_prediction_endpoint(
    dataset_id: int,
    body: ChurnRequest = ChurnRequest(recency_threshold_days=None),
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    db: Session = Depends(get_db),
    service: MlService = Depends(get_ml_service)
):
    """
    POST route triggering XGBoost churn prediction over dataset.
    Why: Rejects if permissions or columns mapping are invalid.
    """
    # 1. Verify dataset ownership
    dataset_repo = SQLAlchemyDatasetRepository(db)
    dataset = dataset_repo.get_by_id(dataset_id)
    if not dataset or dataset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )

    # 2. Run service calculations
    try:
        results = service.run_churn_prediction(dataset_id, body.recency_threshold_days)
        from app.services.activity_log_service import log_activity
        log_activity(db, current_user.id, "ml_run_trained", f"model_type=churn&dataset_id={dataset_id}")
        return results
    except MissingColumnMappingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during churn prediction: {str(e)}"
        )


@router.post("/{dataset_id}/anomaly", status_code=status.HTTP_200_OK)
def run_anomaly_detection_endpoint(
    dataset_id: int,
    body: AnomalyRequest = AnomalyRequest(contamination=0.05),
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    db: Session = Depends(get_db),
    service: MlService = Depends(get_ml_service)
):
    """
    POST route triggering IsolationForest anomaly detection over dataset.
    Why: Rejects if permissions or columns mapping are invalid.
    """
    # 1. Verify dataset ownership
    dataset_repo = SQLAlchemyDatasetRepository(db)
    dataset = dataset_repo.get_by_id(dataset_id)
    if not dataset or dataset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )

    # 2. Run service calculations
    try:
        results = service.run_anomaly_detection(dataset_id, body.contamination)
        from app.services.activity_log_service import log_activity
        log_activity(db, current_user.id, "ml_run_trained", f"model_type=anomaly&dataset_id={dataset_id}")
        return results
    except MissingColumnMappingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during anomaly detection: {str(e)}"
        )


@router.get("/{ml_run_id}/shap/{entity_ref}", status_code=status.HTTP_200_OK)
def get_shap_explanation_endpoint(
    ml_run_id: int,
    entity_ref: str,
    current_user: User = Depends(require_role(UserRole.VIEWER, UserRole.ANALYST, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    GET route retrieving SHAP explainability values for a specific prediction record.
    Why: Visualizes predictive contributions, rejecting Prophet runs with 400 Bad Request.
    """
    # 1. Look up ML Run
    run_repo = SQLAlchemyMlRunRepository(db)
    run = run_repo.get_by_id(ml_run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ML Run with id {ml_run_id} not found"
        )

    # 2. Check for Prophet limitations
    if run.model_type == "prophet":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prophet models are additive time-series models and do not support Tree-based SHAP explainability."
        )

    # 3. Retrieve specific entity prediction
    pred_repo = SQLAlchemyMlPredictionRepository(db)
    # Get all predictions under ml_run_id
    preds = pred_repo.list_by_run_id(ml_run_id)
    target_pred = next((p for p in preds if p.entity_ref == entity_ref), None)
    if not target_pred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prediction for entity_ref '{entity_ref}' not found in ML Run {ml_run_id}"
        )

    # Return explanation payload format
    return {
        "ml_run_id": ml_run_id,
        "entity_ref": entity_ref,
        "prediction_value": target_pred.prediction,
        "explainability": target_pred.shap_values_json
    }
