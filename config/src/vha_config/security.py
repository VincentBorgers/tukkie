import base64
import hashlib
from typing import Protocol

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:  # pragma: no cover
    Fernet = None
    InvalidToken = Exception


class CipherProtocol(Protocol):
    def encrypt(self, value: str) -> str:
        ...

    def decrypt(self, value: str) -> str:
        ...


class NoopCipher:
    def encrypt(self, value: str) -> str:
        return value

    def decrypt(self, value: str) -> str:
        return value


class FernetCipher:
    def __init__(self, secret: str):
        if Fernet is None:
            raise RuntimeError("cryptography is niet beschikbaar")

        digest = hashlib.sha256(secret.encode("utf-8")).digest()
        key = base64.urlsafe_b64encode(digest)
        self._fernet = Fernet(key)

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, value: str) -> str:
        try:
            return self._fernet.decrypt(value.encode("utf-8")).decode("utf-8")
        except InvalidToken:
            return value


def build_cipher(secret: str | None) -> CipherProtocol:
    if not secret:
        return NoopCipher()
    return FernetCipher(secret)
