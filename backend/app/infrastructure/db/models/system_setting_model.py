from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.base import Base


class SystemSettingModel(Base):
    """
    SQLAlchemy ORM model representing the "system_settings" table.
    Why: Handles database mapping for key-value configuration flags.
    """
    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(sa.String(100), primary_key=True, nullable=False)
    value: Mapped[str] = mapped_column(sa.Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
