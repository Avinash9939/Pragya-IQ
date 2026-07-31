from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.domain.entities.user import UserRole

class UserCreate(BaseModel):
    """
    Schema for user registration requests.
    Why: Validates signup input payload.
    """
    email: EmailStr
    password: str = Field(..., min_length=6, description="Plaintext password, minimum 6 characters")
    role: UserRole = Field(default=UserRole.VIEWER, description="Assigned role for the user")

class UserOut(BaseModel):
    """
    Schema for user details responses.
    Why: Completely excludes the hashed_password field in JSON responses to avoid security issues.
    """
    id: int
    email: EmailStr
    role: UserRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
