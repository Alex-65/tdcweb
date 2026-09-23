"""
Password hashing utilities -- bcrypt with cost factor 12 (CLAUDE.md security policy).

Use these helpers everywhere; do NOT call bcrypt directly from routes / services
so the cost factor stays uniform and auditable.
"""
from __future__ import annotations

import bcrypt

# Cost factor: 12 rounds (~250ms on a modern CPU).
# Per CLAUDE.md "Security Rules": bcrypt with min 12 rounds.
BCRYPT_ROUNDS: int = 12


def hash_password(plaintext: str) -> str:
    """
    Hash a plaintext password with bcrypt and return the hash as a UTF-8 string.

    The returned string includes the algorithm identifier, cost, and salt --
    everything `verify_password` needs. Each call produces a different hash
    because bcrypt generates a fresh random salt per invocation.

    Raises:
        TypeError: if `plaintext` is not a str.
    """
    if not isinstance(plaintext, str):
        raise TypeError("plaintext must be str")
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    digest = bcrypt.hashpw(plaintext.encode("utf-8"), salt)
    return digest.decode("utf-8")


def verify_password(plaintext: str, hash_: str) -> bool:
    """
    Constant-time check of `plaintext` against a bcrypt hash.

    Returns False (never raises) on:
      - empty / None hash
      - malformed hash
      - mismatch
    """
    if not plaintext or not hash_:
        return False
    try:
        return bcrypt.checkpw(plaintext.encode("utf-8"), hash_.encode("utf-8"))
    except (ValueError, TypeError):
        # bcrypt raises ValueError on invalid hash format.
        return False
