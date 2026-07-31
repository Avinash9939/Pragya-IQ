from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.base import Base
from app.domain.entities.dataset import DatasetStatus

class DatasetModel(Base):
    """
    SQLAlchemy ORM model representing the "datasets" table.
    Why: Records upload transaction, status, shape, and storage destination of datasets.
    """
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(sa.String(512), nullable=False)
    row_count: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    column_count: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    status: Mapped[DatasetStatus] = mapped_column(sa.Enum(DatasetStatus), default=DatasetStatus.UPLOADED, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    column_mapping: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
