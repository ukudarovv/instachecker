"""Encryption utilities for sensitive data."""

from typing import Optional
from cryptography.fernet import Fernet


class OptionalFernet:
    """Optional Fernet encryption - works with or without encryption key."""
    
    def __init__(self, key: Optional[str]):
        """Initialize with optional encryption key."""
        self._fernet = None
        if key:
            try:
                self._fernet = Fernet(key.encode() if isinstance(key, str) else key)
            except Exception:
                self._fernet = None

    def encrypt(self, data: str) -> str:
        """Encrypt data if key is available, otherwise return as-is."""
        if not self._fernet:
            return data
        return self._fernet.encrypt(data.encode()).decode()

    def decrypt(self, token: str) -> str:
        """Decrypt data if key is available, otherwise return as-is."""
        if not self._fernet:
            return token
        return self._fernet.decrypt(token.encode()).decode()
