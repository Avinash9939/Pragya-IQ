from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.infrastructure.db.session import get_db
from app.infrastructure.db.repositories.user_repository import SQLAlchemyUserRepository
from app.services.auth_service import AuthService, EmailAlreadyRegisteredError, InvalidCredentialsError
from app.schemas.user import UserCreate, UserOut
from app.schemas.auth import Token
from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user in the system.
    Why: Handles client request to signup new users and returns user metadata.
    """
    from app.services.activity_log_service import log_activity
    user_repository = SQLAlchemyUserRepository(db)
    auth_service = AuthService(user_repository)
    try:
        user = auth_service.register_user(
            email=user_in.email,
            password=user_in.password,
            role=user_in.role,
        )
        log_activity(db, user.id, "user_registered")
        return user
    except EmailAlreadyRegisteredError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return a JWT access token.
    Why: Implements standard OAuth2 OAuth2PasswordRequestForm matching bearer schemes.
    """
    from app.services.activity_log_service import log_activity
    user_repository = SQLAlchemyUserRepository(db)
    auth_service = AuthService(user_repository)
    try:
        user = auth_service.authenticate_user(
            email=form_data.username,
            password=form_data.password,
        )
        token = create_access_token(subject=user.email, role=user.role.value)
        log_activity(db, user.id, "user_logged_in")
        return {"access_token": token, "token_type": "bearer"}
    except InvalidCredentialsError as e:
        log_activity(db, None, "login_failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
