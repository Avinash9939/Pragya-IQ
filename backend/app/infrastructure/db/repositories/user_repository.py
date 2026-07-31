from typing import List, Optional
from sqlalchemy.orm import Session
from app.domain.entities.user import User
from app.domain.interfaces.user_repository import UserRepositoryInterface
from app.infrastructure.db.models.user_model import UserModel

class SQLAlchemyUserRepository(UserRepositoryInterface):
    """
    Concrete repository implementation of UserRepositoryInterface mapping entities to database items.
    Why: Handles ORM transaction bounds and separates database mappings from pure domain concepts.
    """
    def __init__(self, db: Session) -> None:
        self.db = db

    def _to_domain(self, model: UserModel) -> User:
        """Map SQLAlchemy UserModel to pure domain User entity."""
        return User(
            id=model.id,
            email=model.email,
            hashed_password=model.hashed_password,
            role=model.role,
            created_at=model.created_at,
        )

    def _to_model(self, domain: User) -> UserModel:
        """Map domain User entity to SQLAlchemy UserModel."""
        model = UserModel(
            email=domain.email,
            hashed_password=domain.hashed_password,
            role=domain.role,
            created_at=domain.created_at,
        )
        if domain.id is not None:
            model.id = domain.id
        return model

    def get_by_email(self, email: str) -> Optional[User]:
        """Lookup database record matching input email string."""
        model = self.db.query(UserModel).filter(UserModel.email == email).first()
        return self._to_domain(model) if model else None

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Lookup database record matching input user primary ID key."""
        model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        return self._to_domain(model) if model else None

    def create(self, user: User) -> User:
        """Saves a user record to the relational database structure."""
        model = self._to_model(user)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def list_all(self) -> List[User]:
        """Lookup all records inside database mapping table."""
        models = self.db.query(UserModel).all()
        return [self._to_domain(model) for model in models]
