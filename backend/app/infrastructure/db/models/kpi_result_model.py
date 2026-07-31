from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.base import Base

class KpiResultModel(Base):
    """
    SQLAlchemy ORM model representing the "kpi_results" table.
    Why: Handles database mapping for KPI calculation outcomes.
    """
    __tablename__ = "kpi_results"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    kpi_type: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    value_json: Mapped[dict] = mapped_column(sa.JSON, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
