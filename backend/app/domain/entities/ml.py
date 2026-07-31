from dataclasses import dataclass
from datetime import datetime

@dataclass
class MlRun:
    """
    Pure domain entity representing a single machine learning execution run.
    Why: Framework-agnostic baseline tracking of a training run, parameters, and evaluations metrics.
    """
    id: int | None
    dataset_id: int
    model_type: str  # "prophet" | "xgboost"
    params_json: dict
    metrics_json: dict
    created_at: datetime

@dataclass
class MlPrediction:
    """
    Pure domain entity representing a single ML forecast data point.
    Why: Framework-agnostic mapping of predictions (e.g. date target predictions) linked to an ML run.
    """
    id: int | None
    ml_run_id: int
    entity_ref: str  # Date string or category value
    prediction: float
    shap_values_json: dict | None = None
