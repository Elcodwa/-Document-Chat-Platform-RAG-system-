"""
Credential encryption at rest.

Database connection passwords / connection strings are never stored in
plaintext (see acceptance criteria: "connection is encrypted, validated,
and available for authorized chats"). We use Fernet (AES-128-CBC + HMAC),
which is authenticated symmetric encryption - suitable for secrets an
application must be able to *decrypt itself* later (unlike password
hashing, which is one-way).

The key is a single value read from the environment. In production this
should come from a secrets manager (Vault, AWS Secrets Manager, etc.),
never checked into source control. Generate one with:

    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings
from app.exceptions import AppError


class CredentialDecryptionError(AppError):
    status_code = 500
    public_message = "Stored credentials could not be decrypted."


@lru_cache
def _fernet() -> Fernet:
    settings = get_settings()
    key = settings.encryption_key.encode()
    return Fernet(key)


def encrypt_value(plain_text: str) -> str:
    if not plain_text:
        return ""
    return _fernet().encrypt(plain_text.encode()).decode()


def decrypt_value(cipher_text: str) -> str:
    if not cipher_text:
        return ""
    try:
        return _fernet().decrypt(cipher_text.encode()).decode()
    except InvalidToken as exc:
        raise CredentialDecryptionError() from exc
