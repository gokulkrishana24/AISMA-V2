from __future__ import annotations

import base64
import hashlib
import os

from cryptography.fernet import Fernet

DEFAULT_VAULT_KEY = os.getenv(
    "INTEGRATION_VAULT_SECRET",
    "aisma_vault_enterprise_encryption_key_32_bytes_safe",
)


def _get_fernet_key(secret: str) -> bytes:
    derived = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(derived)


class CredentialVault:
    def __init__(self, secret: str = DEFAULT_VAULT_KEY) -> None:
        self._fernet = Fernet(_get_fernet_key(secret))

    def encrypt(self, plain_token: str) -> str:
        if not plain_token:
            return ""
        encrypted = self._fernet.encrypt(plain_token.encode("utf-8"))
        return encrypted.decode("utf-8")

    def decrypt(self, encrypted_token: str) -> str:
        if not encrypted_token:
            return ""
        decrypted = self._fernet.decrypt(encrypted_token.encode("utf-8"))
        return decrypted.decode("utf-8")
