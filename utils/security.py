"""
Security and Cryptography Utilities.
Provides PBKDF2-HMAC-SHA256 password hashing, verification, and hidden input handling.
"""

import hashlib
import hmac
import secrets
import getpass
import sys
from typing import Tuple
from config import PBKDF2_ITERATIONS, SALT_BYTES, HASH_ALGORITHM

def generate_salt(length: int = SALT_BYTES) -> str:
    """Generates a cryptographically secure random hexadecimal salt."""
    return secrets.token_hex(length)

def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
    """
    Hashes a password using PBKDF2-HMAC with the configured hash algorithm and iterations.
    
    Args:
        password: Plain text password to hash.
        salt: Optional hexadecimal salt string. If None, a new random salt is generated.
        
    Returns:
        Tuple of (password_hash_hex, salt_hex)
    """
    if not salt:
        salt = generate_salt()
        
    password_bytes = password.encode("utf-8")
    salt_bytes = bytes.fromhex(salt)
    
    derived_key = hashlib.pbkdf2_hmac(
        HASH_ALGORITHM,
        password_bytes,
        salt_bytes,
        PBKDF2_ITERATIONS
    )
    
    password_hash = derived_key.hex()
    return password_hash, salt

def verify_password(plain_password: str, stored_hash: str, stored_salt: str) -> bool:
    """
    Verifies a plain text password against a stored PBKDF2 hash and salt in constant time.
    
    Args:
        plain_password: Password entered by user.
        stored_hash: Hex hash string stored in database.
        stored_salt: Hex salt string stored in database.
        
    Returns:
        True if password matches, False otherwise.
    """
    if not plain_password or not stored_hash or not stored_salt:
        return False
        
    try:
        computed_hash, _ = hash_password(plain_password, stored_salt)
        return hmac.compare_digest(computed_hash, stored_hash)
    except Exception:
        return False

def get_hidden_input(prompt_text: str = "Password: ") -> str:
    """
    Reads hidden user input safely using getpass with fallback for unsupported terminals.
    """
    try:
        # Check if stdin is a tty
        if sys.stdin.isatty():
            return getpass.getpass(prompt_text)
        else:
            # Fallback for piped input or automated testing environments
            sys.stdout.write(prompt_text)
            sys.stdout.flush()
            return sys.stdin.readline().rstrip("\r\n")
    except Exception:
        sys.stdout.write(prompt_text)
        sys.stdout.flush()
        return sys.stdin.readline().rstrip("\r\n")
