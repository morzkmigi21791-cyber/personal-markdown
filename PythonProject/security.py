from argon2 import PasswordHasher, exceptions
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os
from cryptography.fernet import Fernet
import base64

ph = PasswordHasher()

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Cookie encryption settings
COOKIE_SECRET_KEY = os.getenv("COOKIE_SECRET_KEY", "your-cookie-secret-key-change-this-in-production")
# Generate a key from the secret
key = base64.urlsafe_b64encode(COOKIE_SECRET_KEY.encode()[:32].ljust(32, b'0'))
fernet = Fernet(key)


def hash_password(plain_password: str) -> str:
    """Return a secure Argon2 hash for the given plain text password."""
    return ph.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify plain password against stored Argon2 hash."""
    try:
        return ph.verify(password_hash, plain_password)
    except exceptions.VerifyMismatchError:
        return False
    except Exception:
        # Any unexpected verification error should be treated as a failure
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def encrypt_cookie(data: str) -> str:
    """Encrypt cookie data."""
    try:
        encrypted_data = fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    except Exception:
        return ""


def decrypt_cookie(encrypted_data: str) -> str:
    """Decrypt cookie data."""
    try:
        decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = fernet.decrypt(decoded_data)
        return decrypted_data.decode()
    except Exception:
        return ""