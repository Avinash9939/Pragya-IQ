from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.base import Base


class ActivityLogModel(Base):
    """
    SQLAlchemy ORM model representing the "activity_logs" table.
    Why: Handles database mapping for audit logs.
    """
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    resource: Mapped[str] = mapped_column(sa.String(255), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
