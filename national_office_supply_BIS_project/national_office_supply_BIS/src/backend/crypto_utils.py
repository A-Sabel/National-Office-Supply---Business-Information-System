"""
backend/crypto_utils.py
-----------------------
Encryption utilities for sensitive data (e.g., SSN).
Uses Fernet (symmetric encryption) from cryptography library.
"""

from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

load_dotenv()


class CryptoUtils:
    """
    Provides encrypt/decrypt for sensitive employee data (SSN, etc).

    Methods
    -------
    encrypt_ssn(ssn: str) → str (encrypted)
    decrypt_ssn(encrypted_ssn: str) → str (plaintext)
    """

    # Try to load encryption key from environment
    _ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", None)

    if _ENCRYPTION_KEY:
        _cipher = Fernet(_ENCRYPTION_KEY.encode())
    else:
        # Fallback: generate a new key (in production, this should be persisted)
        _new_key = Fernet.generate_key()
        _ENCRYPTION_KEY = _new_key.decode()
        _cipher = Fernet(_new_key)
        print(
            "[WARNING] No ENCRYPTION_KEY in .env. Generated temporary key (not persisted)."
        )
        print(f"[WARNING] Set ENCRYPTION_KEY={_ENCRYPTION_KEY} in .env to persist.")

    @classmethod
    def encrypt_ssn(cls, ssn: str) -> str:
        """
        Encrypt an SSN (plaintext) → ciphertext string.

        Args:
            ssn: plaintext SSN (e.g., "123-45-6789")

        Returns:
            Base64-encoded ciphertext (safe to store in DB)
        """
        if not ssn:
            return ""

        # Fernet returns bytes; decode to string for DB storage
        encrypted_bytes = cls._cipher.encrypt(ssn.encode())
        return encrypted_bytes.decode()

    @classmethod
    def decrypt_ssn(cls, encrypted_ssn: str) -> str:
        """
        Decrypt an SSN (ciphertext) → plaintext string.

        Args:
            encrypted_ssn: Base64-encoded ciphertext from DB

        Returns:
            Plaintext SSN (e.g., "123-45-6789")

        Raises:
            cryptography.fernet.InvalidToken if decryption fails
        """
        if not encrypted_ssn:
            return ""

        # Fernet expects bytes; decode the string from DB
        decrypted_bytes = cls._cipher.decrypt(encrypted_ssn.encode())
        return decrypted_bytes.decode()

    @classmethod
    def generate_encryption_key(cls) -> str:
        """
        Generate a new encryption key for use in .env file.
        Call this once to set up a persistent key.
        """
        key = Fernet.generate_key()
        return key.decode()
