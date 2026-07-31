from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.base import Base


class ReportModel(Base):
    """
    SQLAlchemy ORM model representing the "reports" table.
    Why: Handles database mapping for generated PDF report metadata.
    """
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    file_path: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
