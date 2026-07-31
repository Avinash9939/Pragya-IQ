from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.db.base import Base

class MlRunModel(Base):
    """
    SQLAlchemy ORM model representing the "ml_runs" table.
    Why: Tracks model parameters and metrics for machine learning forecast runs.
    """
    __tablename__ = "ml_runs"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    model_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    params_json: Mapped[dict] = mapped_column(sa.JSON, nullable=False)
    metrics_json: Mapped[dict] = mapped_column(sa.JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    predictions: Mapped[list["MlPredictionModel"]] = relationship(
        "MlPredictionModel",
        back_populates="ml_run",
        cascade="all, delete-orphan"
    )

class MlPredictionModel(Base):
    """
    SQLAlchemy ORM model representing the "ml_predictions" table.
    Why: Stores forecasted data points mapped to a specific training run.
    """
    __tablename__ = "ml_predictions"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    ml_run_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("ml_runs.id", ondelete="CASCADE"), nullable=False)
    entity_ref: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    prediction: Mapped[float] = mapped_column(sa.Float, nullable=False)
    shap_values_json: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)

    ml_run: Mapped[MlRunModel] = relationship("MlRunModel", back_populates="predictions")
