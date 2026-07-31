from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.api.v1.dependencies import require_role
from app.domain.entities.user import User, UserRole
from app.infrastructure.db.session import get_db
from app.infrastructure.db.repositories.activity_log_repository import SQLAlchemyActivityLogRepository
from app.schemas.activity_log import ActivityLogOut

router = APIRouter(prefix="/logs", tags=["Admin Logs"])


@router.get("", response_model=List[ActivityLogOut], status_code=status.HTTP_200_OK)
def get_activity_logs(
    limit: int = Query(50, ge=1, le=200, description="Retrieve up to this number of logs"),
    offset: int = Query(0, ge=0, description="Skip this number of logs"),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    GET /api/v1/logs
    Fetch system audit trail logs. Paginated and restricted to Admin role.
    Why: Keeps system operations completely transparent for regulatory and security reviews.
    """
    repo = SQLAlchemyActivityLogRepository(db)
    logs = repo.get_paginated(limit=limit, offset=offset)
    return logs
