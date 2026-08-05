import pytest
from cryptography.fernet import Fernet

from core.encryption import CredentialDecryptionError, decrypt_value, encrypt_value


class TestEncryption:
    def test_round_trip(self):
        original = "super-secret-db-password"
        encrypted = encrypt_value(original)
        assert encrypted != original
        assert decrypt_value(encrypted) == original

    def test_empty_string_round_trip(self):
        assert encrypt_value("") == ""
        assert decrypt_value("") == ""

    def test_encrypted_value_is_not_plaintext_substring(self):
        original = "postgres123"
        encrypted = encrypt_value(original)
        assert original not in encrypted

    def test_tampered_ciphertext_fails_to_decrypt(self):
        encrypted = encrypt_value("some-password")
        tampered = encrypted[:-4] + "abcd"
        with pytest.raises(CredentialDecryptionError):
            decrypt_value(tampered)

    def test_two_encryptions_of_same_value_differ(self):
        """Fernet includes a random IV, so encrypting the same password
        twice must not produce identical ciphertext (defends against
        pattern-matching identical passwords across connections)."""
        a = encrypt_value("same-password")
        b = encrypt_value("same-password")
        assert a != b
        assert decrypt_value(a) == decrypt_value(b) == "same-password"
