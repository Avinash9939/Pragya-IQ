from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.base import Base

class CleaningLogModel(Base):
    """
    SQLAlchemy ORM model representing the "cleaning_logs" table.
    Why: Audits data cleaning operations and logs detail files metadata.
    """
    __tablename__ = "cleaning_logs"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    operation: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    details: Mapped[dict] = mapped_column(sa.JSON, nullable=False)
    executed_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
