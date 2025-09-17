from argon2 import PasswordHasher, exceptions
from jose import JWTError, jwt
import os
from cryptography.fernet import Fernet
import base64

ph = PasswordHasher()

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "@37!34Hif77+UIfgE22&&1#eee2EC1#$")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Cookie encryption settings
COOKIE_SECRET_KEY = os.getenv("COOKIE_SECRET_KEY", "&193##82jddS2h@ff#hk-+rfb##@2@1")
# Generate a key from the secret
key = base64.urlsafe_b64encode(COOKIE_SECRET_KEY.encode()[:32].ljust(32, b'0'))
fernet = Fernet(key)


def hash_password(plain_password: str) -> str:
    return ph.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return ph.verify(password_hash, plain_password)
    except exceptions.VerifyMismatchError:
        return False
    except Exception:
        return False