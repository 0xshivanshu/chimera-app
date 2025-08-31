# auth_utils.py
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from config import JWT_SECRET_KEY, JWT_ALGORITHM

# This part remains the same
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# --- NEW JWT FUNCTION ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Creates a new JWT access token.
    """
    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY is not configured in the environment.")
        
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Default token expiry: 1 day
        expire = datetime.now(timezone.utc) + timedelta(days=1)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt