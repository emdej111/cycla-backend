"""Field-level encryption at rest for sensitive health data.

Wraps the Fernet symmetric cipher so individual columns (journal text, medical
document analysis, free-text notes) can be stored encrypted in the database
regardless of whether the underlying disk/volume is also encrypted. This gives
us defense-in-depth: a DB dump or leaked backup does not expose plaintext
health data without SECRET_KEY-derived material.
"""

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.types import TEXT, TypeDecorator

from src.core.config import get_settings


def _get_fernet() -> Fernet:
    settings = get_settings()
    return Fernet(settings.encryption_key.encode())


def encrypt_value(value: str) -> str:
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt_value(token: str) -> str:
    try:
        return _get_fernet().decrypt(token.encode()).decode()
    except InvalidToken:
        # Data written before encryption was enabled, or corrupted; fail safe.
        return token


class EncryptedText(TypeDecorator):
    """SQLAlchemy column type that transparently encrypts/decrypts TEXT values."""

    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return encrypt_value(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return decrypt_value(value)
