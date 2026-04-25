"""ConfigEncryptor: encrypt and decrypt sensitive config values using Fernet symmetric encryption."""

import base64
import hashlib
import os
from typing import Any, Dict, Optional

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:
    Fernet = None  # type: ignore
    InvalidToken = Exception  # type: ignore

ENCRYPTED_PREFIX = "enc:"


def _derive_key(passphrase: str) -> bytes:
    """Derive a 32-byte Fernet-compatible key from a passphrase."""
    digest = hashlib.sha256(passphrase.encode()).digest()
    return base64.urlsafe_b64encode(digest)


class EncryptionError(Exception):
    """Raised when encryption or decryption fails."""


class ConfigEncryptor:
    """Encrypt and decrypt config values in-place.

    Values that are encrypted are stored with the prefix ``enc:`` so they
    can be identified and decrypted transparently at load time.
    """

    def __init__(self, key: Optional[str] = None) -> None:
        if Fernet is None:
            raise EncryptionError(
                "cryptography package is required for ConfigEncryptor. "
                "Install it with: pip install cryptography"
            )
        raw_key = key or os.environ.get("ENVOY_CFG_SECRET_KEY")
        if not raw_key:
            raise EncryptionError(
                "An encryption key must be supplied via the 'key' argument "
                "or the ENVOY_CFG_SECRET_KEY environment variable."
            )
        self._fernet = Fernet(_derive_key(raw_key))

    def encrypt_value(self, plaintext: str) -> str:
        """Return an ``enc:``-prefixed encrypted representation of *plaintext*."""
        token = self._fernet.encrypt(plaintext.encode()).decode()
        return f"{ENCRYPTED_PREFIX}{token}"

    def decrypt_value(self, value: str) -> str:
        """Decrypt an ``enc:``-prefixed value and return the plaintext."""
        if not value.startswith(ENCRYPTED_PREFIX):
            raise EncryptionError(f"Value does not have expected prefix '{ENCRYPTED_PREFIX}'.")
        token = value[len(ENCRYPTED_PREFIX):]
        try:
            return self._fernet.decrypt(token.encode()).decode()
        except InvalidToken as exc:
            raise EncryptionError("Decryption failed — invalid token or wrong key.") from exc

    def encrypt_config(self, config: Dict[str, Any], keys: list) -> Dict[str, Any]:
        """Return a copy of *config* with specified *keys* encrypted."""
        result = dict(config)
        for key in keys:
            if key in result and isinstance(result[key], str):
                result[key] = self.encrypt_value(result[key])
        return result

    def decrypt_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Return a copy of *config* with all ``enc:``-prefixed values decrypted."""
        result = {}
        for k, v in config.items():
            if isinstance(v, str) and v.startswith(ENCRYPTED_PREFIX):
                result[k] = self.decrypt_value(v)
            elif isinstance(v, dict):
                result[k] = self.decrypt_config(v)
            else:
                result[k] = v
        return result
