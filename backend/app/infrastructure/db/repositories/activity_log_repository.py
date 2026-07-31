from typing import List
from sqlalchemy.orm import Session
from app.domain.entities.activity_log import ActivityLog
from app.domain.interfaces.activity_log_repository import ActivityLogRepositoryInterface
from app.infrastructure.db.models.activity_log_model import ActivityLogModel


class SQLAlchemyActivityLogRepository(ActivityLogRepositoryInterface):
    """
    SQLAlchemy-based concrete implementation of ActivityLogRepositoryInterface.
    Why: Handles mapping and database transactions for audit logs.
    """
    def __init__(self, db: Session) -> None:
        self.db = db

    def _to_domain(self, model: ActivityLogModel) -> ActivityLog:
        """Helper to map SQLAlchemy DB model to pure domain ActivityLog entity."""
        return ActivityLog(
            id=model.id,
            user_id=model.user_id,
            action=model.action,
            resource=model.resource,
            timestamp=model.timestamp
        )

    def _to_model(self, domain: ActivityLog) -> ActivityLogModel:
        """Helper to map pure domain ActivityLog entity to SQLAlchemy DB model."""
        model = ActivityLogModel(
            user_id=domain.user_id,
            action=domain.action,
            resource=domain.resource,
            timestamp=domain.timestamp
        )
        if domain.id is not None:
            model.id = domain.id
        return model

    def create(self, log: ActivityLog) -> ActivityLog:
        """Create a new activity log entry."""
        model = self._to_model(log)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def get_paginated(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[ActivityLog]:
        """Fetch logs sorted by timestamp descending, paginated."""
        models = (
            self.db.query(ActivityLogModel)
            .order_by(ActivityLogModel.timestamp.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [self._to_domain(m) for m in models]
