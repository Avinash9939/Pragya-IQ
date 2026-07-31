from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    """
    Enum representing different user access roles in the system.
    Why: Dictates RBAC permissions across API endpoints.
    """
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"

@dataclass
class User:
    """
    Pure domain User entity.
    Why: Framework-independent representation of a registered user.
    """
    id: int | None
    email: str
    hashed_password: str
    role: UserRole
    created_at: datetime

    def has_role(self, *allowed_roles: UserRole | str) -> bool:
        """
        Helper method to check if the user belongs to allowed roles.
        Why: Simple verification of user privileges.
        """
        # Convert string roles to UserRole enum if they are passed as strings
        converted_roles = {
            r if isinstance(r, UserRole) else UserRole(r)
            for r in allowed_roles
        }
        return self.role in converted_roles
