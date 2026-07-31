from pydantic import BaseModel

class Token(BaseModel):
    """
    Authentication success JWT token schema.
    Why: Defines login response payload configuration.
    """
    access_token: str
    token_type: str = "bearer"
