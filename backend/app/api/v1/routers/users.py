from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_current_user, require_role
from app.domain.entities.user import User, UserRole
from app.infrastructure.db.session import get_db
from app.infrastructure.db.repositories.user_repository import SQLAlchemyUserRepository
from app.infrastructure.db.models.user_model import UserModel
from app.schemas.user import UserOut

router = APIRouter(prefix="/users", tags=["Users Admin"])


class RoleUpdateRequest(BaseModel):
    role: UserRole = Field(..., description="Target role to assign to the user")


@router.get("/me", response_model=UserOut, status_code=status.HTTP_200_OK)
def get_me(current_user: User = Depends(get_current_user)):
    """
    GET /api/v1/users/me
    Retrieves the profile details of the current authenticated user.
    Why: Standard profiling/identity inspection for client side apps.
    """
    return current_user


@router.get("", response_model=List[UserOut], status_code=status.HTTP_200_OK)
def list_users(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    GET /api/v1/users
    Retrieves a list of all users in the system. Restricted to Admin role.
    Why: Administrative user directory browsing.
    """
    repo = SQLAlchemyUserRepository(db)
    return repo.list_all()


@router.put("/{id}/role", response_model=UserOut, status_code=status.HTTP_200_OK)
def update_user_role(
    id: int,
    body: RoleUpdateRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    PUT /api/v1/users/{id}/role
    Modify target user's role. Restricted to Admin role.
    Why: Handles administrative promotions or demotions, logging the operation.
    """
    user_model = db.query(UserModel).filter(UserModel.id == id).first()
    if not user_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {id} not found"
        )

    old_role = user_model.role
    user_model.role = body.role
    db.commit()
    db.refresh(user_model)

    # Convert to domain
    repo = SQLAlchemyUserRepository(db)
    user_domain = repo.get_by_id(id)

    # Log activity
    from app.services.activity_log_service import log_activity
    log_activity(
        db,
        current_user.id,
        "user_role_changed",
        f"target_user_id={id}&old_role={old_role.value}&new_role={body.role.value}"
    )

    return user_domain
