from argon2 import PasswordHasher, exceptions

ph = PasswordHasher()


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