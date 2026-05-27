import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken
from app.models.config import ENCRYPTION_SECRET_KEY


class SecretCipher:
    def __init__(self):
        self._fernet = self._build_fernet(ENCRYPTION_SECRET_KEY)

    @staticmethod
    def _build_fernet(secret: str):
        if not secret:
            return None
        digest = hashlib.sha256(secret.encode("utf-8")).digest()
        key = base64.urlsafe_b64encode(digest)
        return Fernet(key)

    def encrypt(self, value: str) -> str:
        if not value:
            return value
        if not self._fernet:
            return value
        token = self._fernet.encrypt(value.encode("utf-8")).decode("utf-8")
        return f"enc:{token}"

    def decrypt(self, value: str) -> str:
        if not value:
            return value
        if not self._fernet:
            return value
        if not value.startswith("enc:"):
            return value
        token = value[4:].encode("utf-8")
        try:
            return self._fernet.decrypt(token).decode("utf-8")
        except InvalidToken:
            return ""


secret_cipher = SecretCipher()
