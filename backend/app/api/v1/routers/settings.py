from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_current_user, require_role
from app.domain.entities.user import User, UserRole
from app.infrastructure.db.session import get_db
from app.services.system_setting_service import SystemSettingService
from app.schemas.system_setting import SystemSettingsResponse, SystemSettingsUpdate

router = APIRouter(prefix="/settings", tags=["System Settings"])


@router.get("", response_model=SystemSettingsResponse, status_code=status.HTTP_200_OK)
def get_system_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    GET /api/v1/settings
    Retrieve system configurations. Accessible by any authenticated user.
    Why: Allows frontend and clients to read feature toggles (like maintenance mode).
    """
    service = SystemSettingService(db)
    m_mode = service.get_bool_setting("maintenance_mode", default=False)
    return {"maintenance_mode": m_mode}


@router.put("", response_model=SystemSettingsResponse, status_code=status.HTTP_200_OK)
def update_system_settings(
    body: SystemSettingsUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    PUT /api/v1/settings
    Update system configuration settings. Restricted to Admin role.
    Why: Admin can safely toggle system status variables dynamically.
    """
    service = SystemSettingService(db)
    service.set_setting("maintenance_mode", "true" if body.maintenance_mode else "false")
    return {"maintenance_mode": body.maintenance_mode}
