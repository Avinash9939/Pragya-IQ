from datetime import datetime, timezone
from app.domain.entities.user import User, UserRole
from app.domain.interfaces.user_repository import UserRepositoryInterface
from app.core.security import hash_password, verify_password

class EmailAlreadyRegisteredError(Exception):
    """Raised when email registration fails due to duplication."""
    pass

class InvalidCredentialsError(Exception):
    """Raised when email or password authentication fails."""
    pass

class AuthService:
    """
    Service coordinating authentication, user signup, and credential validation.
    Why: Business logic implementation for user access management.
    """
    def __init__(self, user_repo: UserRepositoryInterface) -> None:
        self.user_repo = user_repo

    def register_user(self, email: str, password: str, role: UserRole) -> User:
        """
        Registers a new user inside the system.
        Why: Ensures unique email registration and secures passwords before storing.
        """
        existing_user = self.user_repo.get_by_email(email)
        if existing_user:
            raise EmailAlreadyRegisteredError("Email is already registered")

        hashed = hash_password(password)
        new_user = User(
            id=None,
            email=email,
            hashed_password=hashed,
            role=role,
            created_at=datetime.now(timezone.utc),
        )
        return self.user_repo.create(new_user)

    def authenticate_user(self, email: str, password: str) -> User:
        """
        Authenticates an existing user credentials.
        Why: Validates credentials securely without leaking details on invalid accounts vs bad passwords.
        """
        user = self.user_repo.get_by_email(email)
        if not user:
            raise InvalidCredentialsError("Invalid email or password")

        if not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Invalid email or password")

        return user
