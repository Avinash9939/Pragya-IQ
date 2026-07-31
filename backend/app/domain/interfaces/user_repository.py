from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.user import User

class UserRepositoryInterface(ABC):
    """
    Abstract interface for user repository database operations.
    Why: Enforces Dependency Inversion so Service layer doesn't depend on SQLAlchemy.
    """

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user entity by their email."""
        pass

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Retrieve a user entity by their ID."""
        pass

    @abstractmethod
    def create(self, user: User) -> User:
        """Persist a new user to the database and return it with assigned ID."""
        pass

    @abstractmethod
    def list_all(self) -> List[User]:
        """Retrieve all users stored in the database."""
        pass
