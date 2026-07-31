from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.infrastructure.db.session import get_db
from app.infrastructure.db.repositories.user_repository import SQLAlchemyUserRepository
from app.core.security import decode_access_token
from app.domain.entities.user import User, UserRole

# OAuth2 scheme configuration pointing to local login route
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency resolving the current authenticated user using JWT tokens.
    Why: Core protection handler verifying claims and mapping request context to domain entities.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception

    user_repository = SQLAlchemyUserRepository(db)
    user = user_repository.get_by_email(email)
    if user is None:
        raise credentials_exception

    return user

class RoleChecker:
    """
    Callable dependency verifying that the authenticated user matches the required roles.
    Why: Centralized authorization mechanism to enforce Role-Based Access Control.
    """
    def __init__(self, allowed_roles: List[UserRole]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for your current access level",
            )
        return current_user

def require_role(*roles: UserRole | str) -> RoleChecker:
    """
    Dependency factory to enforce specific roles.
    Why: Returns a RoleChecker callable to be used inside Depends().
    """
    converted_roles = []
    for r in roles:
        if isinstance(r, str):
            converted_roles.append(UserRole(r))
        else:
            converted_roles.append(r)
    return RoleChecker(converted_roles)
