from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.domain.entities.activity_log import ActivityLog
from app.infrastructure.db.repositories.activity_log_repository import SQLAlchemyActivityLogRepository


def log_activity(
    db: Session,
    user_id: Optional[int],
    action: str,
    resource: Optional[str] = None
) -> ActivityLog:
    """
    Helper function to insert a new ActivityLog row.
    Why: Keeps log writing DRY and centrally managed across routers/services.
    """
    repo = SQLAlchemyActivityLogRepository(db)
    log_ent = ActivityLog(
        id=None,
        user_id=user_id,
        action=action,
        resource=resource,
        timestamp=datetime.now(timezone.utc)
    )
    return repo.create(log_ent)
