from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import bcrypt
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings

# Workaround for compatibility between passlib and bcrypt >= 4.0.0
# passlib's internal tests verify BSD wraparound bug using 255-byte passwords,
# which raises ValueError in newer bcrypt versions.
orig_hashpw = bcrypt.hashpw
def patched_hashpw(password, salt):
    if len(password) > 72:
        password = password[:72]
    return orig_hashpw(password, salt)
bcrypt.hashpw = patched_hashpw

# Initialize Passlib context for secure bcrypt password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.
    Why: Prevents raw passwords from being stored in the database.
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against its bcrypt hash.
    Why: Used to authenticate users upon login.
    """
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(
    subject: str,
    role: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a signed JWT access token containing subject (email) and user role.
    Why: Identifies authenticated users and roles in subsequent stateless API calls.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode = {
        "sub": str(subject),
        "role": str(role),
        "exp": expire
    }
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)

def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """
    Decode and validate a JWT access token.
    Why: Extract identity and role claims from requests securely.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
