from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.base import Base


class AiOutputModel(Base):
    """
    SQLAlchemy ORM model representing the "ai_outputs" table.
    Why: Handles database mapping for cached recommendations and executive summaries.
    """
    __tablename__ = "ai_outputs"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    output_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    content_json: Mapped[dict] = mapped_column(sa.JSON, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    __table_args__ = (
        sa.Index("ix_ai_outputs_dataset_id_output_type", "dataset_id", "output_type"),
    )
